import logging
import secrets
import json
from datetime import datetime, timedelta, timezone
from jose import jwt

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, get_db
from app.core.email import send_password_reset_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.database.auth_models import PasswordReset, PasswordResetRequest, Token
from app.models.database.schema_models import (
    PasswordResetToken,
    RefreshToken,
    User,
    BlacklistedToken
)
from app.models.xero.xero_token_models import XeroToken

router = APIRouter()

logger = logging.getLogger(__name__)


class RefreshTokenRequest(BaseModel):
    token: str


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
    "/login",
    response_model=Token,
    description="Login with email and password",
    responses={
        200: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "token_type": "bearer",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "user_id": "1",
                        "xero": {
                            "access_token": "xero_access_token",
                            "refresh_token": "xero_refresh_token",
                            "expires_at": "xero_expires_at",
                            "token_type": "Bearer",
                            "tenant_id": "xero_tenant_id"
                        }
                    }
                }
            },
        },
        401: {"description": "Invalid credentials or account locked"},
    },
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
            logger.warning(
                f"Login blocked: Account locked until {user.locked_until} for user {email}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Account locked. Try again after {user.locked_until}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.now(timezone.utc)
            logger.warning(
                f"Login failed: Invalid password for user {email}. Failed attempts: {user.failed_login_attempts}"
            )

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.login_cooldown_minutes
                )
                logger.warning(
                    f"Account locked: Too many failed attempts for user {email}"
                )
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

        # Generate access and refresh tokens
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        refresh_token = create_refresh_token(db, user.id)

        # Get Xero tokens for the user
        xero_tokens = db.query(XeroToken).filter(XeroToken.user_id == user.id).all()
        xero_token_data = None
        if xero_tokens:
            # Get the most recent token
            latest_token = max(xero_tokens, key=lambda t: t.created_at)
            if latest_token and latest_token.token_data:
                # Parse the token data
                token_json = json.loads(latest_token.token_data)
                # Convert Unix timestamp to ISO format
                expires_at = datetime.fromtimestamp(
                    token_json.get("expires_at", 0), 
                    tz=timezone.utc
                ).isoformat()
                
                xero_token_data = {
                    "access_token": token_json.get("access_token"),
                    "refresh_token": token_json.get("refresh_token"),
                    "expires_at": expires_at,
                    "token_type": token_json.get("token_type", "Bearer"),
                    "tenant_id": latest_token.tenant_id
                }

        logger.info(f"Generated access token and refresh token for user {email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "xero": xero_token_data
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


@router.post("/refresh", response_model=Token, description="Refresh access token")
async def refresh_token(
    refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)
):
    try:
        stored_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token == refresh_request.token,
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
            "user_id": user.id
        }
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

        if token:
            # Decode token to get expiration time
            try:
                payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
                expires_at = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
                
                # Add token to blacklist
                blacklisted_token = BlacklistedToken(
                    token=token,
                    expires_at=expires_at
                )
                db.add(blacklisted_token)
            except jwt.JWTError:
                # If token is invalid, we still proceed with logout but log the error
                logger.warning("Failed to decode token during logout")
            
        # Remove all refresh tokens for the user from database
        db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
        db.commit()

        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


@router.post("/forgot-password", description="Request password reset")
async def request_password_reset(
    request: Request, reset_request: PasswordResetRequest, db: Session = Depends(get_db)
):
    """
    Request a password reset by sending a reset link to the user's email.

    Production Setup:
    ----------------
    1. Frontend should implement a reset password page at: /reset-password
    2. The page should accept a token parameter: /reset-password?token=[TOKEN]
    3. Update the reset_url to use frontend URL in production:
       reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    Current Implementation:
    ---------------------
    - In debug mode: Uses a temporary HTML form endpoint
    - In production: Should use frontend URL (see above)

    Flow:
    -----
    1. User requests password reset
    2. Backend generates secure token
    3. Email sent with reset link
    4. User clicks link
    5. Frontend handles password reset form
    6. Frontend calls /reset-password endpoint with token and new password
    """
    try:
        user = db.query(User).filter(User.email == reset_request.email).first()
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

        # Development: Use debug endpoint
        if settings.debug:
            server_url = str(request.url).split("/forgot-password")[0]
            reset_url = f"{server_url}/reset-password-form/{token}"
        else:
            # Production: Use frontend URL
            reset_url = f"{settings.frontend_url}/reset-password?token={token}"

        # Send reset email
        email_sent = send_password_reset_email(user.email, reset_url)

        if not email_sent:
            logger.error(f"Failed to send password reset email to {user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email",
            )

        return {"message": "If the email exists, a password reset link will be sent"}
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset request",
        )


@router.get("/reset-password-form/{token}", response_class=HTMLResponse)
async def reset_password_form(token: str):
    """
    DEBUG MODE ONLY: Serves a simple HTML form for password reset.

    This endpoint is for testing purposes only and is disabled in production.
    In production, password reset should be handled by the frontend application.

    Frontend Implementation:
    ----------------------
    1. Create a reset password page component
    2. Get token from URL query parameter
    3. Implement password form with validation
    4. Send POST request to /reset-password endpoint
    5. Handle success/error responses
    6. Redirect to login page on success
    """
    if not settings.debug:
        raise HTTPException(
            status_code=404, detail="This endpoint is only available in debug mode"
        )

    return f"""
    <html>
        <head>
            <title>Reset Password</title>
            <style> 
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 500px;
                    margin: 50px auto;
                    padding: 20px;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                input {{
                    width: 100%;
                    padding: 8px;
                    margin-top: 5px;
                }}
                button {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                button:hover {{
                    background-color: #45a049;
                }}
                .error {{
                    color: #f44336;
                    margin-top: 10px;
                }}
                .success {{
                    color: #4CAF50;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <h2>Reset Your Password</h2>
            <form id="resetForm">
                <div class="form-group">
                    <label for="password">New Password:</label>
                    <input type="password" id="password" name="new_password" required>
                </div>
                <div class="form-group">
                    <label for="confirm_password">Confirm Password:</label>
                    <input type="password" id="confirm_password" required>
                </div>
                <button type="submit">Reset Password</button>
            </form>
            <p id="message"></p>

            <script>
                document.getElementById('resetForm').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    const messageEl = document.getElementById('message');
                    messageEl.className = '';
                    
                    const password = document.getElementById('password').value;
                    const confirmPassword = document.getElementById('confirm_password').value;
                    
                    if (password !== confirmPassword) {{
                        messageEl.textContent = 'Passwords do not match!';
                        messageEl.className = 'error';
                        return;
                    }}
                    
                    try {{
                        const response = await fetch('/api/v1/reset-password', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                token: '{token}',
                                new_password: password
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        if (response.ok) {{
                            messageEl.textContent = 'Password reset successful! You can now login with your new password.';
                            messageEl.className = 'success';
                            document.getElementById('resetForm').style.display = 'none';
                        }} else {{
                            messageEl.textContent = data.detail || 'Failed to reset password';
                            messageEl.className = 'error';
                        }}
                    }} catch (error) {{
                        messageEl.textContent = 'An error occurred. Please try again.';
                        messageEl.className = 'error';
                        console.error('Error:', error);
                    }}
                }});
            </script>
        </body>
    </html>
    """


@router.post("/reset-password", description="Reset password using token from email")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Reset password using the token received via email.

    Frontend Integration:
    -------------------
    1. Frontend should send a POST request to this endpoint
    2. Request body should be JSON with:
       {
         "token": "token-from-url",
         "new_password": "user-entered-password"
       }
    3. Response will be:
       - 200: Password reset successful
       - 400: Invalid/expired token
       - 404: User not found
       - 500: Server error

    Security Notes:
    -------------
    - Token expires after 24 hours
    - Token is single-use (invalidated after reset)
    - All user's existing reset tokens are invalidated after reset
    """
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
                detail="Invalid or expired reset token. Please request a new password reset.",
            )

        # Get user and update password
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)

        # Remove all reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).delete()

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
