# Invoice Processor Documentation

## Overview
The Invoice Processor is a scheduled task system that automatically fetches and processes invoices from Xero. It provides endpoints to start and stop the scheduled processing of invoices.

## Features
- Automated invoice fetching from Xero
- Configurable scheduling using cron expressions
- Integration with brain API for invoice processing
- Logging and error handling
- Easy start/stop control via API endpoints

## API Endpoints

### Start Invoice Processing
```http
POST /scheduled/start-invoice-processing
```

Starts the scheduled processing of Xero invoices. The schedule is configured through the application settings.

#### Query Parameters
- `brain_id` (required): The ID of the brain to process the invoices with

#### Authentication
- Requires a valid Xero OAuth token

#### Response
- 200: Successfully started the invoice processing schedule
- 400: No tenant selected
- 500: Internal server error

### Stop Invoice Processing
```http
POST /scheduled/stop-invoice-processing
```

Stops the scheduled processing of Xero invoices.

#### Response
- 200: Successfully stopped the invoice processing schedule
- 500: Internal server error

## Configuration
The schedule for invoice processing can be configured through the following settings in the config file:
- `schedule_hour`
- `schedule_minute`
- `schedule_second`
- `schedule_day`
- `schedule_month`
- `schedule_day_of_week`

## Functions

### process_xero_invoices
Fetches invoices from Xero and processes them through the brain API.

#### Parameters
- `brain_id`: The ID of the brain to process the invoices with
- `xero_tenant_id`: The Xero tenant ID

#### Process Flow
1. Connects to Xero API
2. Fetches invoices for the specified tenant
3. Serializes the invoice data
4. Processes the invoices through the brain API
5. Logs the results

#### How to Use
1. Login to your Xero account and authenticate
2. Select a tenant via the "Set Active Tenant" endpoint
3. Select a bank account via the "Set Active Account" endpoint
4. Configure the schedule for invoice processing
5. Enter the brain ID for invoice processing
6. Start the invoice processing schedule
7. Monitor the logs for processing results


### get_schedule_description
Constructs a human-readable description of the schedule interval based on cron components.

#### Parameters
- `hour`: Hour component of the cron expression
- `minute`: Minute component of the cron expression
- `day`: Day component of the cron expression
- `month`: Month component of the cron expression
- `day_of_week`: Day of week component of the cron expression

#### Returns
A string describing the schedule interval (e.g., "every 2 hours", "every 30 minutes")
