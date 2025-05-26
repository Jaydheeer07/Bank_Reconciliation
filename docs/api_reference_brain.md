# API Reference - Brain Management and Scheduled Tasks

## Overview

This document provides a reference for all Brain Management and Scheduled Tasks endpoints in the Bank Reconciliation API. It should be used alongside the main API reference document.

## Table of Contents

- [Brain Management Endpoints](#brain-management-endpoints)
  - [Brain Management](#brain-management)
    - [Get Brains](#get-brains)
    - [Get Brain by ID](#get-brain-by-id)
    - [Create Brain](#create-brain)
  - [File Management](#file-management)
    - [List Files](#list-files)
    - [Upload File](#upload-file)
    - [Get File](#get-file)
    - [Process Text](#process-text)
  - [Transaction Management](#transaction-management)
    - [Get Brain Statistics](#get-brain-statistics)
    - [Get Invoice Transactions](#get-invoice-transactions)
    - [Get Statement Transactions](#get-statement-transactions)
    - [Get Reconciliation](#get-reconciliation)
    - [Verify Reconciliation](#verify-reconciliation)
    - [Save Invoice Notes](#save-invoice-notes)
- [Scheduled Jobs Endpoints](#scheduled-jobs-endpoints)
  - [Stop Processing Job](#stop-processing-job)
- [Error Codes](#error-codes)

## Brain Management Endpoints

### Brain Management

#### Get Brains

**Endpoint**: `GET /brain/me/`

**Description**: Get a list of brains owned by the user.

**Request**:
- Authorization: Bearer token required
- Query Parameters:
  - `start` (optional): Pagination start value (default: 0)
  - `limit` (optional): Number of results to return (default: 20)
  - `sort` (optional): Sort order, 'asc' or 'desc' (default: desc)

**Response Success**:
```json
{
  "brains": [
    {
      "id": "brain-123-456",
      "name": "My Reconciliation Brain",
      "created_at": "2025-01-01T00:00:00Z",
      "status": "active",
      "document_count": 125,
      "transaction_count": 1250
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "total_items": 1
}
```

#### Get Brain by ID

**Endpoint**: `GET /brain/me/{brain_id}`

**Description**: Get details of a specific brain by ID.

**Request**:
- Authorization: Bearer token required
- Path Parameters:
  - `brain_id`: ID of the brain to retrieve

**Response Success**:
```json
{
  "id": "brain-123-456",
  "name": "My Reconciliation Brain",
  "created_at": "2025-01-01T00:00:00Z",
  "status": "active",
  "document_count": 125,
  "transaction_count": 1250,
  "config": {
    "matching_threshold": 0.8,
    "auto_verification": false
  }
}
```

#### Create Brain

**Endpoint**: `POST /brain/me/create`

**Description**: Create a new brain.

**Request**:
- Authorization: Bearer token required
- Request Body:
```json
{
  "name": "My New Brain",
  "config": {
    "matching_threshold": 0.8,
    "auto_verification": false
  }
}
```

**Response Success** (201 Created):
```json
{
  "id": "brain-789-012",
  "name": "My New Brain",
  "created_at": "2025-01-02T00:00:00Z",
  "status": "active",
  "document_count": 0,
  "transaction_count": 0,
  "config": {
    "matching_threshold": 0.8,
    "auto_verification": false
  }
}
```

### File Management

#### List Files

**Endpoint**: `GET /brain/files/`

**Description**: List all documents in a brain.

**Request**:
- Authorization: Bearer token required
- Query Parameters:
  - `brain_id` (required): Brain ID to filter files
  - `start` (optional): Pagination start value (default: 0)
  - `limit` (optional): Number of results to return (default: 20)
  - `sort` (optional): Sort order, 'asc' or 'desc' (default: desc)
  - `filter_by` (optional): Filter by document type: 'invoice', 'statement', or 'all' (default: all)

**Response Success**:
```json
{
  "files": [
    {
      "id": "file-123-456",
      "name": "January2025_Statement.pdf",
      "type": "statement",
      "size": 256000,
      "uploaded_at": "2025-01-01T00:00:00Z",
      "status": "processed",
      "transaction_count": 25
    },
    {
      "id": "file-789-012",
      "name": "Invoice_12345.pdf",
      "type": "invoice",
      "size": 128000,
      "uploaded_at": "2025-01-02T00:00:00Z",
      "status": "processed",
      "transaction_count": 1
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "total_items": 2
}
```

#### Upload File

**Endpoint**: `POST /brain/files/upload`

**Description**: Upload a document for processing.

**Request**:
- Authorization: Bearer token required
- Content-Type: multipart/form-data
- Form Parameters:
  - `file`: The file to upload
  - `brain_id`: Brain ID to associate the file with
  - `document_type`: Document type (e.g., "invoice" or "statement")

**Response Success**:
```json
{
  "message": "File uploaded successfully",
  "details": {
    "file_id": "file-345-678",
    "name": "February2025_Statement.pdf",
    "type": "statement",
    "size": 256000,
    "status": "processing",
    "uploaded_at": "2025-01-03T00:00:00Z"
  }
}
```

#### Get File

**Endpoint**: `GET /brain/files/{file_id}`

**Description**: Get details of a specific document.

**Request**:
- Authorization: Bearer token required
- Path Parameters:
  - `file_id`: ID of the file to retrieve

**Response Success**:
```json
{
  "id": "file-345-678",
  "name": "February2025_Statement.pdf",
  "type": "statement",
  "size": 256000,
  "uploaded_at": "2025-01-03T00:00:00Z",
  "status": "processed",
  "transaction_count": 30,
  "transactions": [
    {
      "id": "tx-123-456",
      "description": "Office Supplies",
      "amount": 250.00,
      "date": "2025-02-01T00:00:00Z"
    }
  ]
}
```

#### Process Text

**Endpoint**: `POST /brain/files/text/process`

**Description**: Process text content from various document types.

**Request**:
- Authorization: Bearer token required
- Request Body:
```json
{
  "brain_id": "brain-123-456",
  "document_type": "invoice",
  "text": "{\"Invoices\": [{\"InvoiceNumber\": \"INV-001\", \"Date\": \"2025-01-01\", \"DueDate\": \"2025-01-31\", \"Amount\": 1000.00, \"Description\": \"Consulting Services\"}]}"
}
```

**Response Success**:
```json
{
  "status": "success",
  "message": "Text processed successfully",
  "details": {
    "document_id": "doc-123-456",
    "transaction_count": 1,
    "status": "processed"
  }
}
```

### Transaction Management

#### Get Brain Statistics

**Endpoint**: `GET /brain/transactions/stats`

**Description**: Get statistics for a brain, including reconciliation status counts.

**Request**:
- Authorization: Bearer token required
- Query Parameters:
  - `brain_id` (required): Brain ID to get statistics for

**Response Success**:
```json
{
  "document_counts": {
    "invoices": 50,
    "statements": 12
  },
  "transaction_counts": {
    "invoices": 50,
    "statements": 250
  },
  "reconciliation": {
    "matched": 45,
    "unmatched": 5,
    "verified": 40,
    "pending": 5
  },
  "last_updated": "2025-01-03T12:34:56Z"
}
```

#### Get Invoice Transactions

**Endpoint**: `GET /brain/transactions/invoices`

**Description**: Get invoice transactions for a brain.

**Request**:
- Authorization: Bearer token required
- Query Parameters:
  - `brain_id` (required): Brain ID to filter transactions
  - `start` (optional): Pagination start value (default: 0)
  - `limit` (optional): Number of results to return (default: 20)
  - `sort` (optional): Sort order, 'asc' or 'desc' (default: desc)
  - `query` (optional): Search query for invoices

**Response Success**:
```json
{
  "invoices": [
    {
      "id": "inv-123-456",
      "invoice_number": "INV-001",
      "date": "2025-01-01T00:00:00Z",
      "due_date": "2025-01-31T00:00:00Z",
      "sender": {
        "name": "ABC Company",
        "address": "123 Business St, Business City"
      },
      "recipient": {
        "name": "XYZ Corp",
        "address": "456 Corporate Ave, Enterprise City"
      },
      "total_amount": 1000.00,
      "currency": "USD",
      "status": "matched",
      "verification_status": "verified"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "total_items": 1
}
```

#### Get Statement Transactions

**Endpoint**: `GET /brain/transactions/statements`

**Description**: Get statement transactions for a brain.

**Request**:
- Authorization: Bearer token required
- Query Parameters:
  - `brain_id` (required): Brain ID to filter transactions
  - `start` (optional): Pagination start value (default: 0)
  - `limit` (optional): Number of results to return (default: 20)
  - `sort` (optional): Sort order, 'asc' or 'desc' (default: desc)

**Response Success**:
```json
{
  "statements": [
    {
      "id": "stmt-123-456",
      "date": "2025-01-02T00:00:00Z",
      "description": "Incoming payment - ABC Company",
      "payee": "ABC Company",
      "amount": 1000.00,
      "currency": "USD",
      "account": "Business Checking",
      "status": "matched",
      "verification_status": "verified",
      "file_id": "file-123-456"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "total_items": 1
}
```

#### Get Reconciliation

**Endpoint**: `GET /brain/transactions/recon`

**Description**: Get reconciliation data matching invoices and statements.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Query Parameters:
  - `brain_id` (required): Brain ID for reconciliation
  - `start_period` (optional): Start of the period (Unix timestamp)
  - `end_period` (optional): End of the period (Unix timestamp)
  - `sort` (optional): Sort order, 'asc' or 'desc' (default: desc)
  - `status` (optional): Filter by status: 'verified', 'unverified', 'all' (default: all)

**Response Success**:
```json
{
  "reconciliation": [
    {
      "id": "recon-123-456",
      "statementItem": {
        "statementId": "stmt-123-456",
        "date": "2025-01-02T00:00:00Z",
        "description": "Incoming payment - ABC Company",
        "payee": "ABC Company",
        "amount": 1000.00,
        "verified": true
      },
      "matchingInvoices": {
        "invoiceId": "inv-123-456",
        "invoiceNumber": "INV-001",
        "date": "2025-01-01T00:00:00Z",
        "dueDate": "2025-01-31T00:00:00Z",
        "sender": {
          "name": "ABC Company"
        },
        "totalAmount": 1000.00,
        "notes": "Payment received on time"
      }
    }
  ],
  "metadata": {
    "tenant_id": "xxx-xxx-xxx",
    "tenant_name": "My Company Ltd",
    "period": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-31T23:59:59Z"
    },
    "stats": {
      "total": 1,
      "verified": 1,
      "unverified": 0
    }
  }
}
```

#### Verify Reconciliation

**Endpoint**: `POST /brain/transactions/recon/verify`

**Description**: Verify one or more reconciled transactions.

**Request**:
- Authorization: Bearer token required
- Request Body:
```json
[
  {
    "statement_id": "stmt-123-456",
    "invoice_id": "inv-123-456",
    "verified": true
  }
]
```

**Response Success**:
```json
{
  "status": "success",
  "message": "Reconciliation verification updated",
  "updated": 1,
  "details": [
    {
      "statement_id": "stmt-123-456",
      "invoice_id": "inv-123-456",
      "status": "verified"
    }
  ]
}
```

#### Save Invoice Notes

**Endpoint**: `POST /brain/transactions/invoice/notes`

**Description**: Save notes for a specific invoice in the reconciliation system.

**Request**:
- Authorization: Bearer token required
- Xero Authentication: Required
- Active Tenant: Required
- Request Body:
```json
{
  "tenant_shortcode": "MCL",
  "statement_id": "stmt-123-456",
  "invoice_id": "inv-123-456",
  "notes": "Payment received on time"
}
```

**Response Success**:
```json
{
  "status": "success",
  "message": "Notes updated successfully",
  "entry": {
    "tenant_shortcode": "MCL",
    "statement_id": "stmt-123-456",
    "invoice_id": "inv-123-456",
    "notes": "Payment received on time",
    "updated_at": "2025-01-03T12:34:56Z"
  }
}
```

## Scheduled Jobs Endpoints

### Stop Processing Job

**Endpoint**: `POST /scheduled/stop-processing/{job_id}`

**Description**: Stop a scheduled processing job.

**Request**:
- Authorization: Bearer token required
- Path Parameters:
  - `job_id`: ID of the job to stop

**Response Success**:
```json
{
  "status": "success",
  "message": "Job stopped successfully",
  "job_id": "job-123-456"
}
```

**Response Error**:
```json
{
  "detail": "Job not found or already stopped"
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