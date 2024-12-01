from typing import List

from pydantic import BaseModel


class BrainCreateRequest(BaseModel):
    name: str
    description: str = None


class ReconciliationVerification(BaseModel):
    statementId: str
    invoiceIds: List[str]
