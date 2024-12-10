import logging
from typing import Dict, Optional

from fastapi import Request
from xero_python.accounting import AccountingApi
from xero_python.api_client import serialize

from app.core.oauth import api_client
from app.utils.xero.xero_client import XeroClient

xero_client = XeroClient()
logger = logging.getLogger(__name__)


def get_stored_account_id(request: Request) -> Optional[str]:
    """Get the stored bank account ID from the session."""
    return request.session.get("xero_bank_account_id")


def store_account_id(request: Request, account_id: str):
    """Store the bank account ID in the session."""
    request.session["xero_bank_account_id"] = account_id


async def validate_account_id(tenant_id: str, account_id: str) -> bool:
    """Validate that the account ID exists in the specified tenant."""
    try:
        accounting_api = AccountingApi(api_client)
        accounts = accounting_api.get_accounts(
            xero_tenant_id=tenant_id,
            where=f'Status=="ACTIVE" AND Type=="BANK" AND AccountID=guid("{account_id}")',
        )
        return len(accounts.accounts) > 0
    except Exception as e:
        logger.error(f"Error validating account ID: {str(e)}", exc_info=True)
        return False


async def get_account_details(tenant_id: str, account_id: str) -> Optional[Dict]:
    """Get detailed information about a specific bank account."""
    try:
        accounting_api = AccountingApi(api_client)
        accounts = accounting_api.get_accounts(
            xero_tenant_id=tenant_id, where=f'AccountID=guid("{account_id}")'
        )
        if accounts.accounts:
            return serialize(accounts.accounts[0])
        return None
    except Exception as e:
        logger.error(f"Error getting account details: {str(e)}", exc_info=True)
        return None
