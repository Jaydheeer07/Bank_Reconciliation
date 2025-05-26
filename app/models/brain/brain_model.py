from typing import Any, Dict, List, Union

from pydantic import BaseModel


class BrainCreateRequest(BaseModel):
    name: str
    description: str = None


class ReconciliationVerification(BaseModel):
    statementId: str
    invoiceIds: List[str]


class TextProcessRequest(BaseModel):
    text: Union[str, Dict[str, Any]]
    brain_id: str
    document_type: str
