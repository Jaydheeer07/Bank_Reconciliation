import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.auth.oauth import (
    create_token_dict,
    oauth,
    obtain_xero_oauth2_token,
    store_xero_oauth2_token,
)
from backend.config import frontend_url

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse, description="Index page")
async def index(request: Request):
    token = obtain_xero_oauth2_token()
    if not token:
        return RedirectResponse(url="/login")
    # Redirect to the frontend dashboard page
    frontend_dashboard_url = (
         f"{frontend_url}/dashboard" # Update this URL as needed
    )
    return RedirectResponse(url=frontend_dashboard_url)


@router.get("/login", description="Login page")
async def login(request: Request):
    redirect_uri = request.url_for("oauth_callback")
    return await oauth.xero.authorize_redirect(request, redirect_uri)


@router.get("/callback", description="OAuth callback")
async def oauth_callback(request: Request):
    try:
        token = await oauth.xero.authorize_access_token(request)
        xero_token = create_token_dict(token)
        store_xero_oauth2_token(xero_token)
        return RedirectResponse(url="/")
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logout", description="Logout")
async def logout():
    store_xero_oauth2_token(None)
    return RedirectResponse(url="/login")
