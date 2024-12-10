from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from app.config import settings
from app.database import SessionLocal
from app.models.database.schema_models import User
from app.models.database.auth_models import TokenData
from app.utils.database.auth_utils import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
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

    # Try to get token from cookie if not in header
    if not token and request and request.cookies.get("access_token"):
        token = request.cookies.get("access_token").replace("Bearer ", "")
        logger.info("Using token from cookie")
    elif token:
        logger.info("Using token from Authorization header")
    else:
        logger.warning("No token found in either cookie or Authorization header")
        raise credentials_exception

    if is_token_blacklisted(db, token):
        logger.warning("Token is blacklisted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been blacklisted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            logger.warning("No email found in token payload")
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        logger.warning(f"No user found for email: {token_data.email}")
        raise credentials_exception
    
    logger.info(f"Successfully authenticated user: {user.email}")
    return user
