import logging
from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.database.auth_models import TokenData
from app.models.database.schema_models import User
from app.utils.database.auth_utils import is_token_blacklisted

logger = logging.getLogger(__name__)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login", scheme_name="OAuth2PasswordBearer"
)


def get_db() -> Generator:
    """Dependency function to get database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        db.close()


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token or not isinstance(token, str):
        logger.warning("No valid token found in Authorization header")
        raise credentials_exception

    try:
        # First decode and validate the JWT token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("No email found in token payload")
            raise credentials_exception

        # Now check if the validated token is blacklisted
        if is_token_blacklisted(db, token):
            logger.warning("Token is blacklisted")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been blacklisted",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(email=email)
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        logger.warning(f"No user found for email: {token_data.email}")
        raise credentials_exception

    logger.info(f"Successfully authenticated user: {user.email}")
    request.state.user = user
    return user

async def get_current_user_id(
    current_user: User = Depends(get_current_user)
) -> str:
    """
    Get the current user's ID from the authenticated user object
    """
    return str(current_user.id)
