import logging
from datetime import datetime, timedelta

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token, TokenApi

from app.config import app, settings

logger = logging.getLogger(__name__)

oauth = OAuth()
oauth.register(
    name="xero",
    client_id=settings.client_id,
    client_secret=settings.client_secret_key,
    server_metadata_url=settings.xero_metadata_url,
    client_kwargs={"scope": settings.scope},
)

api_client = ApiClient(
    Configuration(
        debug=True,
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
def obtain_xero_oauth2_token():
    """Get the token from the session."""
    if hasattr(app.state, "token"):
        token_dict = app.state.token
        if "expires_at" in token_dict and token_dict["expires_at"] is not None:
            expiration_time = datetime.fromtimestamp(token_dict["expires_at"])
            logger.info(f"Token expires at: {expiration_time}")
        else:
            logger.warning("Token expiration time is not set.")
        # Ensure scope is included in the token
        if "scope" not in token_dict:
            token_dict["scope"] = settings.scope
        return token_dict
    return None


@api_client.oauth2_token_saver
def store_xero_oauth2_token(token):
    """Store the token in the session."""
    if token is None:
        app.state.token = None
        logger.info("Token cleared from session.")
    else:
        token_dict = token if isinstance(token, dict) else token
        token_dict["scope"] = settings.scope  # Ensure scope is always included
        app.state.token = token_dict
        logger.info(f"Token stored: {token_dict}")

def is_token_expired(token: dict) -> bool:
    """Check if the token is expired or about to expire in the next 60 seconds."""
    if not token or "expires_at" not in token:
        return True
    return datetime.now().timestamp() >= (token["expires_at"] - 60)


async def refresh_token_if_expired():
    """Refresh the token if it's expired."""
    token = obtain_xero_oauth2_token()
    logger.info(f"Current token: {token}")

    if token:
        logger.info("Attempting to refresh token.")
        try:
            # Create a TokenApi instance
            token_api = TokenApi(
                api_client, settings.client_id, settings.client_secret_key
            )

            # Prepare refresh token request
            new_token = token_api.refresh_token(
                refresh_token=token.get("refresh_token"),
                scope=settings.scope,
            )

            if new_token:
                new_token_dict = create_token_dict(new_token)
                store_xero_oauth2_token(new_token_dict)
                logger.info(f"Token refreshed successfully: {new_token_dict}")
                return new_token_dict
            else:
                logger.error("Failed to refresh token: No new token received")
                return None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
            # Don't set token to None if refresh fails, keep the old token
            return token
    return token


async def require_valid_token(request: Request):
    """Dependency to ensure a valid token exists."""
    token = await refresh_token_if_expired()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"Location": "/login"},
        )
    return token
