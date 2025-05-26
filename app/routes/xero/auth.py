import json
import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, get_db
from app.core.oauth import (
    create_token_dict,
    oauth,
    refresh_token_if_expired,
    store_xero_oauth2_token,
)
from app.models.database.schema_models import User
from app.models.xero.xero_state_models import XeroAuthStatus, XeroCallbackResponse
from app.models.xero.xero_token_models import XeroToken
from app.utils.xero.state_utils import (
    generate_state_parameter,
    store_state,
    validate_state,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/xero/auth")


@router.get(
    "/", response_model=XeroAuthStatus, description="Check authentication status"
)
async def index(request: Request, current_user: User = Depends(get_current_user)):
    """
    Check the current authentication status:
    - If authenticated: Returns token info
    - If not authenticated: Returns status with redirect URL
    """
    try:
        db = next(get_db())
        token_record = (
            db.query(XeroToken)
            .filter(XeroToken.user_id == str(current_user.id))
            .first()
        )

        if token_record and token_record.token_data:
            token = json.loads(token_record.token_data)

            # If we have a token, check if it's expired
            if token.get("expires_at", 0) < time.time():
                logger.info("Token has expired, attempting to refresh")
                try:
                    # Try to refresh the token
                    refreshed_token = await refresh_token_if_expired(request, current_user)
                    if refreshed_token:
                        logger.info("Token refreshed successfully")
                        return XeroAuthStatus(
                            status="authenticated",
                            message="Successfully refreshed authentication with Xero",
                            token_type=refreshed_token.get("token_type"),
                            expires_at=datetime.fromtimestamp(refreshed_token.get("expires_at", 0)).isoformat() if refreshed_token.get("expires_at") else None,
                            scopes=refreshed_token.get("scope", "").split() if refreshed_token.get("scope") else None,
                        )
                    else:
                        # If refresh failed, redirect to login
                        logger.warning("Token refresh failed, redirect to login required")
                        return XeroAuthStatus(
                            status_code=status.HTTP_403_FORBIDDEN,
                            status="expired",
                            message="Session has expired and refresh failed",
                            redirect_url="/api/v1/xero/auth/login",
                        )
                except Exception as refresh_error:
                    logger.error(f"Error refreshing token: {str(refresh_error)}", exc_info=True)
                    return XeroAuthStatus(
                        status_code=status.HTTP_403_FORBIDDEN,
                        status="expired",
                        message="Session has expired",
                        redirect_url="/api/v1/xero/auth/login",
                    )

            # Token exists and is valid
            return XeroAuthStatus(
                status="authenticated",
                message="Successfully authenticated with Xero",
                token_type=token.get("token_type"),
                expires_at=datetime.fromtimestamp(token.get("expires_at", 0)).isoformat() if token.get("expires_at") else None,
                scopes=token.get("scope", "").split() if token.get("scope") else None,
            )

        # Handle case when no token exists
        logger.info("No active token found, redirect to login required")
        return XeroAuthStatus(
            status="unauthenticated",
            message="No active session found",
            redirect_url="/api/v1/xero/auth/login",
        )

    except Exception as e:
        logger.error(f"Error checking authentication status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    finally:
        if "db" in locals():
            db.close()


@router.get("/login", response_class=JSONResponse, description="Login page for Xero")
async def login(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate Xero OAuth flow with state parameter for CSRF protection
    """
    try:
        # Generate and store state parameter
        state = generate_state_parameter()
        store_state(db, state, current_user.id)

        # Get redirect URI
        redirect_uri = request.url_for("oauth_callback")
        if settings.env != "development":
            redirect_uri = str(redirect_uri).replace("http://", "https://")

        logger.info(
            f"Redirecting to OAuth login with redirect URI: {redirect_uri} and state: {state}"
        )

        # Get the authorization redirect response
        redirect_response = await oauth.xero.authorize_redirect(
            request, redirect_uri, state=state
        )

        # Extract the URL from the redirect response
        auth_url = str(redirect_response.headers.get("location"))

        # Return JSON response with CORS headers
        return JSONResponse(
            content={"auth_url": auth_url},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/callback", response_model=XeroCallbackResponse, description="OAuth callback"
)
async def oauth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Xero OAuth callback with state parameter validation
    """
    try:
        # Get state from query params
        state = request.query_params.get("state")
        if not state:
            logger.error("No state parameter in callback")
            return XeroCallbackResponse(
                status="error",
                message="Invalid authentication session",
                redirect_url="/api/v1/xero/auth/login",
            )

        # Validate state parameter
        user_id = validate_state(db, state)
        if not user_id:
            logger.error("Invalid or expired state parameter")
            return XeroCallbackResponse(
                status="error",
                message="Invalid or expired authentication session",
                redirect_url="/api/v1/xero/auth/login",
            )

        # Get the authorization code from Xero
        token = await oauth.xero.authorize_access_token(request)
        if not token:
            logger.error("Failed to get access token")
            return XeroCallbackResponse(
                status="error",
                message="Failed to authenticate with Xero",
                redirect_url="/api/v1/xero/auth/login",
            )

        # Store the token with user_id
        token_dict = create_token_dict(token)
        store_xero_oauth2_token(token_dict, user_id)

        logger.info("Successfully authenticated with Xero")
        # return XeroCallbackResponse(
        #     status="success",
        #     message="Successfully authenticated with Xero",
        #     redirect_url="/api/v1/xero/auth",
        # )
        return RedirectResponse(url=f"{settings.frontend_url}/dashboard")

    except Exception as e:
        logger.error(f"Error in callback endpoint: {str(e)}", exc_info=True)
        return XeroCallbackResponse(
            status="error",
            message=f"Authentication failed: {str(e)}",
            redirect_url="/api/v1/xero/auth/login",
        )


@router.post("/refresh", description="Refresh token")
async def refresh_token_endpoint(
    request: Request, response: Response, current_user: User = Depends(get_current_user)
):
    """
    Endpoint to refresh the token if expired.

    Returns:
        - New token if refresh successful
        - 401 with re-auth URL if refresh token expired
        - 401 for other failures
    """
    try:
        new_token = await refresh_token_if_expired(request, current_user)
        if new_token:
            response.headers["Authorization"] = (
                f"Bearer {new_token.get('access_token')}"
            )
            logger.info("Token refreshed successfully")
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Token refreshed successfully",
                    "expires_at": datetime.fromtimestamp(
                        new_token.get("expires_at", 0)
                    ).isoformat(),
                }
            )
        else:
            logger.warning("Token refresh failed, redirect to login required")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "message": "Token refresh failed",
                    "redirect_url": "/api/v1/xero/auth/login",
                },
            )

    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "error",
                "message": "Error refreshing token",
                "error": str(e),
                "redirect_url": "/api/v1/xero/auth/login",
            },
        )


@router.get("/config", description="Debug OAuth configuration")
async def debug_config():
    return {
        "client_id": settings.client_id,
        "metadata_url": settings.xero_metadata_url,
        "token_endpoint": settings.xero_token_endpoint,
        "scope": settings.scope,
    }
