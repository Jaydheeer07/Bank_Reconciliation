# Brain Integration Documentation

This document provides detailed information about the Brain-related endpoints in the Bank Reconciliation API.

## Base URL

All Brain endpoints are prefixed with `/api/v1`

## Authentication

These endpoints require proper authentication headers as configured in the application settings.

## Brain Endpoints

### Brain Management

#### 1. List Brains

Retrieves a list of brains with pagination support.

- **URL**: `/api/v1/brain/me/`
- **Method**: `GET`
- **Query Parameters**:
  - `start` (optional): Starting index for pagination (default: 0)
  - `limit` (optional): Number of items per page (default: 20)
  - `sort` (optional): Sort order, can be "desc" or "asc" (default: "desc")

- Response

```json
{
    // Array of brain objects
    // Exact structure depends on the brain service response
}
```

#### 2. Get Brain by ID

Retrieves details of a specific brain by its ID.

- **URL**: `/api/v1/brain/me/:brain_id`
- **Method**: `GET`
- **Note**: Replace `:brain_id` with the actual brain ID. Use the List Brains endpoint to get available brain IDs.

- Response

```json
{
    // Brain object details
    // Exact structure depends on the brain service response
}
```

#### 3. Create Brain

Creates a new brain with the specified details.

- **URL**: `/api/v1/brain/me/create`
- **Method**: `POST`
- **Request Body**:

```json
{
    "name": "string",
    "description": "string" // optional
}
```

### File Management

#### 1. List Files

Lists all documents in a brain with optional filters and pagination.

- **URL**: `/api/v1/brain/files/`
- **Method**: `GET`
- **Query Parameters**:
  - `brain_id` (required): Brain ID to filter files
  - `start` (optional): Starting index for pagination (default: 0)
  - `limit` (optional): Number of items per page (default: 20)
  - `sort` (optional): Sort order, can be "desc" or "asc" (default: "desc")
  - `filter_by` (optional): Filter by document type: "invoice", "statement", or "all" (default: "all")

- Response

```json
{
    // Array of file objects
    // Exact structure depends on the brain service response
}
```

#### 2. Upload File

Uploads a document to a specific brain.

- **URL**: `/api/v1/brain/files/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Parameters**:
  - `file`: The file to upload
  - `brain_id`: Brain ID to associate the file with
  - `document_type`: Type of document ("invoice" or "statement")

- Response

```json
{
    "message": "File uploaded successfully",
    "details": {
        // Upload details from the brain service
    }
}
```

#### 3. Get File by ID

Retrieves details of a specific file.

- **URL**: `/api/v1/brain/files/:file_id`
- **Method**: `GET`
- **Note**: Replace `:file_id` with the actual file ID

- Response

```json
{
    // File object details
    // Exact structure depends on the brain service response
}
```

### File Processing

#### Process Text Content

Process text content through the brain API for various document types.

- **URL**: `/brain/files/text/process`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "brain_id": "string",
    "document_type": "string",  // Must be either "invoice" or "statement"
    "text": "string | object"   // Can be a JSON string or object
  }
  ```

- **Response**:
  ```json
  {
    // Processed text response
    // Structure depends on the document type and brain service response
  }
  ```

- **Notes**:
  - The `text` field can accept either a JSON string or an object
  - For invoices, the text should contain an "Invoices" array
  - The service will automatically handle JSON parsing and formatting
  - All processing results are logged for monitoring

- **Error Responses**:
  - `400`: Invalid request (e.g., invalid document type or text format)
  - `500`: Server error during processing

### Transaction Management

#### 1. Get Invoice Transactions

Retrieves invoice transactions for a brain with pagination.

- **URL**: `/api/v1/brain/transactions/invoices`
- **Method**: `GET`
- **Query Parameters**:
  - `brain_id` (required): Brain ID to filter transactions
  - `start` (optional): Starting index for pagination (default: 0)
  - `limit` (optional): Number of items per page (default: 20)
  - `sort` (optional): Sort order, can be "desc" or "asc" (default: "desc")

- Response

```json
{
    "data": [
        {
            // Invoice details with consolidated line items
            "lineItems": [
                // Array of line items for this invoice
            ]
        }
    ],
    "hasMore": boolean,
    "total": number
}
```

#### 2. Get Statement Transactions

Retrieves statement transactions for a brain with pagination.

- **URL**: `/api/v1/brain/transactions/statements`
- **Method**: `GET`
- **Query Parameters**:
  - `brain_id` (required): Brain ID to filter transactions
  - `start` (optional): Starting index for pagination (default: 0)
  - `limit` (optional): Number of items per page (default: 20)
  - `sort` (optional): Sort order, can be "desc" or "asc" (default: "desc")

- Response

```json
{
    "data": [
        // Array of statement transactions
    ],
    "hasMore": boolean,
    "total": number
}
```

#### 3. Get Reconciliation

Retrieves reconciliation data for a brain within a specified date range.

- **URL**: `/api/v1/brain/transactions/recon`
- **Method**: `GET`
- **Query Parameters**:
  - `brain_id` (required): Brain ID for reconciliation
  - `start_period` (required): Start of the period (Unix timestamp)
  - `end_period` (optional): End of the period (Unix timestamp, defaults to now)
  - `filter_by` (optional): Filter by status: "all" or "verified" (default: "all")

- Response

```json
{
    "data": [
        {
            // Reconciliation record with consolidated matching invoice items
            "matchingInvoiceItems": [
                {
                    // Invoice details with consolidated line items
                    "lineItems": [
                        // Array of line items for this invoice
                    ]
                }
            ]
        }
    ]
}
```

#### 4. Verify Reconciliation

Verifies one or more reconciled transactions.

- **URL**: `/api/v1/brain/transactions/verify`
- **Method**: `POST`
- **Request Body**: Array of reconciliation mappings

```json
[
  {
    "statementId": "string",
    "invoiceIds": ["string"]
  }
]
```

- Response

```json
{
  "message": "success"
}
```

Example:

```json
// Request
[
  {
    "statementId": "st_755e73c0-987d-45e1-8585-e1ed4e9e41bc",
    "invoiceIds": [
      "inv_741faef4-6c6c-4edd-a5b4-45b17ecaa436"
    ]
  }
]

// Response
{
  "message": "success"
}
```

## Testing with Postman

1. Import the `Bank_Reconciliation_API.postman_collection.json` collection into Postman.
2. Navigate to the "Brain Management" folder in the collection.
3. Each endpoint is organized in its respective folder:
   - **Me**: Brain management endpoints
   - **Files**: File management endpoints
   - **Transactions**: Transaction management endpoints
4. For endpoints with path variables (like `:brain_id` or `:file_id`):
   - The variables can be set directly in the request's "Path Variables" tab
   - Use the List endpoints to get valid IDs
5. Make sure to set up any required environment variables for authentication.

## Error Handling

All endpoints follow a consistent error handling pattern:

- **400 Bad Request**: Invalid input parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side issues

Each error response includes a detail message explaining the error.
