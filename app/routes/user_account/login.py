import logging
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.database.auth_models import PasswordReset, PasswordResetRequest, Token
from app.models.database.schema_models import (
    BlacklistedToken,
    PasswordResetToken,
    RefreshToken,
    User,
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/", response_class=JSONResponse, description="Index page")
async def index(request: Request, current_user: User = Depends(get_current_user)):
    try:
        logger.info("Accessing index endpoint")
        if current_user is None:
            logger.warning("No authenticated user found")
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail="Redirecting to login",
                headers={"Location": "/login"},
            )
        
        logger.info(f"Authenticated user accessing index: {current_user.email}")
        # Provide a simple response indicating the backend is running
        return JSONResponse(
            status_code=200,
            content={
                "message": "Backend is running. Use the API documentation to interact with the endpoints."
            },
        )
    except Exception as e:
        logger.error(f"Error in index endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post(
    "/login", response_model=Token, description="Login with email and password"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Login endpoint that accepts both form data and JSON.
    Form data is used by Swagger UI, while JSON can be used for API calls.
    """
    try:
        logger.info(f"Login attempt for email: {form_data.username}")
        email = form_data.username
        password = form_data.password

        user = db.query(User).filter(User.email == email).first()

        # Handle non-existent user
        if not user:
            logger.warning(f"Login failed: User not found for email {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            logger.warning(f"Login blocked: Account locked until {user.locked_until} for user {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account locked. Try again after {user.locked_until}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.now(timezone.utc)
            logger.warning(f"Login failed: Invalid password for user {email}. Failed attempts: {user.failed_login_attempts}")

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.login_cooldown_minutes
                )
                logger.warning(f"Account locked: Too many failed attempts for user {email}")
            db.commit()

            # Calculate remaining attempts
            remaining_attempts = (
                settings.max_login_attempts - user.failed_login_attempts
            )
            detail = "Incorrect email or password"
            if remaining_attempts > 0:
                detail += f". {remaining_attempts} attempts remaining"
            else:
                detail += (
                    f". Account locked for {settings.login_cooldown_minutes} minutes"
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.locked_until = None
        user.last_successful_login = datetime.now(timezone.utc)
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Login successful for user {email}")

        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        refresh_token = create_refresh_token(db, user.id)

        logger.info(f"Generated access token and refresh token for user {email}")

        response = JSONResponse(
            content={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        )
        
        # Set httponly cookie with the access token
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=settings.env == "production",  # True in production
            samesite="lax",
            max_age=settings.access_token_expire_minutes * 60
        )
        
        logger.info(f"Set access token cookie for user {email}")
        return response
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


@router.post("/refresh", response_model=Token, description="Refresh access token")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        stored_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token == refresh_token,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user = db.query(User).filter(User.id == stored_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Create new tokens
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        new_refresh_token = create_refresh_token(db, user.id)

        # Invalidate old refresh token
        db.delete(stored_token)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


@router.post("/logout", description="Logout user")
async def logout(
    token: str = Depends(OAuth2PasswordRequestForm),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Blacklist the current access token
        blacklisted_token = BlacklistedToken(token=token)
        db.add(blacklisted_token)

        # Remove all refresh tokens for the user
        db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()

        db.commit()
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout",
        )


@router.post("/forgot-password", description="Request password reset")
async def request_password_reset(
    request: PasswordResetRequest, db: Session = Depends(get_db)
):
    """
    Request a password reset. In a real application, this would send an email
    with the reset token. For this example, we'll just return the token.
    """
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Don't reveal that the user doesn't exist
            return {
                "message": "If the email exists, a password reset link will be sent"
            }

        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # Store reset token
        reset_token = PasswordResetToken(
            user_id=user.id, token=token, expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()

        # In a real application, send email with reset link
        # For demo purposes, return the token
        return {
            "message": "Password reset instructions sent",
            "token": token,  # Remove this in production
        }
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset request",
        )


@router.post("/reset-password", description="Reset password using token")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password using the token received in email"""
    try:
        # Find valid reset token
        token_record = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token == reset_data.token,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Get user and update password
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)

        # Remove used token
        db.delete(token_record)

        # Reset login-related fields
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.locked_until = None

        db.commit()

        return {"message": "Password has been reset successfully"}
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset",
        )
