import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token

from app.config import settings
from app.core.deps import get_current_user, get_db
from app.models.database.schema_models import User
from app.services.xero.token_manager import token_manager

logger = logging.getLogger(__name__)

oauth = OAuth()

oauth.register(
    name="xero",
    client_id=settings.client_id,
    client_secret=settings.client_secret_key,
    server_metadata_url=settings.xero_metadata_url,
    client_kwargs={
        "scope": settings.scope,
        "token_endpoint": settings.xero_token_endpoint,
    },
    authorize_params={"response_type": "code"},
)

# Add debug logging after registration
logger.info("OAuth client registration completed")

api_client = ApiClient(
    Configuration(
        debug=False,
        oauth2_token=OAuth2Token(
            client_id=settings.client_id,
            client_secret=settings.client_secret_key,
        ),
    ),
    pool_threads=1,
)


def create_token_dict(token):
    """Create a complete token dictionary including scope."""
    expires_at = datetime.now() + timedelta(seconds=token.get("expires_in", 0))
    return {
        "access_token": token.get("access_token"),
        "token_type": token.get("token_type", "Bearer"),
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "expires_at": expires_at.timestamp(),
        "scope": settings.scope,
    }


@api_client.oauth2_token_getter
def obtain_xero_oauth2_token() -> Optional[Dict[str, Any]]:
    """
    Get the current OAuth2 token using the token manager.
    Returns None if no token exists.
    """
    try:
        return token_manager.get_current_token()
    except Exception as e:
        logger.error(f"Error retrieving token: {str(e)}", exc_info=True)
        return None


async def refresh_token_if_expired(request: Request, current_user: User):
    """
    Refresh the token if it's expired.
    Args:
        request: The FastAPI request object
        current_user: The authenticated user
    Returns:
        The refreshed token if successful, None otherwise
    """
    try:
        token = token_manager.get_current_token(str(current_user.id))
        if token:
            return token
        return None
    except Exception as e:
        logger.error(f"Error in refresh_token_if_expired: {str(e)}", exc_info=True)
        return None


async def require_valid_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dependency to ensure a valid token exists."""
    token = await refresh_token_if_expired(request, current_user)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid Xero token found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def store_xero_oauth2_token(
    token: Optional[Dict[str, Any]], user_id: Optional[str] = None
) -> None:
    """
    Store the OAuth2 token using the token manager.
    Args:
        token: The OAuth2 token to store, or None to clear the token
        user_id: The ID of the user who owns this token
    """
    if token and user_id:
        token_manager.store_token(token, user_id)
    elif user_id:
        token_manager.invalidate_token(user_id)
