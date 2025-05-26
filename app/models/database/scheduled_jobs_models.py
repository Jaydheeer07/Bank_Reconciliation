from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.database import Base


class ScheduledJob(Base):
    """Model to track active scheduled jobs per user/tenant"""

    __tablename__ = "scheduled_jobs"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), nullable=False)
    brain_id = Column(String(100), nullable=False)  # Increased length to accommodate brain_ prefix
    job_type = Column(String(50), nullable=False)  # 'invoice' or 'statement'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
