# Backend API Documentation

This document provides instructions on how to set up, run, and use the backend API.

## Introduction

This backend API is built using FastAPI and provides endpoints to interact with Xero accounting data. It includes endpoints for retrieving accounts, contacts, and invoices.

## Setup

### Prerequisites

- Python 3.6 or higher
- FastAPI
- Xero Python SDK

### Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/Jaydheeer07/Bank_Reconciliation.git
    cd backend
    ```

2. Create a virtual environment:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables. Create a `.env` file in the root directory and add the necessary environment variables:

    ```ini
        # OAuth settings
        CLIENT_ID="your_client_id"
        CLIENT_SECRET_KEY="your_client_secret"
        SECRET_KEY="your_secret_key"

        # Environment settings
        ENV="development"
        DEBUG=true

        # Brain settings
        API_KEY="your_brain_api_key"
        BRAIN_BASE_URL="your_brain_base_url"

        # Frontend settings
        FRONTEND_URL="your_frontend_url"

        # JWT settings
        JWT_SECRET_KEY="your_jwt_secret"
        JWT_ALGORITHM="HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        REFRESH_TOKEN_EXPIRE_DAYS=30

        # Database settings
        DATABASE_URL="your_database_url"
        MAX_LOGIN_ATTEMPTS=3
        LOGIN_COOLDOWN_MINUTES=2

        # Xero endpoints
        XERO_METADATA_URL="https://identity.xero.com/.well-known/openid-configuration"
        XERO_TOKEN_ENDPOINT="https://identity.xero.com/connect/token"

        # OAuth Xero scope
        SCOPE="offline_access openid profile email accounting.transactions accounting.journals.read accounting.transactions payroll.payruns accounting.reports.read files accounting.settings.read accounting.settings accounting.attachments payroll.payslip payroll.settings files.read openid assets.read profile payroll.employees projects.read email accounting.contacts.read accounting.attachments.read projects assets accounting.contacts payroll.timesheets accounting.budgets.read"

    ```

### Running the Server

1. Ensure you have activated your virtual environment:

    ```sh
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2. Start the FastAPI server:

    ```sh
    python run.py
    ```

3. The server will start and be accessible at `http://127.0.0.1:8000`. You can also view the Swagger documentation at `http://127.0.0.1:8000/docs`.

## Sample API Endpoints

### 1. Retrieve Accounts
- **Endpoint**: `/accounts`
- **Method**: `GET`
- **Description**: Retrieve a list of accounts for the selected Xero organization.
- **Response**: JSON array of accounts.

### 2. Select an Account by ID
- **Endpoint**: `/select-account/{account_id}`
- **Method **: `POST`
- **Description**: Select a specific account by ID.
- **Response**: JSON object with success message and selected account details.

### 3. Retrieve Selected Account
- **Endpoint**: `/selected-account`
- **Method**: `GET`
- **Description**: Get information about the currently selected account.
- **Response**: JSON object with chosen account details.

### 2 . Retrieve Contacts
- **Endpoint**: `/contacts`
- **Method**: `GET`
- **Description**: Retrieve a list of contacts.
- **Response**: JSON array of contacts.

### 3. Retrieve Invoices
- **Endpoint**: `/invoices`
- **Method**: `GET`
- **Description**: Retrieve a list of invoices.
- **Response**: JSON array of invoices.

### 4. Retrieve a Specific Invoice
- **Endpoint**: `/invoices/{invoice_id}`
- **Method**: `GET`
- **Description**: Retrieve a specific invoice by ID.
- **Response**: JSON object of the invoice.

### 5. Create Invoices
- **Endpoint**: `/create-invoices`
- **Method**: `PUT`
- **Description**: Create new invoices.
- **Request Body**: JSON object of the invoices to be created.
- **Response**: JSON object with success message and created invoices.

### 6. Create Invoice Attachment
- **Endpoint**: `/invoice-attachment/{invoice_id}`
- **Method**: `PUT`
- **Description**: Create a new invoice attachment.
- **Request Body**: Form data with the file to be uploaded.
- **Response**: JSON object with success message and attachment details.

### 7. Get Bank Transactions
- **Endpoint**: `/bank-transactions`
- **Method**: `GET`
- **Description**: Returns a list of bank transactions for the current tenant.
- **Response**: JSON array of bank transactions.

### 8. Get Tenants
- **Endpoint**: `/tenants`
- **Method**: `GET`
- **Description**: Returns a list of tenants for the current user.
- **Response**: JSON array of tenants.

### 9. Select a Tenant
- **Endpoint**: `/select-tenant/{tenant_id}`
- **Method**: `POST`
- **Description**: Selects a specific Xero tenant ID.
- **Response**: JSON object with success message and selected tenant ID.

### 10. Get Selected Tenant
- **Endpoint**: `/selected-tenant`
- **Method**: `GET`
- **Description**: Returns the currently selected tenant ID.
- **Response**: JSON object with the selected tenant details.

### 11. Get Selected Account
- **Endpoint**: `/selected-account`
- **Method**: `GET`
- **Description**: Get information about the currently selected bank account.
- **Response**: JSON object with account details.

### 12. Select an Account
- **Endpoint**: `/select-account/{account_id}`
- **Method**: `POST`
- **Description**: Select and store a specific bank account ID for transaction retrieval.
- **Response**: JSON object with success message and selected account details.


### 13. Get a List of Brains
- **Endpoint**: `/brains`
- **Method**: `GET`
- **Description**: Retrieve a list of available brains.
- **Response**: JSON array of brains.

### 14. Get a Specific Brain
- **Endpoint**: `/brains/{brain_id}`
- **Method**: `GET`
- **Description**: Retrieve information about a specific brain.
- **Response**: JSON object of the brain.

### 15. Create a Brain
- **Endpoint**: `/brains/create`
- **Method**: `POST`
- **Description**: Create a new brain.
- **Request Body**: Name and description of the brain.
- **Response**: JSON object with success message and created brain details.

### 16. Upload a file
- **Endpoint**: `/upload-file`
- **Method**: `POST`
- **Description**: Upload a file to the server. 
- **Request Body**: File to be uploaded, brain_id, and document_type (whether it's a statement or an invoice).
- **Response**: JSON object with success message and uploaded file details.

### 17. Get details of a specific file
- **Endpoint**: `/file/{file_id}`
- **Method**: `GET`
- **Description**: Retrieve details of a specific file by its ID.
- **Response**: JSON object with file details.

### 18. Get a list of files
- **Endpoint**: `/files`
- **Method**: `GET`
- **Description**: Retrieve a list of files.
- **Response**: JSON array of files.

### 19. Get Invoice Transactions
- **Endpoint**: `/transactions/invoices`
- **Method**: `GET`
- **Description**: Retrieve a list of invoice transactions.
- **Response**: JSON array of invoice transactions.

## Error Handling
The API returns appropriate error responses for various scenarios, including authentication errors, invalid requests, and more.

## Authentication
The API uses OAuth2 for authentication. Ensure you have the necessary credentials to access the Xero API.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.
