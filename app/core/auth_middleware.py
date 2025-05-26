import logging
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import decode_access_token
from app.models.database.schema_models import User

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Optional[User]:
    """Get the current user from the Authorization header."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        # Extract token from Authorization header
        access_token = auth_header.replace("Bearer ", "")

        # Decode the token
        payload = decode_access_token(access_token)
        if payload == "expired":
            raise HTTPException(status_code=419, detail="Token has expired")
        if not payload:
            return None

        # Get user from database
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == payload.get("sub")).first()
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user from token: {str(e)}", exc_info=True)
        return None


async def AuthMiddleware(request: Request, call_next: Callable) -> Response:
    """FastAPI middleware to set the current user in request state."""

    # Only process HTTP requests
    if request.scope["type"] != "http":
        return await call_next(request)
    try:
        # Get and set the current user
        user = await get_current_user(request)
        request.state.user = user

        # Continue processing the request
        response = await call_next(request)
        return response
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
