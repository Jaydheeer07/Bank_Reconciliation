from pydantic import BaseModel


class Tenant(BaseModel):
    tenantId: str
    tenantName: str
    tenantType: str
    lastAccessed: str

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
