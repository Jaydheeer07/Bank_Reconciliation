import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from xero_python.accounting import AccountingApi
from xero_python.identity import IdentityApi

from app.core.deps import get_db
from app.core.oauth import api_client, require_valid_token, token_manager
from app.models.database.scheduled_jobs_models import ScheduledJob
from app.models.xero.tenant_models import ActiveTenantResponse
from app.models.xero.xero_token_models import XeroToken
from app.scheduled_tasks.job_manager import start_job_for_user, stop_job
from app.utils.xero.tenant_utils import (
    create_tenant_metadata,
    get_active_tenant_id,
    get_tenant_metadata,
    update_tenant_metadata,
    validate_tenant_access,
)

router = APIRouter(prefix="/xero/tenants")
logger = logging.getLogger(__name__)


# Utility function for retry logic
async def retry_with_backoff(func, max_retries=3, initial_delay=1):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = initial_delay * (2**attempt)  # exponential backoff
            await asyncio.sleep(delay)


@router.get("/", description="List all available Xero tenants")
async def list_tenants(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
):
    async def fetch_tenants():
        try:
            # Check if user is authenticated
            if not request.state.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated",
                )

            # Get current token from token manager
            current_token = token_manager.get_current_token(str(request.state.user.id))
            if not current_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No valid Xero token found",
                )

            identity_api = IdentityApi(api_client)
            accounting_api = AccountingApi(api_client)
            available_tenants = []

            connections = identity_api.get_connections()
            user_id = str(request.state.user.id)
            for connection in connections:
                if connection.tenant_type == "ORGANISATION":
                    try:
                        organisations = accounting_api.get_organisations(
                            xero_tenant_id=connection.tenant_id
                        )
                        org = organisations.organisations[0]

                        # Get or create tenant metadata
                        tenant_metadata = await get_tenant_metadata(
                            db, connection.tenant_id, user_id
                        )
                        if not tenant_metadata:
                            table_name = "statements"  # Use fixed table name instead of generating one
                            tenant_metadata = await create_tenant_metadata(
                                db=db,
                                user_id=user_id,
                                tenant_id=connection.tenant_id,
                                tenant_name=org.name,
                                tenant_short_code=getattr(org, "short_code", None),
                                table_name=table_name,
                            )
                        elif (
                            getattr(org, "short_code", None)
                            and tenant_metadata.tenant_short_code != org.short_code
                        ):
                            # Update short code if it has changed
                            await update_tenant_metadata(
                                db,
                                connection.tenant_id,
                                tenant_short_code=org.short_code,
                            )
                            tenant_metadata.tenant_short_code = org.short_code

                        tenant_info = {
                            "id": connection.tenant_id,
                            "name": org.name,
                            "short_code": getattr(org, "short_code", None),
                            "table_name": tenant_metadata.table_name,
                            "is_active": tenant_metadata.is_active,
                        }
                        available_tenants.append(tenant_info)
                    except Exception as e:
                        logger.error(
                            f"Error processing organisation {connection.tenant_id}: {str(e)}",
                            exc_info=True,
                        )

            return {"tenants": available_tenants}

        except Exception as e:
            logger.error(f"Error fetching tenants: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching tenants: {str(e)}",
            )

    return await retry_with_backoff(fetch_tenants)


@router.post("/{tenant_id}/activate", description="Select a tenant as active and start scheduled processing")
async def activate_tenant(
    request: Request,
    tenant_id: str,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
):
    """
    Activate a tenant and start scheduled processing.
    This endpoint:
    1. Sets the tenant as active for the user
    2. Stops any existing scheduled jobs for the previous tenant
    3. Starts new scheduled jobs for the newly activated tenant
    """
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        user_id = str(request.state.user.id)

        # Get current active tenant
        current_tenant_id = await get_active_tenant_id(db, user_id)

        # If there's an active tenant and it's different from the new one,
        # stop its jobs
        if current_tenant_id and current_tenant_id != tenant_id:
            # Find and stop all active jobs for the current tenant
            active_jobs = (
                db.query(ScheduledJob)
                .filter(
                    ScheduledJob.user_id == user_id,
                    ScheduledJob.tenant_id == current_tenant_id,
                    ScheduledJob.is_active == True,
                )
                .all()
            )
            
            for job in active_jobs:
                try:
                    await stop_job(db, job.id)
                    logger.info(f"Stopped job {job.id} for previous tenant {current_tenant_id}")
                except Exception as e:
                    # Log the error but continue - we don't want to block tenant activation
                    # if a job can't be stopped
                    logger.error(f"Error stopping job {job.id}: {str(e)}")

        # Validate user has access to this tenant
        # if not await validate_tenant_access(db, user_id, tenant_id):
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Tenant {tenant_id} not found or not accessible",
        #     )

        # Get tenant metadata
        tenant_metadata = await get_tenant_metadata(db, tenant_id, user_id)
        if not tenant_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant metadata not found for tenant {tenant_id}",
            )

        # Update the token with the selected tenant
        token_record = (
            db.query(XeroToken)
            .filter(XeroToken.user_id == request.state.user.id)
            .first()
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid Xero token found",
            )

        # Update the token with the selected tenant
        token_record.tenant_id = tenant_id
        db.commit()

        # Start scheduled processing for the new tenant
        await start_job_for_user(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            job_type='invoice'
        )
        
        await start_job_for_user(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            job_type='statement'
        )

        return JSONResponse(
            content={
                "message": f"Successfully activated tenant {tenant_id}",
                "tenant_id": tenant_id,
                "tenant_name": tenant_metadata.tenant_name,
            },
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating tenant: {str(e)}",
        )


@router.get(
    "/active", response_model=ActiveTenantResponse, description="Get active Xero tenant"
)
async def get_active_tenant(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
) -> ActiveTenantResponse:
    """
    Get the currently active Xero tenant for the current user.
    Returns tenant details from TenantMetadata if an active tenant is found.
    Also ensures that scheduled jobs are running for the active tenant.
    """
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        user_id = str(request.state.user.id)
        logger.info(f"get_active_tenant called for user_id: {user_id}")
        
        # Get active tenant ID from token
        active_tenant_id = await get_active_tenant_id(db, user_id)
        if not active_tenant_id:
            logger.warning(f"No active tenant found for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found",
            )
        
        logger.info(f"Active tenant found: {active_tenant_id} for user: {user_id}")

        # Get tenant metadata
        tenant_metadata = await get_tenant_metadata(db, active_tenant_id, user_id)
        if not tenant_metadata:
            logger.warning(f"Tenant metadata not found for tenant {active_tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant metadata not found for tenant {active_tenant_id}",
            )
            
        # Initialize job status information
        job_status = {
            "jobs_exist": False,
            "jobs_created": False,
            "active_job_count": 0,
            "job_details": []
        }
            
        # Check if there are active jobs for this tenant
        active_jobs = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.user_id == user_id,
                ScheduledJob.tenant_id == active_tenant_id,
                ScheduledJob.is_active == True,
            )
            .all()
        )
        
        logger.info(f"Found {len(active_jobs)} active jobs for tenant {active_tenant_id}")
        
        # If no active jobs, start them
        if not active_jobs:
            logger.info(f"No active jobs found for tenant {active_tenant_id}, starting scheduled processing")
            
            # Start scheduled processing for the active tenant
            invoice_job = await start_job_for_user(
                db=db,
                user_id=user_id,
                tenant_id=active_tenant_id,
                job_type='invoice'
            )
            logger.info(f"Started invoice job: {invoice_job}")
            
            statement_job = await start_job_for_user(
                db=db,
                user_id=user_id,
                tenant_id=active_tenant_id,
                job_type='statement'
            )
            logger.info(f"Started statement job: {statement_job}")
            
            # Update job status
            job_status["jobs_created"] = True
            job_status["job_details"] = [
                {"job_type": "invoice", "job_id": invoice_job.get("job_id", "unknown"), "status": "created"},
                {"job_type": "statement", "job_id": statement_job.get("job_id", "unknown"), "status": "created"}
            ]
        else:
            logger.info(f"Active jobs already exist for tenant {active_tenant_id}, no need to start new ones")
            
            # Update job status
            job_status["jobs_exist"] = True
            job_status["active_job_count"] = len(active_jobs)
            job_status["job_details"] = [
                {"job_type": job.job_type, "job_id": str(job.id), "status": "active", "created_at": job.created_at.isoformat() if job.created_at else None}
                for job in active_jobs
            ]

        # Create response with tenant metadata and job status
        response_dict = {
            "tenant_id": tenant_metadata.tenant_id,
            "tenant_name": tenant_metadata.tenant_name,
            "tenant_short_code": tenant_metadata.tenant_short_code,
            "table_name": tenant_metadata.table_name,
            "job_status": job_status
        }
        
        return response_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting active tenant: {str(e)}",
        )
