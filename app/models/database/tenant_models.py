from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class TenantMetadata(Base):
    """Model for storing tenant metadata and their associated PostgreSQL tables."""
    __tablename__ = "tenant_metadata"
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String, nullable=False)
    tenant_name = Column(String, nullable=False)
    tenant_short_code = Column(String, nullable=True)  # Some organizations might not have a short code
    table_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationship with the user table
    user = relationship("User", back_populates="tenants")

    def __repr__(self):
        return f"<TenantMetadata(id={self.id}, tenant_name='{self.tenant_name}', table_name='{self.table_name}')>"
