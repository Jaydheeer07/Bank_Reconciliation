import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize

from app.core.deps import get_db
from app.core.oauth import api_client, require_valid_token
from app.utils.xero.tenant_utils import get_active_tenant_id

router = APIRouter(prefix="/xero/bank-transactions")
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_class=JSONResponse,
    description="Returns a list of bank transactions for the current tenant",
)
async def get_bank_transactions(
    request: Request,
    db: Session = Depends(get_db),
    token: dict = Depends(require_valid_token),
):
    """
    Get bank transactions for the current active tenant.
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

        # Get bank transactions from Xero
        accounting_api = AccountingApi(api_client)
        bank_transactions = accounting_api.get_bank_transactions(xero_tenant_id)

        # Serialize and return the JSON response
        serialized_transactions = serialize(bank_transactions)
        return JSONResponse(
            content=serialized_transactions,
            status_code=status.HTTP_200_OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bank transactions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting bank transactions: {str(e)}",
        )
