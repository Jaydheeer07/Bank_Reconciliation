import logging

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from app.core.oauth import (
    create_token_dict,
    oauth,
    refresh_token_if_expired,
    store_xero_oauth2_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/xero-login", description="Login page for Xero")
async def login(request: Request):
    try:
        redirect_uri = request.url_for("oauth_callback")
        logger.info(f"Redirecting to OAuth login with redirect URI: {redirect_uri}")
        return await oauth.xero.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/xero-callback", description="OAuth callback")
async def oauth_callback(request: Request):
    try:
        token = await oauth.xero.authorize_access_token(request)
        xero_token = create_token_dict(token)
        store_xero_oauth2_token(xero_token)
        logger.info("OAuth callback successful, redirecting to home.")
        return RedirectResponse(url="/xero-login")
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/xero-logout", description="Logout")
async def logout():
    try:
        store_xero_oauth2_token(None)
        logger.info("User logged out successfully.")
        return RedirectResponse(url="/login")
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/refresh", description="Refresh token")
async def refresh_token_endpoint(response: Response):
    """Endpoint to refresh the token if expired."""
    new_token = await refresh_token_if_expired()
    if new_token:
        response.headers["Authorization"] = f"Bearer {new_token.get('access_token')}"
        logger.info(f"Token refreshed successfully: {new_token}")
        return {"message": "Token refreshed successfully", "token": new_token}
    else:
        raise HTTPException(status_code=401, detail="Failed to refresh token")
