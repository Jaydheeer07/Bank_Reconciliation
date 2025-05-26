import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize

from app.core.deps import get_db
from app.core.oauth import api_client, require_valid_token
from app.utils.xero.tenant_utils import get_active_tenant_id

router = APIRouter(prefix="/xero/contacts")
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_class=JSONResponse,
    description="Returns a list of contacts for the current tenant",
)
async def get_contacts(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
):
    """
    Get contacts for the current active tenant.
    Requires an active tenant to be selected.
    """
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get active tenant ID from token
        xero_tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        if not xero_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found. Please select a tenant first.",
            )

        # Get contacts from Xero
        accounting_api = AccountingApi(api_client)
        contacts = accounting_api.get_contacts(xero_tenant_id)
        serialized_contacts = serialize(contacts)

        return JSONResponse(
            content=serialized_contacts,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contacts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting contacts: {str(e)}",
        )


@router.get(
    "/{contact_id}",
    response_class=HTMLResponse,
    description="Returns a contact by ID for the current tenant",
)
async def get_contact_by_id(
    request: Request,
    contact_id: str = Path(..., description="The ID of the contact"),
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
) -> JSONResponse:
    """
    Get a specific contact by ID for the current active tenant.
    Requires an active tenant to be selected.
    """
    try:
        # Check if user is authenticated
        if not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get active tenant ID from token
        xero_tenant_id = await get_active_tenant_id(db, str(request.state.user.id))
        if not xero_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active tenant found. Please select a tenant first.",
            )

        # Get contact from Xero
        accounting_api = AccountingApi(api_client)
        contact = accounting_api.get_contact(xero_tenant_id, contact_id)
        serialized_contact = serialize(contact)

        return JSONResponse(
            content=serialized_contact,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact {contact_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting contact: {str(e)}",
        )
