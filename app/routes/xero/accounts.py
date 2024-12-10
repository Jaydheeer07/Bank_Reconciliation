import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse, JSONResponse
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize

from app.core.oauth import api_client, require_valid_token
from app.utils.xero.account_utils import (
    get_account_details,
    get_stored_account_id,
    store_account_id,
    validate_account_id,
)
from app.utils.xero.tenant_utils import get_stored_tenant_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/accounts",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=JSONResponse,
    description="Get a list of all bank accounts for the selected tenant",
)
async def get_tenant_accounts(
    request: Request, token: dict = Depends(require_valid_token)
):
    try:
        xero_tenant_id = get_stored_tenant_id(request)
        if not xero_tenant_id:
            raise HTTPException(status_code=404, detail="No organisation tenant found")

        accounting_api = AccountingApi(api_client)
        accounts = accounting_api.get_accounts(
            xero_tenant_id, where='Status=="ACTIVE" AND Type=="BANK"'
        )

        formatted_accounts = serialize(accounts)

        return JSONResponse(content=formatted_accounts)

    except Exception as e:
        logger.error(f"Accounts error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/selected-account",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=HTMLResponse,
    description="Get information about the currently selected bank account",
)
async def get_selected_account(
    request: Request, token: dict = Depends(require_valid_token)
) -> JSONResponse:
    """Get information about the currently selected bank account."""
    try:
        tenant_id = get_stored_tenant_id(request)
        account_id = get_stored_account_id(request)

        if not tenant_id:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_tenant",
                    "message": "No tenant currently selected",
                },
            )

        if not account_id:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_account",
                    "message": "No bank account currently selected",
                },
            )

        # Get account details
        account_details = await get_account_details(tenant_id, account_id)

        if not account_details:
            # Clear invalid account ID
            request.session.pop("xero_bank_account_id", None)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "invalid_account",
                    "message": "Previously selected account is no longer valid",
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "active",
                "account_id": account_id,
                "account_details": account_details,
            },
        )
    except Exception as e:
        logger.error(f"Error getting selected account: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/select-account/{account_id}",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=HTMLResponse,
    description="Select and store a specific bank account ID for transaction retrieval.",
)
async def select_account(
    request: Request,
    account_id: str = Path(..., description="The ID of the bank account to select"),
    token: dict = Depends(require_valid_token),
) -> JSONResponse:
    """Select and store a specific bank account ID for transaction retrieval."""
    try:
        # Get the stored tenant ID
        tenant_id = get_stored_tenant_id(request)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="No tenant selected. Please select a tenant first.",
            )

        # Validate the account ID
        is_valid = await validate_account_id(tenant_id, account_id)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid account ID or account not found in selected organization",
            )

        # Get account details for the response
        account_details = await get_account_details(tenant_id, account_id)

        # Store the account ID in the session
        store_account_id(request, account_id)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Bank account selected successfully",
                "account_id": account_id,
                "account_details": account_details,
            },
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error selecting account: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
