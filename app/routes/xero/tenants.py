import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize
from xero_python.identity import IdentityApi

from app.core.oauth import api_client, require_valid_token
from app.models.xero.tenant_models import TenantError
from app.utils.xero.tenant_utils import (
    get_stored_tenant_id,
    store_tenant_id,
    validate_tenant_id,
)

router = APIRouter()
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

@router.get("/tenants")
async def get_tenants(
    request: Request,
    token: dict = Depends(require_valid_token),
    description="Returns a list of tenants for the current user.",
):
    async def fetch_tenants():
        try:
            identity_api = IdentityApi(api_client)
            accounting_api = AccountingApi(api_client)
            available_tenants = []

            connections = identity_api.get_connections()

            for connection in connections:
                if connection.tenant_type == "ORGANISATION":
                    try:
                        organisations = accounting_api.get_organisations(
                            xero_tenant_id=connection.tenant_id
                        )
                        tenant_info = {
                            "tenantId": connection.tenant_id,
                            "tenantName": organisations.organisations[0].name
                            if organisations.organisations
                            else "Unknown",
                            "tenantType": connection.tenant_type,
                            "lastAccessed": datetime.now(timezone.utc).isoformat(),
                        }
                        available_tenants.append(tenant_info)
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch organisation details for tenant {connection.tenant_id}: {str(e)}"
                        )
                        continue

            if not available_tenants:
                raise TenantError(
                    message="No available organizations found", error_code="NO_TENANTS"
                )

            return available_tenants

        except Exception as e:
            logger.error(f"Tenants error: {str(e)}", exc_info=True)
            raise TenantError(
                message="Failed to fetch organizations",
                error_code="FETCH_ERROR",
            )

    try:
        tenants = await retry_with_backoff(fetch_tenants)
        return JSONResponse(content={"tenants": tenants})
    except TenantError as te:
        logger.error(f"TenantError: {str(te)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(te),
        )
    except Exception as e:
        logger.error(f"Error selecting tenant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@router.post("/select-tenant/{tenant_id}")
async def select_tenant(
    request: Request,
    tenant_id: str,
    token: dict = Depends(require_valid_token),
    description="Selects a specific Xero tenant ID.",
) -> JSONResponse:
    """Select and store a specific Xero tenant ID."""
    try:
        # Validate the tenant ID
        is_valid = await validate_tenant_id(tenant_id)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid tenant ID or tenant not found in available connections",
            )
        # Store the tenant ID in the session
        store_tenant_id(request, tenant_id)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Tenant ID selected and stored successfully",
                "tenant_id": tenant_id,
            },
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error selecting tenant: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/selected-tenant")
async def get_selected_tenant(
    request: Request,
    token: dict = Depends(require_valid_token),
    description="Returns the currently selected tenant ID.",
) -> JSONResponse:
    """Get information about the currently selected tenant."""
    try:
        tenant_id = get_stored_tenant_id(request)
        if not tenant_id:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_tenant",
                    "message": "No tenant currently selected",
                },
            )

        # Get tenant details from Xero
        identity_api = IdentityApi(api_client)
        connections = identity_api.get_connections()
        tenant_info = next(
            (serialize(conn) for conn in connections if conn.tenant_id == tenant_id),
            None,
        )

        if not tenant_info:
            # Clear invalid tenant ID
            request.session.pop("xero_tenant_id", None)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "invalid_tenant",
                    "message": "Previously selected tenant is no longer valid",
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "active",
                "tenant_id": tenant_id,
                "tenant_info": tenant_info,
            },
        )

    except Exception as e:
        logger.error(f"Error getting selected tenant: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))