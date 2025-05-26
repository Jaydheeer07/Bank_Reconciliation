# Authentication API Documentation

## API Endpoints Overview

### Base URL

All endpoints are prefixed with `/api/v1`

### Common Headers

| Header | Value |
|--------|-------|
| Content-Type | application/json |
| WWW-Authenticate | Bearer (for authentication errors) |

## Using the Postman Collection

### Setting Up

1. Import the `Bank_Reconciliation_API.postman_collection.json` file into Postman
2. Create a new Environment in Postman:
   - Click on "Environments" in the sidebar
   - Click "New"
   - Add the following variables:
     - `baseUrl`: Set to your API base URL (e.g., `http://localhost:8000`)
     - `accessToken`: Leave initial value empty
     - `refreshToken`: Leave initial value empty
     - `xeroAccessToken`: Leave initial value empty
     - `xeroTenantId`: Leave initial value empty

## Authentication Flow

### 1. User Login

**Endpoint**: POST `{{baseUrl}}/api/v1/login`

Authenticates a user and returns access tokens for both the app and Xero (if connected).

**Request**:
- Content-Type: application/x-www-form-urlencoded
- Body:
  ```
  username: your.email@example.com
  password: your_password
  ```

**Response**:
```json
{
  "access_token": "app_access_token",
  "refresh_token": "app_refresh_token",
  "token_type": "bearer",
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

Notes:
- The `xero` field will be `null` if the user hasn't connected to Xero
- `expires_at` is in ISO 8601 format and UTC timezone

### 2. User Logout

**Endpoint**: POST `{{baseUrl}}/api/v1/logout`

Logs out a user by:
1. Blacklisting the current access token
2. Removing all refresh tokens
3. Clearing authentication cookies

**Request**:
- Authorization: Bearer token required (either in header or cookie)
- No body required

**Response Success**:
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

Notes:
- After logout, the blacklisted token cannot be reused even if it hasn't expired
- All cookies (`access_token`, `refresh_token`, `xero_oauth_state`, `xero_token`) are cleared
- Subsequent requests with the same token will return 401 Unauthorized

### 3. Xero Authentication

#### First-time Connection
If `xero` is `null` in the login response, redirect the user to connect with Xero:

1. GET `{{baseUrl}}/api/v1/xero/auth/login`
2. User completes Xero OAuth flow
3. Tokens are stored and user is redirected back

#### Token Refresh
When making Xero API calls, check if the token needs refresh:

1. Compare current time with `expires_at` from Xero token
2. If token is close to expiring (e.g., within 5 minutes):
   - POST `{{baseUrl}}/api/v1/xero/auth/refresh`
   
**Refresh Response Success**:
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

**Refresh Response Re-auth Required**:
```json
{
  "status": "re-auth-required",
  "message": "Your Xero session has expired. Please re-authenticate.",
  "redirect_url": "/api/v1/xero/auth/login"
}
```

### 4. App Token Refresh

**Endpoint**: POST `{{baseUrl}}/api/v1/refresh`

Use this to refresh the app's access token (not Xero tokens).

**Request**:
```json
{
  "token": "{{refreshToken}}"
}
```

**Response**:
```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer"
}
```

## Frontend Implementation Guide

### Managing Xero Integration

```typescript
// Check if Xero token needs refresh
function isXeroTokenExpiring(expiresAt: string): boolean {
  const expiryTime = new Date(expiresAt);
  const fiveMinutesFromNow = new Date(Date.now() + 5 * 60 * 1000);
  return expiryTime <= fiveMinutesFromNow;
}

// Handle Xero API calls
async function makeXeroApiCall() {
  const xeroData = getCurrentXeroData(); // from login response
  
  if (!xeroData) {
    // Not connected to Xero
    window.location.href = '/api/v1/xero/auth/login';
    return;
  }
  
  if (isXeroTokenExpiring(xeroData.expires_at)) {
    try {
      const response = await fetch('/api/v1/xero/auth/refresh');
      const data = await response.json();
      
      if (response.status === 200) {
        // Update stored tokens
        updateStoredXeroData(data.token);
      } else if (data.status === 're-auth-required') {
        // Token expired, need to reconnect
        window.location.href = data.redirect_url;
        return;
      }
    } catch (error) {
      console.error('Error refreshing Xero token:', error);
      return;
    }
  }
  
  // Make Xero API call with valid token
  // ...
}

## Security Notes

- All tokens are stored securely in the database
- Xero tokens are encrypted before storage
- Access tokens expire after 30 minutes
- Refresh tokens are single-use and rotated
- Failed login attempts are rate-limited
- Password reset requests are rate-limited per email
