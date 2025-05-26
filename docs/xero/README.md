# Xero Integration

## Overview

This document provides a comprehensive guide to the Xero integration in the Bank Reconciliation application. The integration enables secure OAuth2 authentication with Xero, tenant management, and access to Xero's accounting data for bank reconciliation purposes.

## Table of Contents

- [Base URL](#base-url)
- [Authentication Flow](#authentication-flow)
  - [Initial Authentication](#initial-authentication)
  - [Token Management](#token-management)
  - [Callback and State Validation](#callback-and-state-validation)
- [Authentication Endpoints](#authentication-endpoints)
  - [Check Authentication Status](#check-authentication-status)
  - [Login to Xero](#login-to-xero)
  - [OAuth Callback](#oauth-callback)
  - [Refresh Token](#refresh-token)
  - [Logout](#logout)
- [Tenant Management](#tenant-management)
  - [List All Tenants](#list-all-tenants)
  - [Activate Tenant](#activate-tenant)
  - [Get Active Tenant](#get-active-tenant)
- [Bank Transactions](#bank-transactions)
  - [List Bank Transactions](#list-bank-transactions)
- [Contact Management](#contact-management)
  - [List Contacts](#list-contacts)
  - [Get Contact](#get-contact)
- [Invoice Management](#invoice-management)
  - [List Invoices](#list-invoices)
  - [Get Invoice](#get-invoice)
  - [Create Invoice Attachment](#create-invoice-attachment)
- [Organisation Management](#organisation-management)
  - [Get Organisation](#get-organisation)
- [Implementation Details](#implementation-details)
  - [Security Measures](#security-measures)
  - [Error Handling](#error-handling)
  - [Rate Limiting](#rate-limiting)
- [Frontend Integration Guide](#frontend-integration-guide)

## Base URL

All endpoints are prefixed with `/api/v1`

## Authentication Flow

### Initial Authentication

Due to Xero's OAuth2 requirements, the authentication process must be initiated through a web browser. You cannot complete the OAuth flow directly in Postman.

**Authentication Steps:**

1. Open your browser and navigate to your local development server's login URL:

   ```plaintext
   http://localhost:8000/api/v1/xero/auth/login
   ```

2. Complete the Xero authentication process in the browser
3. After successful authentication, you'll be redirected back to your application
4. The tokens will be stored in your application's session/storage
5. You can then use these tokens for subsequent API requests in Postman

### Token Management

Tokens are managed through the `XeroTokenManager` service:

1. **Token Storage**
   - Tokens are encrypted before database storage
   - User-specific tokens ensure proper isolation
   - Token includes access token, refresh token, expiry time, and scopes

2. **Token Refresh**
   - Automatic token refresh when expired
   - Refresh tokens have a 60-day validity
   - Failed refreshes trigger re-authentication flow

3. **Token Validation**
   - Tokens are validated before each API call
   - Invalid tokens trigger appropriate error responses
   - Expiry times are checked and refreshes initiated as needed

### Callback and State Validation

To prevent CSRF attacks, the OAuth flow uses state validation:

1. **State Generation** - A cryptographically secure random state parameter is generated
2. **State Storage** - State is stored with user ID and timestamp
3. **State Validation** - Callback verifies the state parameter matches stored state
4. **Timeout** - States expire after a configurable period (default: 10 minutes)

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

### Login to Xero

- **Endpoint**: `GET /api/v1/xero/auth/login`
- **Description**: Initiates the OAuth2 login flow with Xero
- **Note**: This endpoint must be accessed through a web browser, not Postman
- **Response**: Returns a JSON with auth URL for redirection

### OAuth Callback

- **Endpoint**: `GET /api/v1/xero/auth/callback`
- **Description**: Callback endpoint for Xero OAuth2 flow
- **Note**: This is handled automatically after browser authentication
- **Response**: Handles the OAuth token response and stores the credentials
- **Success Response**:

  ```json
  {
    "status": "success",
    "message": "Successfully authenticated with Xero",
    "redirect_url": "/dashboard"
  }
  ```

- **Error Response**:

  ```json
  {
    "status": "error",
    "message": "Failed to authenticate with Xero",
    "redirect_url": "/api/v1/xero/auth/login"
  }
  ```

### Refresh Token

- **Endpoint**: `POST /api/v1/xero/auth/refresh`
- **Description**: Refreshes the Xero OAuth token if it's expired
- **Authentication**: Requires valid app token
- **Response Success**:

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

- **Response Re-auth Required**:

  ```json
  {
    "status": "re-auth-required",
    "message": "Your Xero session has expired. Please re-authenticate.",
    "redirect_url": "/api/v1/xero/auth/login"
  }
  ```

### Logout

- **Endpoint**: `GET /api/v1/xero/auth/logout`
- **Description**: Logs out from Xero by clearing tokens and session data
- **Authentication**: Requires valid app token
- **Response**:

  ```json
  {
    "status": "success",
    "message": "Successfully logged out from Xero"
  }
  ```

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

### Activate Tenant

- **Endpoint**: `POST /api/v1/xero/tenants/{tenant_id}/activate`
- **Description**: Sets the specified tenant as active and starts scheduled processing
- **Parameters**:
  - `tenant_id`: ID of the Xero organization to set as active
- **Authentication**: Requires valid Xero OAuth token
- **Response**:

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
      "id": "xxx-xxx-xxx",
      "name": "My Company Ltd",
      "short_code": "MCL",
      "table_name": "statements",
      "is_active": true
    }
  }
  ```

- **Error Response** (when no active tenant):

  ```json
  {
    "detail": "No active tenant found"
  }
  ```

## Bank Transactions

### List Bank Transactions

- **Endpoint**: `GET /api/v1/xero/bank-transactions`
- **Description**: Returns a list of bank transactions for the current tenant
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Query Parameters**:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 50, max: 100)
  - `from_date` (optional): Filter transactions from this date (format: YYYY-MM-DD)
  - `to_date` (optional): Filter transactions to this date (format: YYYY-MM-DD)
  - `status` (optional): Filter by status (values: AUTHORISED, DELETED)
  - `bank_account_id` (optional): Filter by bank account ID

- **Response**:

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

- **Error Responses**:
  - When no active tenant is set:

    ```json
    {
      "detail": "No active tenant found. Please select a tenant first."
    }
    ```

  - When API request fails:

    ```json
    {
      "detail": "Failed to fetch bank transactions"
    }
    ```

## Contact Management

### List Contacts

- **Endpoint**: `GET /api/v1/xero/contacts`
- **Description**: Returns a list of contacts for the current tenant
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Query Parameters**:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 50, max: 100)
  - `search` (optional): Search term to filter contacts
  - `contact_status` (optional): Filter by status (values: ACTIVE, ARCHIVED)
  - `include_archived` (optional): Include archived contacts (default: false)

- **Response**:

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
        "bank_account_details": "123456-7890-123",
        "addresses": [
          {
            "address_type": "STREET",
            "address_line1": "123 Business St",
            "city": "Business City",
            "postal_code": "12345",
            "country": "United States"
          }
        ]
      }
    ],
    "page": 1,
    "page_size": 50,
    "total_pages": 2,
    "total_items": 75
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "No active tenant found. Please select a tenant first."
  }
  ```

### Get Contact

- **Endpoint**: `GET /api/v1/xero/contacts/{contact_id}`
- **Description**: Returns detailed information about a specific contact
- **Parameters**:
  - `contact_id`: ID of the contact to retrieve
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Response**:

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
        },
        {
          "address_type": "POBOX",
          "address_line1": "PO Box 456",
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

- **Error Response**:

  ```json
  {
    "detail": "Contact not found"
  }
  ```

## Invoice Management

### List Invoices

- **Endpoint**: `GET /api/v1/xero/invoices`
- **Description**: Returns a list of invoices for the current tenant
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Query Parameters**:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 50, max: 100)
  - `from_date` (optional): Filter invoices from this date (format: YYYY-MM-DD)
  - `to_date` (optional): Filter invoices to this date (format: YYYY-MM-DD)
  - `status` (optional): Filter by status (values: DRAFT, SUBMITTED, AUTHORISED, PAID)
  - `contact_id` (optional): Filter by contact ID
  - `invoice_number` (optional): Filter by invoice number

- **Response**:

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

- **Error Response**:

  ```json
  {
    "detail": "No active tenant found. Please select a tenant first."
  }
  ```

### Get Invoice

- **Endpoint**: `GET /api/v1/xero/invoices/{invoice_id}`
- **Description**: Returns detailed information about a specific invoice
- **Parameters**:
  - `invoice_id`: ID of the invoice to retrieve
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Response**:

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

- **Error Response**:

  ```json
  {
    "detail": "Invoice not found"
  }
  ```

### Create Invoice Attachment

- **Endpoint**: `PUT /api/v1/xero/invoices/{invoice_id}/attachments`
- **Description**: Uploads a file attachment to a specific invoice
- **Parameters**:
  - `invoice_id`: ID of the invoice to attach file to
- **Request Body**: Form data with file
  - `file`: The file to upload
  - `filename` (optional): Custom filename for the attachment
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Response**:

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

- **Error Response**:

  ```json
  {
    "detail": "Failed to attach file. File size exceeds 3MB limit."
  }
  ```

## Organisation Management

### Get Organisation

- **Endpoint**: `GET /api/v1/xero/organisations`
- **Description**: Returns information about the current organization
- **Authentication**: Requires valid Xero OAuth token and active tenant
- **Response**:

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
        "tax_number": "123-45-6789",
        "addresses": [
          {
            "address_type": "STREET",
            "address_line1": "123 Business St",
            "city": "Business City",
            "postal_code": "12345",
            "country": "United States"
          }
        ],
        "phones": [
          {
            "phone_type": "OFFICE",
            "phone_number": "+1 555-123-4567"
          }
        ],
        "externalLinks": [
          {
            "link_type": "Website",
            "url": "https://www.mycompany.com"
          }
        ]
      }
    ]
  }
  ```

- **Error Response**:

  ```json
  {
    "detail": "No active tenant found. Please select a tenant first."
  }
  ```

## Implementation Details

### Security Measures

1. **Token Encryption** - All Xero tokens are encrypted before storage
2. **State Validation** - CSRF protection through state parameter validation
3. **Tenant Isolation** - Strong data isolation between tenants
4. **Secure Token Refresh** - Automatic and secure token refresh process
5. **Authorization Validation** - All endpoints validate proper authorization
6. **Token Revocation** - Proper token revocation on logout or disconnection

### Error Handling

1. **Token Errors**
   - Expired tokens trigger automatic refresh
   - Invalid tokens return clear error messages
   - Refresh failures redirect to re-authentication

2. **API Errors**
   - Rate limit errors are handled with backoff
   - Transient API errors use retry with exponential backoff
   - Permanent errors return appropriate status codes

3. **Authentication Errors**
   - Clear error messages guide users to proper authentication
   - State validation errors protect against CSRF attacks
   - Callback errors handled gracefully

### Rate Limiting

1. **Retry with Backoff**
   - Exponential backoff for rate limited requests
   - Configurable retry counts and delays
   - Proper logging of rate limit events

2. **API Quotas**
   - Monitoring of API quota usage
   - Rate limiting for high-volume operations
   - Daily quota management

## Frontend Integration Guide

### Authentication Flow Implementation

```javascript
// 1. Check Xero authentication status
async function checkXeroAuth() {
  const response = await fetch('/api/v1/xero/auth/');
  const data = await response.json();
  
  if (data.status === 'authenticated') {
    // User is authenticated with Xero
    console.log('Authenticated until', data.expires_at);
    return true;
  } else {
    // User needs to authenticate with Xero
    window.location.href = data.redirect_url;
    return false;
  }
}

// 2. Handle token refresh
async function refreshXeroToken() {
  const response = await fetch('/api/v1/xero/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  if (data.status === 're-auth-required') {
    // Token refresh failed, redirect to authentication
    window.location.href = data.redirect_url;
    return false;
  }
  
  return true;
}

// 3. List available tenants
async function listTenants() {
  const response = await fetch('/api/v1/xero/tenants');
  const data = await response.json();
  return data.tenants;
}

// 4. Set active tenant
async function setActiveTenant(tenantId) {
  const response = await fetch(`/api/v1/xero/tenants/${tenantId}/activate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
}
```

### Important Integration Notes

1. Always check authentication status before Xero API operations
2. Handle token refresh gracefully, redirecting when needed
3. Ensure an active tenant is selected before tenant-specific operations
4. Check for error status codes and handle appropriately
5. Implement proper error handling and user feedback
6. Consider token expiration in long-running operations