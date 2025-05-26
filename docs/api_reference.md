# API Reference Documentation

## Overview

This document provides a comprehensive reference for all endpoints in the Bank Reconciliation API. Each endpoint is documented with its URL, method, parameters, and expected responses.

## Table of Contents

- [Base URL](#base-url)
- [Common Headers](#common-headers)
- [Authentication Endpoints](#authentication-endpoints)
  - [Login](#login)
  - [Refresh Token](#refresh-token)
  - [Logout](#logout)
  - [Request Password Reset](#request-password-reset)
  - [Reset Password](#reset-password)
- [Xero Integration Endpoints](#xero-integration-endpoints)
  - [Authentication](#xero-authentication)
    - [Check Authentication Status](#check-authentication-status)
    - [Login to Xero](#login-to-xero)
    - [OAuth Callback](#oauth-callback)
    - [Refresh Token](#refresh-xero-token)
    - [Logout](#logout-from-xero)
  - [Tenant Management](#tenant-management)
    - [List All Tenants](#list-all-tenants)
    - [Activate Tenant](#activate-tenant)
    - [Get Active Tenant](#get-active-tenant)
  - [Bank Transactions](#bank-transactions)
    - [List Bank Transactions](#list-bank-transactions)
  - [Contacts](#contacts)
    - [List Contacts](#list-contacts)
    - [Get Contact](#get-contact)
  - [Invoices](#invoices)
    - [List Invoices](#list-invoices)
    - [Get Invoice](#get-invoice)
    - [Create Invoice Attachment](#create-invoice-attachment)
  - [Organisation](#organisation)
    - [Get Organisation](#get-organisation)
- [Error Codes](#error-codes)
- [Using the Postman Collection](#using-the-postman-collection)

## Base URL

All endpoints are prefixed with `/api/v1`

## Common Headers

| Header | Value |
|--------|-------|
| Content-Type | application/json |
| WWW-Authenticate | Bearer (for authentication errors) |
| Authorization | Bearer {access_token} (for authenticated endpoints) |

## Authentication Endpoints

### Login

**Endpoint**: `POST /login`

Authenticates a user and returns access tokens for both the app and Xero (if connected).

**Request**:
- Content-Type: application/x-www-form-urlencoded or application/json
- Body:
  ```
  username: your.email@example.com
  password: your_password
  ```

**Response Success** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "user_uuid",
  "xero": {
    "access_token": "xero_access_token",
    "refresh_token": "xero_refresh_token",
    "expires_at": "2025-02-12T02:37:33+00:00",
    "token_type": "Bearer",
    "tenant_id": "xero_tenant_id"
  }
}
```

**Response Error** (401 Unauthorized):
```json
{
  "detail": "Incorrect email or password. 4 attempts remaining"
}
```

**Notes**:
- The `xero` field will be `null` if the user hasn't connected to Xero
- `expires_at` is in ISO 8601 format and UTC timezone
- Failed login attempts are tracked and may result in account lockout
- Maximum login attempts and lockout duration are configurable system settings

### Refresh Token

**Endpoint**: `POST /refresh`

Refresh an expired access token using a valid refresh token.

**Request**:
```json
{
  "token": "your_refresh_token"
}
```

**Response Success** (200 OK):
```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer"
}
```

**Response Error** (401 Unauthorized):
```json
{
  "detail": "Invalid refresh token"
}
```

**Notes**:
- Both access and refresh tokens are updated
- The old refresh token is invalidated
- Use the new tokens for subsequent requests

### Logout

**Endpoint**: `POST /logout`

Logs out a user by blacklisting the current token and removing refresh tokens.

**Request**:
- Authorization: Bearer token required (either in header or cookie)
- No body required

**Response Success** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

**Response Error** (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

**Notes**:
- After logout, the blacklisted token cannot be reused even if it hasn't expired
- All cookies (`access_token`, `refresh_token`, `xero_oauth_state`, `xero_token`) are cleared
- Subsequent requests with the same token will return 401 Unauthorized

### Request Password Reset

**Endpoint**: `POST /request-password-reset`

Initiates the password reset process by sending a reset link to the user's email.

**Request**:
```json
{
  "email": "user@example.com"
}
```

**Response Success** (200 OK):
```json
{
  "message": "If your email is registered, you will receive a password reset link shortly"
}
```

**Notes**:
- For security reasons, the response is the same whether the email exists or not
- Reset tokens expire after 24 hours
- Email contains a link to the password reset page with a secure token

### Reset Password

**Endpoint**: `POST /reset-password`

Completes the password reset process using the token received via email.

**Request**:
```json
{
  "token": "reset_token_from_email",
  "new_password": "new_secure_password"
}
```

**Response Success** (200 OK):
```json
{
  "message": "Password has been reset successfully"
}
```

**Response Error** (400 Bad Request):
```json
{
  "detail": "Invalid or expired token"
}
```

**Notes**:
- Token is single-use and expires after 24 hours
- Password must meet security requirements
- All existing tokens for the user are invalidated after password reset
- User will need to login again with the new password

## Xero Integration Endpoints

### Xero Authentication

#### Check Authentication Status

**Endpoint**: `GET /xero/auth/`

Checks the current Xero authentication status.

**Request**:
- Authorization: Bearer token required

**Response** (when not authenticated):
```json
{
  "status": "unauthenticated",
  "message": "No active session found",
  "redirect_url": "/api/v1/xero/auth/login"
}
```

**Response** (when token is expired):
```json
{
  "status": "expired",
  "message": "Session has expired",
  "redirect_url": "/api/v1/xero/auth/login"
}
```

**Response** (when authenticated):
```json
{
  "status": "authenticated",
  "message": "Successfully authenticated with Xero",
  "token_type": "Bearer",
  "expires_at": "2024-12-13T23:43:25",
  "scopes": ["offline_access", "accounting.transactions", "accounting.contacts"]
}
```

#### Login to Xero

**Endpoint**: `GET /xero/auth/login`

Initiates the OAuth2 login flow with Xero.

**Request**:
- Authorization: Bearer token required

**Response**:
```json
{
  "auth_url": "https://login.xero.com/identity/connect/authorize?..."
}
```

**Notes**:
- This endpoint returns a URL that must be opened in a browser
- You cannot complete the OAuth flow directly in Postman
- The user will be redirected to Xero for authentication

#### OAuth Callback

**Endpoint**: `GET /xero/auth/callback`

Callback endpoint for Xero OAuth2 flow.

**Request Parameters**:
- `code`: Authorization code from Xero
- `state`: State parameter for CSRF protection

**Response Success**:
```json
{
  "status": "success",
  "message": "Successfully authenticated with Xero",
  "redirect_url": "/dashboard"
}
```

**Response Error**:
```json
{
  "status": "error",
  "message": "Failed to authenticate with Xero",
  "redirect_url": "/api/v1/xero/auth/login"
}
```

**Notes**:
- This endpoint is called automatically by Xero after user authentication
- It should not be called directly in Postman

#### Refresh Xero Token

**Endpoint**: `POST /xero/auth/refresh`

Refreshes the Xero OAuth token if it's expired.

**Request**:
- Authorization: Bearer token required

**Response Success**:
```json
{
  "status": "success",
  "message": "Token refreshed successfully",
  "token": {
    "access_token": "new_xero_access_token",
    "expires_at": "2025-02-12T03:37:33+00:00",
    "token_type": "Bearer"
  }
}
```

**Response Re-auth Required**:
```json
{
  "status": "re-auth-required",
  "message": "Your Xero session has expired. Please re-authenticate.",
  "redirect_url": "/api/v1/xero/auth/login"
}
```

#### Logout from Xero

**Endpoint**: `GET /xero/auth/logout`

Logs out from Xero by clearing tokens and session data.

**Request**:
- Authorization: Bearer token required

**Response Success**:
```json
{
  "status": "success",
  "message": "Successfully logged out from Xero"
}
```

### Tenant Management

#### List All Tenants

**Endpoint**: `GET /xero/tenants`

Retrieves a list of all available Xero organizations/tenants.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required

**Response Success**:
```json
{
  "tenants": [
    {
      "id": "xxx-xxx-xxx",
      "name": "My Company Ltd",
      "short_code": "MCL",
      "table_name": "statements",
      "is_active": true
    },
    {
      "id": "yyy-yyy-yyy",
      "name": "Another Business",
      "short_code": "AB",
      "table_name": "statements",
      "is_active": false
    }
  ]
}
```

**Response Error** (when not authenticated with Xero):
```json
{
  "detail": "No valid Xero token found"
}
```

#### Activate Tenant

**Endpoint**: `POST /xero/tenants/{tenant_id}/activate`

Sets the specified tenant as active and starts scheduled processing.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Path Parameters:
  - `tenant_id`: ID of the Xero organization to set as active

**Response Success**:
```json
{
  "status": "success",
  "message": "Active tenant set successfully",
  "tenant": {
    "id": "xxx-xxx-xxx",
    "name": "My Company Ltd",
    "short_code": "MCL",
    "table_name": "statements",
    "is_active": true
  },
  "scheduled_jobs": [
    {
      "id": "job-uuid",
      "type": "bank_statement_import",
      "status": "scheduled",
      "next_run": "2025-01-01T00:00:00Z"
    }
  ]
}
```

**Response Error**:
```json
{
  "detail": "Invalid tenant ID or tenant not accessible"
}
```

#### Get Active Tenant

**Endpoint**: `GET /xero/tenants/active`

Retrieves information about the currently active Xero tenant.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required

**Response Success**:
```json
{
  "tenant": {
    "id": "xxx-xxx-xxx",
    "name": "My Company Ltd",
    "short_code": "MCL",
    "table_name": "statements",
    "is_active": true
  }
}
```

**Response Error** (when no active tenant):
```json
{
  "detail": "No active tenant found"
}
```

### Bank Transactions

#### List Bank Transactions

**Endpoint**: `GET /xero/bank-transactions`

Returns a list of bank transactions for the current tenant.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Query Parameters:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 50, max: 100)
  - `from_date` (optional): Filter transactions from this date (format: YYYY-MM-DD)
  - `to_date` (optional): Filter transactions to this date (format: YYYY-MM-DD)
  - `status` (optional): Filter by status (values: AUTHORISED, DELETED)
  - `bank_account_id` (optional): Filter by bank account ID

**Response Success**:
```json
{
  "bank_transactions": [
    {
      "type": "SPEND",
      "date": "2025-01-01",
      "status": "AUTHORISED",
      "bank_transaction_id": "123-456-789",
      "bank_account": {
        "account_id": "acc-123-456",
        "code": "090",
        "name": "Business Account"
      },
      "amount": -250.00,
      "reference": "Office Supplies",
      "is_reconciled": true,
      "line_items": [
        {
          "description": "Printer Paper",
          "quantity": 5,
          "unit_amount": 50.00,
          "account_code": "400",
          "tax_type": "OUTPUT"
        }
      ]
    }
  ],
  "page": 1,
  "page_size": 50,
  "total_pages": 3,
  "total_items": 125
}
```

**Response Error** (when no active tenant):
```json
{
  "detail": "No active tenant found. Please select a tenant first."
}
```

### Contacts

#### List Contacts

**Endpoint**: `GET /xero/contacts`

Returns a list of contacts for the current tenant.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Query Parameters:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 50, max: 100)
  - `search` (optional): Search term to filter contacts
  - `contact_status` (optional): Filter by status (values: ACTIVE, ARCHIVED)
  - `include_archived` (optional): Include archived contacts (default: false)

**Response Success**:
```json
{
  "contacts": [
    {
      "contact_id": "contact-123-456",
      "name": "ABC Company",
      "contact_status": "ACTIVE",
      "contact_number": "CUS-001",
      "email_address": "accounts@abccompany.com",
      "phone_number": "+1 555-123-4567",
      "is_customer": true,
      "is_supplier": false,
      "bank_account_details": "123456-7890-123"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total_pages": 2,
  "total_items": 75
}
```

#### Get Contact

**Endpoint**: `GET /xero/contacts/{contact_id}`

Returns detailed information about a specific contact.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Path Parameters:
  - `contact_id`: ID of the contact to retrieve

**Response Success**:
```json
{
  "contact": {
    "contact_id": "contact-123-456",
    "name": "ABC Company",
    "contact_status": "ACTIVE",
    "contact_number": "CUS-001",
    "email_address": "accounts@abccompany.com",
    "phone_number": "+1 555-123-4567",
    "is_customer": true,
    "is_supplier": false,
    "bank_account_details": "123456-7890-123",
    "tax_number": "12-3456789",
    "accounts_receivable": {
      "outstanding": 1000.00,
      "overdue": 0.00
    },
    "accounts_payable": {
      "outstanding": 0.00,
      "overdue": 0.00
    },
    "addresses": [
      {
        "address_type": "STREET",
        "address_line1": "123 Business St",
        "city": "Business City",
        "postal_code": "12345",
        "country": "United States"
      }
    ],
    "contact_persons": [
      {
        "first_name": "John",
        "last_name": "Smith",
        "email_address": "john.smith@abccompany.com",
        "is_primary": true
      }
    ]
  }
}
```

### Invoices

#### List Invoices

**Endpoint**: `GET /xero/invoices`

Returns a list of invoices for the current tenant.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Query Parameters:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 50, max: 100)
  - `from_date` (optional): Filter invoices from this date (format: YYYY-MM-DD)
  - `to_date` (optional): Filter invoices to this date (format: YYYY-MM-DD)
  - `status` (optional): Filter by status (values: DRAFT, SUBMITTED, AUTHORISED, PAID)
  - `contact_id` (optional): Filter by contact ID
  - `invoice_number` (optional): Filter by invoice number

**Response Success**:
```json
{
  "invoices": [
    {
      "invoice_id": "inv-123-456",
      "invoice_number": "INV-001",
      "reference": "PO-12345",
      "type": "ACCREC",
      "status": "AUTHORISED",
      "contact": {
        "contact_id": "contact-123-456",
        "name": "ABC Company"
      },
      "date": "2025-01-01",
      "due_date": "2025-01-31",
      "total": 1000.00,
      "amount_due": 1000.00,
      "amount_paid": 0.00,
      "currency_code": "USD",
      "url": "https://go.xero.com/Account/View.aspx?InvoiceID=inv-123-456",
      "has_attachments": false
    }
  ],
  "page": 1,
  "page_size": 50,
  "total_pages": 5,
  "total_items": 230
}
```

#### Get Invoice

**Endpoint**: `GET /xero/invoices/{invoice_id}`

Returns detailed information about a specific invoice.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Path Parameters:
  - `invoice_id`: ID of the invoice to retrieve

**Response Success**:
```json
{
  "invoice": {
    "invoice_id": "inv-123-456",
    "invoice_number": "INV-001",
    "reference": "PO-12345",
    "type": "ACCREC",
    "status": "AUTHORISED",
    "contact": {
      "contact_id": "contact-123-456",
      "name": "ABC Company",
      "email_address": "accounts@abccompany.com"
    },
    "date": "2025-01-01",
    "due_date": "2025-01-31",
    "total": 1000.00,
    "amount_due": 1000.00,
    "amount_paid": 0.00,
    "currency_code": "USD",
    "fully_paid_on_date": null,
    "url": "https://go.xero.com/Account/View.aspx?InvoiceID=inv-123-456",
    "has_attachments": false,
    "line_items": [
      {
        "description": "Web Development Services",
        "quantity": 10,
        "unit_amount": 100.00,
        "account_code": "200",
        "tax_type": "OUTPUT",
        "line_amount": 1000.00
      }
    ],
    "payments": []
  }
}
```

#### Create Invoice Attachment

**Endpoint**: `PUT /xero/invoices/{invoice_id}/attachments`

Uploads a file attachment to a specific invoice.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Path Parameters:
  - `invoice_id`: ID of the invoice to attach file to
- Request Body: Form data with file
  - `file`: The file to upload
  - `filename` (optional): Custom filename for the attachment

**Response Success**:
```json
{
  "status": "success",
  "message": "File attached successfully",
  "attachment": {
    "attachment_id": "att-123-456",
    "filename": "invoice-document.pdf",
    "mime_type": "application/pdf",
    "size": 256000,
    "url": "https://api.xero.com/attachments/invoice/inv-123-456/att-123-456"
  }
}
```

### Organisation

#### Get Organisation

**Endpoint**: `GET /xero/organisations`

Returns information about the current organization.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required

**Response Success**:
```json
{
  "organisations": [
    {
      "organisation_id": "org-123-456",
      "name": "My Company Ltd",
      "short_code": "MCL",
      "version": "STANDARD",
      "organisation_type": "COMPANY",
      "base_currency": "USD",
      "timezone": "American/Los_Angeles",
      "organisation_status": "ACTIVE",
      "financial_year_end_day": 31,
      "financial_year_end_month": 12,
      "sales_tax_basis": "ACCRUAL",
      "sales_tax_period": "MONTHLY",
      "registration_number": "12-3456789",
      "employer_id": "EMP-12345",
      "tax_number": "123-45-6789"
    }
  ]
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input or parameters |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Authenticated but not authorized |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid request format |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Something went wrong on the server |

## Using the Postman Collection

For testing the API, use the included Postman collection:

1. Import the `Bank_Reconciliation_API.postman_collection.json` file into Postman
2. Create a new Environment in Postman with the following variables:
   - `baseUrl`: Set to your API base URL (e.g., `http://localhost:8000`)
   - `accessToken`: Leave initial value empty
   - `refreshToken`: Leave initial value empty
   - `xeroAccessToken`: Leave initial value empty
   - `xeroTenantId`: Leave initial value empty
3. The collection includes pre-configured requests for all authentication endpoints
4. Automated scripts set environment variables after successful authentication

### Important Notes

- **Xero Authentication**: You must complete the OAuth flow in a browser first
- **Tenant Selection**: You must select an active tenant before using tenant-specific endpoints
- **Token Refresh**: Monitor token expiration and refresh as needed
- **Error Handling**: Implement proper error handling in your client application