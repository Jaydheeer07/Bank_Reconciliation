# Bank Reconciliation App - Authentication and Usage Guidelines

## User Flow Overview

### 1. User Registration & Login

- **Registration Requirements**
  - Valid email address
  - Strong password:
    - Minimum 8 characters
    - Must contain letters
    - Must contain numbers
    - Must contain special characters (@$!%*#?&)
  - Account verification may be required

- **Login Process**
  - Login with registered email and password
  - System provides:
    - Access token (stored in cookies)
    - Refresh token (for token renewal)
  - Security measures:
    - Access tokens expire after configured time
    - Failed login attempts are tracked
    - Temporary lockout after multiple failed attempts

### 2. Xero Connection

- **Prerequisites**
  - Must be logged into the app
  - Must have valid Xero credentials
  - Valid access token required

- **Connection Process**
  - Redirect to Xero login
  - OAuth2 authentication flow
  - Automatic token management:
    - Secure token storage
    - Automatic token refresh
    - Connection status tracking

### 3. Tenant Selection

- **After Xero Connection**
  - View list of available tenants
  - Select tenant to work with
  - System stores:
    - Selected tenant in session
    - Tenant metadata in database

- **Tenant Management**
  - Switch between tenants without reconnecting
  - Each tenant gets isolated data storage
  - Active tenant status tracking

### 4. Database Updates

- **Tenant Metadata Storage**
  - User ID (UUID)
  - Tenant ID (from Xero)
  - Tenant name
  - Table name
  - Active status
  - Timestamps (created_at, updated_at)

## Important Guidelines

### Authentication Security

1. **Token Management**
   - Keep tokens secure
   - Handle expiration gracefully
   - Use refresh tokens appropriately
   - Clear tokens on logout

2. **API Access**
   - Use secure endpoints (/api/v1/)
   - Include authentication headers
   - Validate permissions
   - Handle unauthorized access

### Error Handling

1. **Common Scenarios**
   - Xero connection loss
   - Token expiration
   - Network issues
   - Invalid permissions

2. **User Experience**
   - Clear error messages
   - Proper redirection
   - Status feedback
   - Recovery options

### Data Security

1. **Best Practices**
   - Use HTTPS for all requests
   - Secure token storage
   - Tenant data isolation
   - Regular security audits

2. **Sensitive Data**
   - Never expose tokens
   - Secure credential handling
   - Proper data encryption
   - Access logging

### Session Management

1. **Session Handling**
   - Proper login/logout
   - Token refresh cycles
   - Session timeout handling
   - Multiple device support

2. **Tenant Context**
   - Clear context on switch
   - Validate tenant access
   - Track active sessions
   - Handle concurrent access

## Protected Route Flow

``` http
Request
  ↓
Auth Middleware
  ↓
Token Validation
  ↓
User Retrieval
  ↓
Tenant Context
  ↓
Data Access
```

### Error Responses

- 401: Not authenticated
- 403: Not authorized
- 404: Resource not found
- 500: Server error

## Best Practices

1. Always verify authentication before operations
2. Keep tokens secure and refresh them properly
3. Maintain proper tenant isolation
4. Handle errors gracefully
5. Log security-relevant events
6. Regular security audits
7. Keep dependencies updated
8. Monitor API usage and limits
