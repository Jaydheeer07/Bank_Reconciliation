import logging
import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import app
from app.error_handlers import tenant_error_handler
from app.logging_settings import default_settings
from app.routes.brain import me, files, transactions
from app.routes.user_account import login, user
from app.routes.xero import (
    auth,
    bank_transactions,
    contacts,
    invoices,
    tenants,
    organisations
)
from app.scheduled_tasks.job_manager import start_jobs_on_startup, scheduler
from app.tests import test_db_connection
from app.core.auth_middleware import AuthMiddleware
from app.core.deps import get_db

logging.config.dictConfig(default_settings)

# Allow CORS for all origins (adjust as needed for your use case)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://dexterous-portal.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Startup
    db = next(get_db())
    start_jobs_on_startup(db)
    yield
    # Shutdown
    scheduler.shutdown()

app.router.lifespan_context = lifespan
# Add authentication middleware
app.middleware("http")(AuthMiddleware)

# Add all routers with /api/v1 prefix
app.include_router(login.router, prefix="/api/v1", tags=["Login and User Signup"])
app.include_router(user.router, prefix="/api/v1", tags=["User Account"])

# Add Xero routers with their own prefixes
app.include_router(auth.router, prefix="/api/v1", tags=["Xero Authentication"])
app.include_router(invoices.router, prefix="/api/v1", tags=["Xero Invoices"])
app.include_router(tenants.router, prefix="/api/v1", tags=["Xero Tenants"])
app.include_router(contacts.router, prefix="/api/v1", tags=["Xero Contacts"])
app.include_router(
    bank_transactions.router, prefix="/api/v1", tags=["Xero Bank Transactions"]
)
app.include_router(organisations.router, prefix="/api/v1", tags=["Xero Organisations"])
# Add brain routers with their own prefixes
app.include_router(me.router, prefix="/api/v1", tags=["Brain Details"])
app.include_router(files.router, prefix="/api/v1", tags=["Brain File Operations"])
app.include_router(
    transactions.router, prefix="/api/v1", tags=["Brain Transaction Operations"]
)

# Include test routes (only in development)
app.include_router(test_db_connection.router, prefix="/api/v1", tags=["Tests"])

# Assign to a global variable to retain the import
_tenant_error_handler = tenant_error_handler

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
