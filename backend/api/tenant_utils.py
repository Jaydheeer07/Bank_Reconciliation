import logging
from typing import Optional

from fastapi import Request
from xero_python.identity import IdentityApi

from backend.auth.oauth import api_client, obtain_xero_oauth2_token

logger = logging.getLogger(__name__)

async def get_xero_tenant_id(request: Request):
    """Get the Xero tenant ID from the session."""
    stored_tenant_id = get_stored_tenant_id(request)
    if stored_tenant_id:
        logger.info(f"Retrieved tenant ID from session: {stored_tenant_id}")
        return stored_tenant_id

    logger.warning("No tenant ID found in session, attempting to fetch from Xero API")
    token = obtain_xero_oauth2_token()
    if not token:
        logger.error("Failed to obtain Xero OAuth2 token")
        return None

    identity_api = IdentityApi(api_client)
    try:
        connections = identity_api.get_connections()
        for connection in connections:
            if connection.tenant_type == "ORGANISATION":
                logger.info(f"Fetched tenant ID from Xero API: {connection.tenant_id}")
                return connection.tenant_id
    except Exception as e:
        logger.error(f"Error getting tenant ID: {str(e)}", exc_info=True)
        return None
    return None

async def validate_tenant_id(tenant_id: str) -> bool:
    """Validate that the tenant ID exists in available connections."""
    try:
        identity_api = IdentityApi(api_client)
        connections = identity_api.get_connections()
        is_valid = any(conn.tenant_id == tenant_id for conn in connections)
        logger.info(f"Validated tenant ID {tenant_id}: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating tenant ID: {str(e)}", exc_info=True)
        return False
    

def store_tenant_id(request: Request, tenant_id: str):
    """Store the tenant ID in the session."""
    request.session["xero_tenant_id"] = tenant_id
    logger.info(f"Stored tenant ID in session: {tenant_id}")


def get_stored_tenant_id(request: Request) -> Optional[str]:
    """Get the stored tenant ID from the session."""
    tenant_id = request.session.get("xero_tenant_id")
    logger.info(f"Retrieved tenant ID from session: {tenant_id}")
    return tenant_id


