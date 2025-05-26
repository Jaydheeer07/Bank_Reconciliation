import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import get_password_hash
from app.models.database.schema_models import User
from app.models.database.user_models import UserCreate, UserResponse
from app.models.xero.xero_token_models import XeroToken
from app.config import settings
from app.models.brain.brain_model import BrainCreateRequest
from app.utils.http_client import post_json, HttpClientError, http_exception_handler

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse, description="Register a new user")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    try:
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            role="user",
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Create a brain for the new user
        try:
            brain_request = BrainCreateRequest(
                name=f"brain_{user_data.email}",
                description=f"Brain for {user_data.email}"
            )
            
            brain_data = await post_json(
                f"{settings.brain_base_url}/v1/brain",
                json=brain_request.model_dump(),
                log_message=f"create brain for user {user_data.email}"
            )
            
            # Log the full response for debugging
            logger.info(f"Brain service response: {brain_data}")
            
            # Check if the response contains the expected 'id' field
            if 'id' not in brain_data:
                raise ValueError("Invalid response format from brain service: 'id' key missing")
            
            # Store brain information in user record
            db_user.brain_name = f"brain_{user_data.email}"  # Set brain_name explicitly
            db_user.brain_id = brain_data['id']  # Use the 'id' from the response
            db.commit()  # Ensure the changes are committed to the database
            db.refresh(db_user)  # Refresh the user object to reflect the changes
            
            logger.info(f"Successfully created brain for user {user_data.email}")
        except HttpClientError as e:
            logger.error(f"Failed to create brain for user {user_data.email}: {e.detail}")
            # Continue with user creation even if brain creation fails
        except Exception as brain_error:
            logger.error(f"Failed to create brain for user {user_data.email}: {str(brain_error)}")
            # Continue with user creation even if brain creation fails

        return db_user
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )

@router.get("/me", response_model=UserResponse, description="Get current user profile")
async def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get Xero authentication status and active tenant
        xero_token = db.query(XeroToken).filter(XeroToken.user_id == current_user.id).first()

        # Create response with additional fields
        user_data = {
            **current_user.__dict__,
            "xero_authenticated": bool(xero_token),
            "active_tenant_id": xero_token.tenant_id if xero_token else None
        }

        return user_data
    except Exception as e:
        logger.error(f"Read current user error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user profile",
        )


@router.get("/users", response_model=List[UserResponse], description="Get all users")
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check permissions first
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return users
    except Exception as e:
        logger.error(f"Read users error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving users"
        )