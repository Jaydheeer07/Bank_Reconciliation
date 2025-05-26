# Brain Management and Scheduled Tasks

## Overview

This document provides comprehensive information about the Brain Management system and Scheduled Tasks features of the Bank Reconciliation application. These components work together to provide intelligent document processing and automated reconciliation of financial data.

## Table of Contents

- [Brain System](#brain-system)
  - [Brain Management](#brain-management)
  - [Document Management](#document-management)
  - [Transaction Processing](#transaction-processing)
- [Scheduled Tasks](#scheduled-tasks)
  - [Job Management](#job-management)
  - [Statement Processing](#statement-processing)
  - [Invoice Processing](#invoice-processing)
- [Reconciliation System](#reconciliation-system)
  - [Draft Reconciliation](#draft-reconciliation)
  - [Verification](#verification)

## Brain System

The Brain system provides intelligent document processing capabilities, allowing the application to:

1. **Process Invoices** - Extract information from invoice documents
2. **Process Statements** - Extract information from bank statements
3. **Match Transactions** - Intelligently match invoice and statement transactions
4. **Generate Reconciliations** - Create draft reconciliation entries based on matched transactions

### Brain Management

The Brain Management module allows users to create and manage "brains" - intelligent processing units that can be associated with specific tenants or users. Each brain maintains its own context and document history.

Key features:
- Create new brains with specific configurations
- Retrieve brain information and status
- Monitor brain processing statistics
- Associate brains with specific users or tenants

The brain system acts as the intelligence layer of the application, processing documents and extracting structured data for reconciliation.

### Document Management

The Document Management module handles file uploads, processing, and retrieval:

1. **File Upload** - Upload invoices and bank statements
2. **Text Processing** - Process raw text content from various sources
3. **Document Listing** - View uploaded and processed documents
4. **Document Retrieval** - Access specific document details and processing results

All documents are associated with a specific brain and are typed as either "invoice" or "statement" to enable proper processing.

### Transaction Processing

The Transaction Processing module handles the core reconciliation functionality:

1. **Invoice Transactions** - View processed invoice data
2. **Statement Transactions** - View processed statement data
3. **Reconciliation** - Match invoices with bank statement entries
4. **Verification** - Mark reconciliation entries as verified

This module bridges the gap between raw document data and actionable reconciliation entries.

## Scheduled Tasks

The Scheduled Tasks system enables automated, recurring processing of financial data. This system allows the application to:

1. **Schedule Jobs** - Create recurring processing tasks
2. **Process Data** - Automatically fetch and process new data
3. **Monitor Progress** - Track job status and results
4. **Manage Execution** - Start, stop, and configure jobs

### Job Management

The Job Manager handles the creation, scheduling, and execution of recurring tasks:

- Jobs are associated with a specific user, tenant, and brain
- Jobs can be scheduled with custom intervals using cron syntax
- Jobs are processed sequentially to avoid resource contention
- Failed jobs are logged with detailed error information for troubleshooting

The system uses APScheduler with a SQLAlchemy job store for persistent scheduling across application restarts.

### Statement Processing

The Statement Processor fetches bank statement data and processes it through the brain:

1. **Data Fetching** - Retrieves statement data from the database
2. **Brain Processing** - Sends statement data to the brain for processing
3. **Results Handling** - Processes and stores the brain's analysis results
4. **Reconciliation Updates** - Updates draft reconciliation entries based on new data

Statement processing jobs run on a configurable schedule to ensure timely updates.

### Invoice Processing

The Invoice Processor fetches Xero invoice data and processes it through the brain:

1. **Xero API Calls** - Fetches new invoice data from Xero
2. **Brain Processing** - Sends invoice data to the brain for processing
3. **Results Handling** - Processes and stores the brain's analysis results
4. **Reconciliation Updates** - Updates draft reconciliation entries based on new data

Invoice processing jobs ensure that the latest Xero invoice data is always available for reconciliation.

## Reconciliation System

The Reconciliation system combines processed statements and invoices to create draft reconciliation entries:

### Draft Reconciliation

Draft reconciliation entries are created automatically by the brain based on matching algorithms:

- Each entry links a specific bank statement transaction with a matching invoice
- Entries include detailed information from both the statement and invoice
- Users can review, verify, or reject these automated matches
- Notes can be added to each entry for additional context

### Verification

The verification process allows users to:

1. **Review** - Check suggested matches between statements and invoices
2. **Approve** - Mark reconciliation entries as verified
3. **Reject** - Remove incorrect matches
4. **Annotate** - Add notes to explain special cases or issues

Verified reconciliations can then be used for financial reporting and auditing purposes.