# Xero OAuth Implementation Guide

This guide provides a comprehensive overview of the Xero OAuth integration implementation, detailing each component's functionality, data flow, and interactions.

## Table of Contents
- [1. Authentication Flow](#1-authentication-flow)
- [2. Token Management](#2-token-management)
- [3. Tenant Management](#3-tenant-management)
- [4. API Operations](#4-api-operations)
- [5. Error Handling](#5-error-handling)
- [6. Security Measures](#6-security-measures)
- [7. Implementation Details](#7-implementation-details)

## 1. Authentication Flow

### Initial Authentication Process
1. **User Initiates Login** (`GET /api/v1/xero/auth/login`)
   - Function: `login()` in `auth.py`
   - Purpose: Initiates the OAuth flow with Xero
   - Process:
     1. Validates user authentication using JWT token
     2. Generates a secure state parameter using `generate_state_parameter()`
     3. Stores state with user ID in database using `store_state()`
     4. Constructs redirect URI for callback
     5. Redirects user to Xero login page

2. **Xero Authentication** (`GET /api/v1/xero/auth/callback`)
   - Function: `oauth_callback()` in `auth.py`
   - Purpose: Handles the OAuth callback from Xero
   - Process:
     1. Receives state and authorization code from Xero
     2. Validates state parameter using `validate_state()`
     3. Exchanges code for access token
     4. Stores token using `token_manager.store_token()`
     5. Creates XeroToken record in database

### Token Refresh Flow
1. **Automatic Token Refresh**
   - Function: `refresh_token()` in `token_manager.py`
   - Purpose: Maintains valid access tokens
   - Process:
     1. Detects expired token during API calls
     2. Uses refresh token to obtain new access token
     3. Updates token in database and cache
     4. Returns new token for immediate use

## 2. Token Management

### Token Manager Service
The `XeroTokenManager` class provides centralized token management:

1. **Token Retrieval** (`get_current_token()`)
   - Purpose: Get valid token for API calls
   - Process:
     1. Checks in-memory cache first
     2. Falls back to database if not in cache
     3. Validates token expiration
     4. Handles refresh if needed
     5. Updates cache with valid token

2. **Token Storage** (`store_token()`)
   - Purpose: Securely store OAuth tokens
   - Process:
     1. Creates token dictionary with expiry
     2. Stores in database using XeroToken model
     3. Updates in-memory cache
     4. Handles concurrent access

3. **Token Invalidation** (`invalidate_token()`)
   - Purpose: Remove invalid or revoked tokens
   - Process:
     1. Removes from cache
     2. Deletes from database
     3. Logs invalidation event

## 3. Tenant Management

### Tenant Discovery and Selection
1. **List Available Tenants** (`GET /api/v1/xero/tenants/`)
   - Function: `list_tenants()` in `tenants.py`
   - Purpose: Show available Xero organizations
   - Process:
     1. Validates current token
     2. Retrieves connections from Xero
     3. Gets detailed organization info
     4. Creates/updates tenant metadata
     5. Returns formatted tenant list

2. **Tenant Activation** (`POST /api/v1/xero/tenants/{tenant_id}/activate`)
   - Function: `set_active_tenant()` in `tenants.py`
   - Purpose: Select working tenant context
   - Process:
     1. Validates tenant existence
     2. Updates XeroToken with tenant ID
     3. Updates tenant metadata last active time
     4. Establishes tenant context for API calls

### Tenant Context Management
1. **Active Tenant Retrieval** (`get_active_tenant()`)
   - Purpose: Get current working context
   - Process:
     1. Checks token for tenant ID
     2. Validates tenant access
     3. Returns tenant metadata

2. **Tenant Access Validation** (`validate_tenant_access()`)
   - Purpose: Ensure proper tenant authorization
   - Process:
     1. Verifies tenant exists
     2. Checks user authorization
     3. Validates tenant status

## 4. API Operations

### API Request Flow
1. **Token Validation**
   - Function: `require_valid_token()` in `oauth.py`
   - Purpose: Ensure valid token for API calls
   - Process:
     1. Extracts token from request
     2. Validates token authenticity
     3. Checks expiration
     4. Handles refresh if needed

2. **Tenant Context Application**
   - Function: `get_tenant_context()` in `tenant_utils.py`
   - Purpose: Apply tenant context to API calls
   - Process:
     1. Gets active tenant ID
     2. Validates tenant access
     3. Applies tenant header

### Available API Operations
Each endpoint follows this pattern:
1. **Organizations** (`/api/v1/xero/organisations/`)
   - Purpose: Manage organization data
   - Operations:
     - Get organization details
     - Update organization settings

2. **Invoices** (`/api/v1/xero/invoices/`)
   - Purpose: Invoice management
   - Operations:
     - List invoices
     - Create invoice
     - Update invoice
     - Get invoice details

3. **Contacts** (`/api/v1/xero/contacts/`)
   - Purpose: Contact management
   - Operations:
     - List contacts
     - Create contact
     - Update contact
     - Get contact details

4. **Bank Transactions** (`/api/v1/xero/bank-transactions/`)
   - Purpose: Transaction management
   - Operations:
     - List transactions
     - Create transaction
     - Update transaction
     - Get transaction details

## 5. Error Handling

### Error Scenarios and Handling
1. **Token Errors**
   - Types:
     - Expired tokens
     - Invalid tokens
     - Refresh failures
   - Handling:
     - Automatic refresh attempts
     - Graceful degradation
     - User notification

2. **Tenant Errors**
   - Types:
     - Invalid tenant
     - Access denied
     - Not found
   - Handling:
     - Clear error messages
     - Proper status codes
     - Recovery options

3. **API Rate Limits**
   - Implementation: `retry_with_backoff` decorator
   - Purpose: Handle rate limiting gracefully
   - Process:
     1. Detects rate limit errors
     2. Implements exponential backoff
     3. Retries with increasing delays
     4. Logs attempts and failures

## 6. Security Measures

### Token Security
1. **Storage Security**
   - Database encryption
   - Secure token handling
   - Access control

2. **Transport Security**
   - HTTPS enforcement
   - Secure headers
   - TLS requirements

### Authentication Security
1. **State Parameter Protection**
   - Secure generation
   - Time limitation
   - One-time use
   - CSRF protection

2. **Access Control**
   - JWT validation
   - Role-based access
   - Tenant isolation
   - Session management

## 7. Implementation Details

### Database Models
1. **XeroToken Model**
   - Purpose: Store OAuth tokens
   - Fields:
     - user_id: User identifier
     - token_data: Encrypted token JSON
     - tenant_id: Active tenant
     - created_at: Creation timestamp
     - expires_at: Token expiry

2. **TenantMetadata Model**
   - Purpose: Store tenant information
   - Fields:
     - tenant_id: Tenant identifier
     - name: Organization name
     - tenant_type: Organization type
     - created_at: Creation timestamp

### Configuration
OAuth client configuration with proper security settings:
- Secure client registration
- Proper scope definition
- Metadata URL configuration
- Token endpoint setup

---
Last Updated: 2025-02-21

Note: This guide reflects the current implementation of the Xero OAuth flow in the Bank Reconciliation project. For the latest updates or changes, please refer to the source code or contact the development team.
