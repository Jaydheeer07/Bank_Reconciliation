import logging
import logging.config

from fastapi.middleware.cors import CORSMiddleware

from app.config import app

# Required import for error handler registration
from app.error_handlers import tenant_error_handler
from app.logging_settings import default_settings
from app.routes.brain import brain, files, transactions
from app.routes.user_account import login, user
from app.routes.xero import (
    accounts,
    auth,
    bank_transactions,
    contacts,
    invoices,
    tenants,
)

logging.config.dictConfig(default_settings)

# Allow CORS for all origins (adjust as needed for your use case)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router, tags=["Login and User Signup"])
app.include_router(user.router, tags=["User Account"])
app.include_router(auth.router, tags=["Xero Authentication"])
app.include_router(invoices.router, tags=["Xero Invoices"])
app.include_router(tenants.router, tags=["Xero Tenants"])
app.include_router(accounts.router, tags=["Xero Accounts"])
app.include_router(contacts.router, tags=["Xero Contacts"])
app.include_router(bank_transactions.router, tags=["Xero Bank Transactions"])
app.include_router(brain.router, tags=["Brain Details"])
app.include_router(files.router, tags=["Brain File Operations"])
app.include_router(transactions.router, tags=["Brain Transaction Operations"])


# Assign to a global variable to retain the import
_tenant_error_handler = tenant_error_handler

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
