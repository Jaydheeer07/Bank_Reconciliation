from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import app
from app.models.xero.tenant_models import DetailedErrorResponse, TenantError


@app.exception_handler(TenantError)
async def tenant_error_handler(request: Request, exc: TenantError):
    return JSONResponse(
        status_code=400,
        content=DetailedErrorResponse(
            detail=str(exc.message),
            error_code=exc.error_code,
            timestamp=datetime.now(datetime.timezone.utc).isoformat(),
        ).model_dump(),
    )
