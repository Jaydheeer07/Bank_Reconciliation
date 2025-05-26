# Xero Integration API Documentation

This document provides detailed information about the Xero integration endpoints in the Bank Reconciliation API.

## Base URL

All endpoints are prefixed with `/api/v1`

## Important: Authentication Flow

Due to Xero's OAuth2 requirements, the authentication process must be initiated through a web browser. You cannot complete the OAuth flow directly in Postman.

### Authentication Steps

1. Open your browser and navigate to your local development server's login URL:

   ```plaintext
   http://localhost:8000/api/v1/xero/auth/login
   ```

2. Complete the Xero authentication process in the browser
3. After successful authentication, you'll be redirected back to your application
4. The tokens will be stored in your application's session/storage
5. You can then use these tokens for subsequent API requests in Postman

## Authentication Endpoints

### Check Authentication Status

- **Endpoint**: `GET /api/v1/xero/auth/`
- **Description**: Checks the current Xero authentication status
- **Response**:
  - When not authenticated:

    ```json
    {
        "status": "unauthenticated",
        "message": "No active session found",
        "redirect_url": "/api/v1/xero/auth/login"
    }
    ```

  - When token is expired:

    ```json
    {
        "status": "expired",
        "message": "Session has expired",
        "redirect_url": "/api/v1/xero/auth/login"
    }
    ```

  - When authenticated:

    ```json
    {
        "status": "authenticated",
        "message": "Successfully authenticated with Xero",
        "token_type": "Bearer",
        "expires_at": "2024-12-13T23:43:25",
        "scopes": ["offline_access", "accounting.transactions", ...]
    }
    ```

  - When logged out:

    ```json
    {
        "status": "success",
        "message": "Successfully logged out from Xero"
    }
    ```

### Login to Xero (Browser Only)

- **Endpoint**: `GET /api/v1/xero/auth/login`
- **Description**: Initiates the OAuth2 login flow with Xero
- **Note**: This endpoint must be accessed through a web browser, not Postman
- **Response**: Redirects to Xero's authentication page

### OAuth Callback

- **Endpoint**: `GET /api/v1/xero/auth/callback`
- **Description**: Callback endpoint for Xero OAuth2 flow
- **Note**: This is handled automatically after browser authentication
- **Response**: Handles the OAuth token response and stores the credentials

### Logout

- **Endpoint**: `GET /api/v1/xero/auth/logout`
- **Description**: Logs out from Xero by clearing tokens and session data
- **Response**: Redirects to login page

### Refresh Token

- **Endpoint**: `POST /api/v1/xero/auth/refresh`
- **Description**: Refreshes the Xero OAuth token if it's expired
- **Response**: Returns the new token information

## Important Notes on OAuth2 flow

- The OAuth flow requires proper configuration of client ID and client secret in the application settings
- Visit <https://developer.xero.com/app/manage> to acquire client ID and client secret
- The redirect URI should be set to <http://localhost:8000/api/v1/xero/auth/callback> or your local development server
- Refer to Xero Developers documentation for more details: <https://developer.xero.com/documentation/getting-started-guide/>
- For security reasons, always log out when finished testing
- Browser authentication is required due to Xero's OAuth2 security requirements

## Tenant Management

The tenant endpoints allow you to manage and interact with different Xero organizations (tenants) that the authenticated user has access to.

### List All Tenants

- **Endpoint**: `GET /api/v1/xero/tenants`
- **Description**: Retrieves a list of all available Xero organizations/tenants
- **Authentication**: Requires valid Xero OAuth token
- **Response**:

  ```json
  {
    "tenants": [
      {
        "tenantId": "xxx-xxx-xxx",
        "tenantName": "My Company Ltd",
        "tenantType": "ORGANISATION",
        "lastAccessed": "2024-12-14T02:16:40+08:00"
      },
      {
        "tenantId": "yyy-yyy-yyy",
        "tenantName": "Another Business",
        "tenantType": "ORGANISATION",
        "lastAccessed": "2024-12-14T02:16:40+08:00"
      }
    ]
  }
  ```

- **Error Responses**:
  - When no tenants are found:

    ```json
    {
      "detail": "No available organizations found"
    }
    ```

  - When fetching fails:

    ```json
    {
      "detail": "Failed to fetch organizations"
    }
    ```

### Set Active Tenant

- **Endpoint**: `PUT /api/v1/xero/tenants/active/{tenant_id}`
- **Description**: Sets the specified tenant as the active organization for subsequent operations
- **Parameters**:
  - `tenant_id`: ID of the Xero organization to set as active
- **Authentication**: Requires valid Xero OAuth token
- **Response**:

  ```json
  {
    "status": "success",
    "message": "Active tenant set successfully",
    "tenant": {
      "tenantId": "xxx-xxx-xxx",
      "tenantName": "My Company Ltd"
    }
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "Invalid tenant ID or tenant not accessible"
  }
  ```

### Get Active Tenant

- **Endpoint**: `GET /api/v1/xero/tenants/active`
- **Description**: Retrieves information about the currently active Xero tenant
- **Authentication**: Requires valid Xero OAuth token
- **Response**:

  ```json
  {
    "tenant": {
      "tenantId": "xxx-xxx-xxx",
      "tenantName": "My Company Ltd",
      "tenantType": "ORGANISATION",
      "lastAccessed": "2024-12-14T02:16:40+08:00"
    }
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "No active tenant set"
  }
  ```

### Important Notes on Tenant Management

1. You must authenticate with Xero before accessing any tenant endpoints
2. An active tenant must be set before performing operations that require a specific organization context
3. Use the "List All Tenants" endpoint to retrieve a list of available tenants then use the "Set Active Tenant" endpoint to select a specific tenant by copying a tenant ID and pasting it into the `tenant_id` Path Variables
4. The active tenant selection persists across sessions until explicitly changed or cleared
5. If your token expires, you'll need to refresh it to continue accessing tenant information

## Contacts Management

The contacts endpoints allow you to retrieve information about contacts (customers, suppliers, etc.) in your Xero organization.

### List All Contacts

- **Endpoint**: `GET /api/v1/xero/contacts`
- **Description**: Retrieves a list of all contacts for the current tenant
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "Contacts": [
      {
        "ContactID": "xxx-xxx-xxx",
        "ContactStatus": "ACTIVE",
        "Name": "ABC Company Ltd",
        "FirstName": "John",
        "LastName": "Smith",
        "EmailAddress": "john.smith@abccompany.com",
        "ContactPersons": [
          {
            "FirstName": "Jane",
            "LastName": "Doe",
            "EmailAddress": "jane.doe@abccompany.com",
            "IncludeInEmails": true
          }
        ],
        "BankAccountDetails": "12-3456-7890123-00",
        "Addresses": [
          {
            "AddressType": "STREET",
            "AddressLine1": "123 Business Street",
            "City": "Wellington",
            "PostalCode": "6011",
            "Country": "New Zealand"
          }
        ],
        "Phones": [
          {
            "PhoneType": "DEFAULT",
            "PhoneNumber": "+64 4 123 4567"
          }
        ],
        "UpdatedDateUTC": "2024-12-14T03:05:28.000Z",
        "IsCustomer": true,
        "IsSupplier": false
      }
    ]
  }
  ```

- **Error Responses**:
  - When no tenant is set:

    ```json
    {
      "detail": "No organisation tenant found"
    }
    ```

  - When an error occurs:

    ```json
    {
      "detail": "Internal Server Error"
    }
    ```

### Get Contact by ID

- **Endpoint**: `GET /api/v1/xero/contacts/{contact_id}`
- **Description**: Retrieves details of a specific contact by their ID
- **Parameters**:
  - `contact_id`: The unique identifier of the contact
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "status": "success",
    "contact": {
      "ContactID": "xxx-xxx-xxx",
      "ContactStatus": "ACTIVE",
      "Name": "ABC Company Ltd",
      "FirstName": "John",
      "LastName": "Smith",
      "EmailAddress": "john.smith@abccompany.com",
      "ContactPersons": [
        {
          "FirstName": "Jane",
          "LastName": "Doe",
          "EmailAddress": "jane.doe@abccompany.com",
          "IncludeInEmails": true
        }
      ],
      "BankAccountDetails": "12-3456-7890123-00",
      "Addresses": [
        {
          "AddressType": "STREET",
          "AddressLine1": "123 Business Street",
          "City": "Wellington",
          "PostalCode": "6011",
          "Country": "New Zealand"
        }
      ],
      "Phones": [
        {
          "PhoneType": "DEFAULT",
          "PhoneNumber": "+64 4 123 4567"
        }
      ],
      "UpdatedDateUTC": "2024-12-14T03:05:28.000Z",
      "IsCustomer": true,
      "IsSupplier": false
    }
  }
  ```

- **Error Responses**:
  - When no tenant is set:

    ```json
    {
      "detail": "No tenant selected. Please select a tenant first."
    }
    ```

  - When contact is not found or other error:

    ```json
    {
      "detail": "Error message from Xero API"
    }
    ```

### Important Notes on Contacts

1. An active tenant must be set before accessing any contacts endpoints
2. Contacts can be either customers, suppliers, or both
3. Contact information includes:
   - Basic details (name, email)
   - Contact persons (additional contacts within the organization)
   - Bank account details (if provided)
   - Addresses (street, postal)
   - Phone numbers
   - Customer/Supplier status
4. All dates are in UTC format
5. Contact IDs should be stored and used consistently across your application
6. Use the List All Contacts endpoint to retrieve contact IDs before using the Get Contact by ID endpoint

## Invoice Management

The invoice endpoints allow you to manage and interact with invoices in your Xero organization.

### List All Invoices

- **Endpoint**: `GET /api/v1/xero/invoices`
- **Description**: Retrieves a list of all invoices for the current tenant
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "Invoices": [
      {
        "Type": "ACCREC",
        "InvoiceID": "xxx-xxx-xxx",
        "InvoiceNumber": "INV-001",
        "Reference": "REF001",
        "Date": "2024-12-14",
        "DueDate": "2024-12-28",
        "Status": "AUTHORISED",
        "LineAmountTypes": "Exclusive",
        "Contact": {
          "ContactID": "yyy-yyy-yyy",
          "Name": "ABC Company Ltd"
        },
        "LineItems": [
          {
            "Description": "Sample Item",
            "Quantity": 1.0,
            "UnitAmount": 100.00,
            "AccountCode": "200",
            "TaxType": "OUTPUT",
            "TaxAmount": 15.00,
            "LineAmount": 100.00
          }
        ],
        "SubTotal": 100.00,
        "TotalTax": 15.00,
        "Total": 115.00,
        "UpdatedDateUTC": "2024-12-14T03:09:48.000Z",
        "CurrencyCode": "NZD"
      }
    ]
  }
  ```

- **Error Responses**:
  - When no tenant is set:

    ```json
    {
      "detail": "No organisation tenant found"
    }
    ```

  - When an error occurs:

    ```json
    {
      "detail": "Failed to fetch invoices"
    }
    ```

### Get Invoice by ID

- **Endpoint**: `GET /api/v1/xero/invoices/{invoice_id}`
- **Description**: Retrieves details of a specific invoice by its ID
- **Parameters**:
  - `invoice_id`: The unique identifier of the invoice
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "status": "success",
    "invoice": {
      "Type": "ACCREC",
      "InvoiceID": "xxx-xxx-xxx",
      "InvoiceNumber": "INV-001",
      "Reference": "REF001",
      "Date": "2024-12-14",
      "DueDate": "2024-12-28",
      "Status": "AUTHORISED",
      "LineAmountTypes": "Exclusive",
      "Contact": {
        "ContactID": "yyy-yyy-yyy",
        "Name": "ABC Company Ltd"
      },
      "LineItems": [
        {
          "Description": "Sample Item",
          "Quantity": 1.0,
          "UnitAmount": 100.00,
          "AccountCode": "200",
          "TaxType": "OUTPUT",
          "TaxAmount": 15.00,
          "LineAmount": 100.00
        }
      ],
      "SubTotal": 100.00,
      "TotalTax": 15.00,
      "Total": 115.00,
      "UpdatedDateUTC": "2024-12-14T03:09:48.000Z",
      "CurrencyCode": "NZD"
    }
  }
  ```

- **Error Responses**:
  - When no tenant is set:

    ```json
    {
      "detail": "No tenant selected. Please select a tenant first."
    }
    ```

  - When invoice is not found or other error:

    ```json
    {
      "detail": "Error selecting invoice"
    }
    ```

### Create Invoice

- **Endpoint**: `PUT /api/v1/xero/invoices/create`
- **Description**: Creates one or more new invoices for the current tenant
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Request Body**:

  ```json
  {
    "invoices": [
      {
        "type": "ACCREC",
        "contact": {
          "contact_id": "xxx-xxx-xxx"
        },
        "line_items": [
          {
            "description": "Sample Item",
            "quantity": 1,
            "unit_amount": 100.00,
            "account_code": "200",
            "tax_type": "OUTPUT"
          }
        ],
        "date": "2024-12-14",
        "due_date": "2024-12-28",
        "invoice_number": "INV-001",
        "status": "DRAFT",
        "currency_code": "USD",
        "reference": "REF001"
      }
    ]
  }
  ```

- **Response**:

  ```json
  {
    "status": "success",
    "message": "Invoices created successfully",
    "data": {
      "Invoices": [
        {
          "InvoiceID": "xxx-xxx-xxx",
          "InvoiceNumber": "INV-001",
          "Status": "DRAFT",
          "Type": "ACCREC",
          "Total": 115.00,
          "UpdatedDateUTC": "2024-12-14T03:09:48.000Z"
        }
      ]
    }
  }
  ```

- **Error Responses**:
  - When no tenant is set:

    ```json
    {
      "detail": "No tenant selected"
    }
    ```

  - When validation fails:

    ```json
    {
      "detail": "Validation error details"
    }
    ```

### Create Invoice Attachment

- **Endpoint**: `PUT /api/v1/xero/invoices/attachment/{invoice_id}`
- **Description**: Uploads a file attachment for a specific invoice
- **Parameters**:
  - `invoice_id`: The ID of the invoice to attach the file to
- **Request Body**: Multipart form data
  - `file`: The file to upload
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "status": "success",
    "message": "Attachment uploaded successfully",
    "data": {
      "AttachmentID": "xxx-xxx-xxx",
      "FileName": "invoice.pdf",
      "Url": "https://api.xero.com/api.xro/2.0/Invoices/xxx-xxx-xxx/Attachments/invoice.pdf",
      "MimeType": "application/pdf",
      "ContentLength": 12345
    }
  }
  ```

- **Error Responses**:
  - When no file is provided:

    ```json
    {
      "detail": "Please provide a file."
    }
    ```

  - When upload fails:

    ```json
    {
      "detail": "Error uploading to Xero API: error details"
    }
    ```

### Important Notes on Invoices

1. An active tenant must be set before accessing any invoice endpoints
2. Invoice types:
   - `ACCREC`: Accounts Receivable (Sales Invoice)
   - `ACCPAY`: Accounts Payable (Bills)
3. Invoice statuses:
   - `DRAFT`: Saved but not approved
   - `SUBMITTED`: Submitted for approval
   - `AUTHORISED`: Approved and ready for sending
   - `PAID`: Fully paid
   - `VOID`: Voided invoice
4. Line items require:
   - Description
   - Quantity
   - Unit Amount
   - Account Code
   - Tax Type
5. Attachments:
   - Support common file types (PDF, images, etc.)
   - Files are stored securely in Xero
   - Each attachment requires a valid invoice ID
   - Includes idempotency key to prevent duplicate uploads

## Bank Account Management

The bank account endpoints allow you to manage and interact with bank accounts within your active Xero organization.

### List All Bank Accounts

- **Endpoint**: `GET /api/v1/xero/accounts`
- **Description**: Retrieves a list of all active bank accounts for the current tenant
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "Accounts": [
      {
        "AccountID": "xxx-xxx-xxx",
        "Code": "1001",
        "Name": "Main Trading Account",
        "Type": "BANK",
        "BankAccountNumber": "12-3456-7890123-00",
        "Status": "ACTIVE",
        "Description": "Primary business bank account",
        "CurrencyCode": "NZD"
      },
      {
        "AccountID": "yyy-yyy-yyy",
        "Code": "1002",
        "Name": "Savings Account",
        "Type": "BANK",
        "BankAccountNumber": "12-3456-7890123-01",
        "Status": "ACTIVE",
        "Description": "Business savings account",
        "CurrencyCode": "NZD"
      }
    ]
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "No active tenant found"
  }
  ```

### Set Active Bank Account

- **Endpoint**: `PUT /api/v1/xero/accounts/active/{account_id}`
- **Description**: Sets the specified bank account as active for transaction retrieval
- **Parameters**:
  - `account_id`: ID of the bank account to set as active
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "status": "success",
    "message": "Active bank account set successfully",
    "account": {
      "account_id": "xxx-xxx-xxx",
      "name": "Main Trading Account",
      "number": "12-3456-7890123-00"
    }
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "Invalid account ID or account not accessible"
  }
  ```

### Get Active Bank Account

- **Endpoint**: `GET /api/v1/xero/accounts/active`
- **Description**: Retrieves information about the currently active bank account
- **Authentication**: Requires valid Xero OAuth token
- **Response**:
  - When active account exists:

    ```json
    {
      "status": "active",
      "account_id": "xxx-xxx-xxx",
      "account_details": {
        "name": "Main Trading Account",
        "number": "12-3456-7890123-00",
        "type": "BANK",
        "currency": "NZD"
      }
    }
    ```

  - When no active tenant:

    ```json
    {
      "status": "inactive",
      "message": "No active tenant"
    }
    ```

  - When no active account:

    ```json
    {
      "status": "inactive",
      "message": "No active bank account"
    }
    ```

  - When previously active account is invalid:

    ```json
    {
      "status": "invalid",
      "message": "Previously active account is no longer valid"
    }
    ```

### Important Notes on Bank Account Management

1. An active tenant must be set before accessing any bank account endpoints
2. Only active bank accounts are returned in the list
3. Use the "Set Active Bank Account" endpoint to select a specific bank account by copying a bank account ID and pasting it into the `account_id` Path Variables
4. Bank account selection persists across sessions until explicitly changed or cleared
5. Invalid or inaccessible bank accounts will be automatically cleared from the session

## Bank Transactions

The bank transactions endpoint allows you to retrieve bank transactions from your Xero organization.

### List Bank Transactions

- **Endpoint**: `GET /api/v1/xero/bank-transactions`
- **Description**: Retrieves a list of bank transactions for the current tenant
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "BankTransactions": [
      {
        "Type": "SPEND",
        "Contact": {
          "ContactID": "xxx-xxx-xxx",
          "Name": "Vendor Name"
        },
        "BankAccount": {
          "AccountID": "yyy-yyy-yyy",
          "Code": "1001",
          "Name": "Main Trading Account"
        },
        "Date": "2024-12-14",
        "Status": "AUTHORISED",
        "LineAmountTypes": "Inclusive",
        "LineItems": [
          {
            "Description": "Office Supplies",
            "Quantity": 1.0,
            "UnitAmount": 50.00,
            "AccountCode": "400",
            "TaxType": "INPUT2",
            "TaxAmount": 7.50,
            "LineAmount": 50.00
          }
        ],
        "SubTotal": 42.50,
        "TotalTax": 7.50,
        "Total": 50.00,
        "UpdatedDateUTC": "2024-12-14T02:16:40.000Z",
        "CurrencyCode": "NZD"
      }
    ]
  }
  ```

- **Error Responses**:
  - When no tenant is set:

    ```json
    {
      "detail": "No organisation tenant found"
    }
    ```

  - When an error occurs:

    ```json
    {
      "detail": "Internal Server Error"
    }
    ```

### Important Notes on Bank Transactions

1. An active tenant must be set before accessing bank transactions
2. Bank transactions are returned in chronological order
3. The response includes both incoming (RECEIVE) and outgoing (SPEND) transactions
4. Each transaction includes:
   - Transaction type and status
   - Contact information (if available)
   - Bank account details
   - Line items with tax information
   - Total amounts (subtotal, tax, and total)
   - Currency information
5. Transaction dates are in ISO format (YYYY-MM-DD)
6. UTC timestamps are provided for transaction updates

## Organisation 

The organisation endpoint allows you to retrieve information about the current Xero organization.

### Get Current Organisation

- **Endpoint**: `GET /api/v1/xero/organisation`
- **Description**: Retrieves information about the current Xero organization
- **Authentication**: Requires valid Xero OAuth token
- **Prerequisites**: Active tenant must be set
- **Response**:

  ```json
  {
    "Organisation": {
      "OrganisationID": "xxx-xxx-xxx",
      "Name": "My Company",
      "OrganisationNumber": "123456789"
    }
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "No active tenant found"
  }
  ```

## Usage in Postman

1. **Initial Authentication**:
   - ⚠️ Do NOT use the Postman "Login" request
   - Instead, authenticate through your web browser first
   - After browser authentication, you can use other endpoints in Postman

2. **Making Authenticated Requests**:
   - Use the "Check Auth Status" request to verify your authentication
   - All requests will use the token stored during browser authentication
   - If the token expires, use the "Refresh Token" endpoint

## Testing Flow

   1. Authenticate through your web browser
   2. Use "Check Auth Status" in Postman to verify authentication
   3. Select a tenant as it is required for some Xero API requests e.g. Invoices, Accounts, Bank Transactions
   4. Make your desired Xero API requests
   5. Refresh your token if needed to continue using the Xero API
   6. Use "Logout" when finished
