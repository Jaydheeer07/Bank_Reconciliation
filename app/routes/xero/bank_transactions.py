import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize

from app.core.oauth import api_client, require_valid_token
from app.utils.xero.tenant_utils import get_stored_tenant_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/bank-transactions",
    dependencies=[Depends(get_stored_tenant_id)],
    response_class=JSONResponse,
    description="Returns a list of bank transactions for the current tenant",
)
async def get_bank_transactions(
    request: Request, token: dict = Depends(require_valid_token)
):
    try:
        xero_tenant_id = get_stored_tenant_id(request)
        logger.info(f"Tenant ID: {xero_tenant_id}")
        if not xero_tenant_id:
            raise HTTPException(status_code=404, detail="No organisation tenant found")

        accounting_api = AccountingApi(api_client)
        bank_transactions = accounting_api.get_bank_transactions(xero_tenant_id)

        # Serialize and return the JSON response
        serialized_transactions = serialize(bank_transactions)
        return JSONResponse(content=serialized_transactions)

    except Exception as e:
        logger.error(f"Bank Transactions error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
