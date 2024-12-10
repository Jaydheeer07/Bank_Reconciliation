from datetime import date as DateType
from typing import List, Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str = Field(alias="Description")
    quantity: int = Field(alias="Quantity")
    unit_amount: float = Field(alias="UnitAmount")
    account_code: str = Field(alias="AccountCode")
    tax_type: str = Field(alias="TaxType")

    class Config:
        populate_by_name = True


class Contact(BaseModel):
    contact_id: str = Field(alias="ContactID")

    class Config:
        populate_by_name = True


class Invoice(BaseModel):
    type: str = Field(..., pattern="^(ACCREC|ACCPAY)", alias="Type")
    contact: Contact = Field(alias="Contact")
    line_items: List[LineItem] = Field(alias="LineItems")
    date: DateType = Field(alias="Date")
    due_date: DateType = Field(alias="DueDate")
    invoice_number: str = Field(alias="InvoiceNumber")
    status: str = Field(..., pattern="^(DRAFT|SUBMITTED|AUTHORISED)$", alias="Status")
    currency_code: str = Field(default="AUD", alias="CurrencyCode")
    reference: Optional[str] = Field(alias="Reference")
  
    class Config:
        populate_by_name = True


class InvoiceRequest(BaseModel):
    invoices: List[Invoice] = Field(alias="Invoices")

    class Config:
        populate_by_name = True


class TenantSelect(BaseModel):
    tenantId: str

class DetailedErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: str

# Custom exception for tenant-related errors
class TenantError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


