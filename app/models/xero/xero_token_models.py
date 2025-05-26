from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class XeroToken(Base):
    __tablename__ = "xero_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_data = Column(Text, nullable=False)  # Store the full token JSON as text
    tenant_id = Column(
        String(200), nullable=True
    )  # Allow null initially since token is stored before tenant selection
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    class Config:
        orm_mode = True
