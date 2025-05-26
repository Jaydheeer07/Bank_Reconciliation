# Authentication Documentation

## Overview

This document provides a comprehensive guide to the authentication system used in the Bank Reconciliation application. The system handles both app-level authentication and Xero integration authentication.

## Table of Contents

- [App Authentication](#app-authentication)
  - [Authentication Flow](#authentication-flow)
  - [Security Measures](#security-measures)
  - [Token Management](#token-management)
  - [Error Handling](#error-handling)
- [Database Authentication](#database-authentication)
- [Implementation Details](#implementation-details)

## App Authentication

### Authentication Flow

1. **User Login**
   - User provides email and password
   - System validates credentials
   - If valid, system provides access token, refresh token, and Xero tokens (if connected)
   - Security measures: Failed login attempts tracking, account lockout, token expiration

2. **Token Usage**
   - Access token used for API requests
   - Refresh token used to obtain new access token when expired
   - App and Xero tokens managed separately

3. **User Logout**
   - Current access token blacklisted
   - Refresh tokens removed
   - Authentication cookies cleared

### Security Measures

1. **Password Security**
   - Passwords stored as hashed values (not plain text)
   - Strong password requirements:
     - Minimum 8 characters
     - Must contain letters
     - Must contain numbers
     - Must contain special characters (@$!%*#?&)

2. **Account Protection**
   - Failed login attempts tracked
   - Account locked after configurable number of failed attempts
   - Automatic unlock after cooldown period

3. **Token Security**
   - Access tokens expire after 30 minutes
   - Refresh tokens managed securely
   - Blacklisting of revoked tokens
   - Secure cookie storage with HTTP-only flag

### Token Management

1. **Access Tokens**
   - JWT format with user identity and expiration
   - Short-lived (30 minutes by default)
   - Stateless validation

2. **Refresh Tokens**
   - Stored in database with user association
   - Used to obtain new access tokens
   - Longer-lived but can be revoked
   - One refresh token per user session

3. **Token Refresh Process**
   - Client detects expired access token
   - Client requests new token with refresh token
   - System validates refresh token and issues new tokens
   - Invalid refresh tokens are rejected

### Error Handling

1. **Common Authentication Errors**
   - Invalid credentials: Clear error messages with remaining attempts
   - Expired tokens: Proper HTTP 401 responses with WWW-Authenticate header
   - Account lockout: Informative messages with unlock time
   - Token validation failures: Secure error messages avoiding information leakage

2. **Security Considerations**
   - Error messages designed to prevent username enumeration
   - Generalized error messages for security
   - Rate limiting on authentication endpoints to prevent brute force attacks

## Database Authentication

This application supports Azure Identity for secure database authentication. While currently not actively used, the infrastructure is in place to leverage Azure's managed identity and Key Vault services for credential management.

### Implementation Details

- The `DefaultAzureCredential` from the `azure-identity` package is integrated for potential Azure resource access
- This approach allows for credential-free authentication when deployed to Azure
- Local development can utilize environment variables or service principal authentication

### Future Enhancements

- Store connection strings and secrets in Azure Key Vault
- Implement managed identity authentication for Azure SQL/PostgreSQL
- Configure role-based access control through Azure AD

## Implementation Details

### Code Structure

- **Security Module**: Core security functions in `app/core/security.py`
- **Auth Dependencies**: Authentication dependencies in `app/core/deps.py`
- **Authentication Routes**: Endpoints in `app/routes/user_account/login.py`
- **Database Models**: User and token models in `app/models/database/schema_models.py`

### Authentication Middleware

Our application uses FastAPI's dependency injection system for authentication:

```python
from fastapi import Depends
from app.core.deps import get_current_user
from app.models.database.schema_models import User

@router.get("/protected-endpoint")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    # Only authenticated users can access this endpoint
    return {"message": f"Hello, {current_user.email}!"}
```

### Password Reset Flow

1. User requests password reset via email
2. System generates secure token and sends email
3. User clicks link in email and sets new password
4. System validates token and updates password
5. All existing sessions are invalidated for security

### Unit Testing Guidance

When testing authentication components:

1. Use test fixtures for authenticated users
2. Mock token validation in unit tests
3. Test both successful and failed authentication scenarios
4. Verify token refresh and expiration behavior
5. Test account lockout after failed login attempts