import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class BankReconciliation(Base):
    __tablename__ = "bank_reconciliation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_name = Column(String, nullable=False)
    account_name = Column(String, nullable=False)
    transaction_date = Column(Date, nullable=False)
    payee = Column(String, nullable=False)
    particulars = Column(String, nullable=False)
    spent = Column(Numeric(10, 2))
    received = Column(Numeric(10, 2))
    start_date = Column(Date)
    end_date = Column(Date)
    min_amount = Column(Numeric(10, 2))
    max_amount = Column(Numeric(10, 2))
    details = Column(String)
    name_ref = Column(String)
    exact_amount = Column(Numeric(10, 2))
    file_name = Column(String, nullable=False)
    insert_time = Column(Date, nullable=False)
    inserted_by = Column(String, nullable=False)

    def __repr__(self):
        return f"<BankReconciliation(client_name='{self.client_name}', transaction_date='{self.transaction_date}')>"


class DraftReconciliationEntry(Base):
    __tablename__ = "draft_reconciliation_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_shortcode = Column(String, nullable=False)
    statement_id = Column(String, nullable=False)
    invoice_id = Column(String, nullable=True)
    statement_client_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    transaction_date = Column(DateTime, nullable=True)
    payee = Column(String, nullable=True)
    particulars = Column(String, nullable=True)
    statement_amount = Column(
        Numeric(10, 2), nullable=True
    )  # Changed from received boolean
    file_name = Column(String, nullable=True)
    invoice_client_name = Column(String, nullable=True)
    details = Column(String, nullable=True)
    invoice_date = Column(DateTime, nullable=True)
    invoice_amount = Column(
        Numeric(10, 2), nullable=True
    )  # Changed from total_amount string
    status = Column(String, nullable=True)
    verified = Column(Boolean, default=False, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<DraftReconciliationEntry(statement_client_name='{self.statement_client_name}', transaction_date='{self.transaction_date}')>"
