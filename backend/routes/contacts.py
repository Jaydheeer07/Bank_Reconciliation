import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, JSONResponse
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize

from backend.api.tenant_utils import get_stored_tenant_id
from backend.auth.oauth import api_client, require_valid_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/contacts",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=JSONResponse,
    description="Returns a list of contacts for the current tenant",
)
async def get_contacts(request: Request, token: dict = Depends(require_valid_token)):
    try:
        xero_tenant_id = get_stored_tenant_id(request)
        if not xero_tenant_id:
            raise HTTPException(status_code=404, detail="No organisation tenant found")

        accounting_api = AccountingApi(api_client)
        contacts = accounting_api.get_contacts(xero_tenant_id)
        serialized_contacts = serialize(contacts)

        return JSONResponse(content=serialized_contacts)

    except Exception as e:
        logger.error(f"Contacts error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/contacts/{contact_id}",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=HTMLResponse,
    description="Returns a contact by ID for the current tenant",
)
async def get_contact_by_id(
    request: Request,
    contact_id: str = Path(..., description="The ID of the contact"),
    token: dict = Depends(require_valid_token),
) -> JSONResponse:
    try:
        # Get the stored tenant ID
        tenant_id = get_stored_tenant_id(request)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="No tenant selected. Please select a tenant first.",
            )
        accounting_api = AccountingApi(api_client)
        contact = accounting_api.get_contact(tenant_id, contact_id=contact_id)

        return JSONResponse(
            status_code=200,
            content={"status": "success", "contact": serialize(contact)},
        )
    except Exception as e:
        logger.error(f"Error selecting contact: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
