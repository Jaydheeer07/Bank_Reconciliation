from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class XeroState(Base):
    """SQLAlchemy model for storing Xero OAuth state parameters"""
    __tablename__ = "xero_states"

    state = Column(String, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship to user
    user = relationship("User", back_populates="xero_states")


# Pydantic models for API responses
class XeroAuthResponse(BaseModel):
    """Response model for Xero authentication initiation"""
    authorization_url: str
    state: str


class XeroAuthStatus(BaseModel):
    """Response model for Xero authentication status"""
    status: str
    message: str
    token_type: str | None = None
    expires_at: str | None = None
    scopes: list[str] | None = None
    

class XeroCallbackResponse(BaseModel):
    """Response model for Xero OAuth callback"""
    status: str
    message: str
    redirect_url: str | None = None
