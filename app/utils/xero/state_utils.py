import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.xero.xero_state_models import XeroState


def generate_state_parameter() -> str:
    """Generate a secure random state parameter"""
    return secrets.token_urlsafe(32)


def store_state(db: Session, state: str, user_id: str, ttl_seconds: int = 600) -> None:
    """
    Store state parameter with user ID and expiration

    Args:
        db: Database session
        state: State parameter to store
        user_id: ID of the user initiating OAuth
        ttl_seconds: Time-to-live in seconds (default 10 minutes)
    """
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    xero_state = XeroState(state=state, user_id=user_id, expires_at=expires_at)
    db.add(xero_state)
    db.commit()


def validate_state(db: Session, state: str) -> Optional[str]:
    """
    Validate state parameter and return associated user_id if valid

    Args:
        db: Database session
        state: State parameter to validate

    Returns:
        user_id if state is valid and not expired, None otherwise
    """
    xero_state = db.query(XeroState).filter(XeroState.state == state).first()

    if not xero_state:
        return None

    current_time = datetime.now(timezone.utc)
    expires_at = xero_state.expires_at
    
    # Ensure expires_at has timezone info
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < current_time:
        return None

    return xero_state.user_id


def cleanup_expired_states(db: Session) -> None:
    """Clean up all expired state parameters"""
    current_time = datetime.now(timezone.utc)
    expired_states = db.query(XeroState).filter(
        XeroState.expires_at < current_time
    ).all()
    
    for state in expired_states:
        if state.expires_at.tzinfo is None:
            expires_at = state.expires_at.replace(tzinfo=timezone.utc)
            if expires_at < current_time:
                db.delete(state)
        else:
            db.delete(state)
    
    db.commit()
