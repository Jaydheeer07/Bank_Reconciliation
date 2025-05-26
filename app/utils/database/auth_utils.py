from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.database.schema_models import BlacklistedToken


def is_token_blacklisted(db: Session, token: str) -> bool:
    """Check if a token is blacklisted.
    
    Args:
        db: Database session
        token: The JWT token string to check
        
    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    
    return (
        db.query(BlacklistedToken)
        .filter(BlacklistedToken.token == token)
        .first() is not None
    )


def cleanup_expired_tokens(db: Session):
    # Clean up expired blacklisted tokens
    expiry = datetime.now(timezone.utc) - timedelta(
        minutes=settings.access_token_expire_minutes
    )
    db.query(BlacklistedToken).filter(BlacklistedToken.created_at < expiry).delete()
    db.commit()
