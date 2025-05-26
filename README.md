# Bank Reconciliation Application


## Overview

The Bank Reconciliation application is a powerful financial tool designed to automate the matching of bank statements with invoices from Xero. The system uses intelligent processing to identify matches, streamline reconciliation workflows, and improve financial accuracy.

## Features

- **Secure Authentication** - User login with token-based authentication
- **Xero Integration** - Seamless connection to Xero for accessing accounting data
- **Intelligent Matching** - AI-powered matching of bank statements and invoices
- **Scheduled Processing** - Automated data processing on configurable schedules
- **Reconciliation Verification** - Review and verify matched transactions
- **Document Management** - Upload and process bank statements and invoices
- **Multi-tenant Support** - Manage multiple Xero organizations

## Table of Contents

- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
  - [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [API Documentation](#api-documentation)
  - [Authentication Flow](#authentication-flow)
  - [Xero Integration](#xero-integration)
  - [Brain Management](#brain-management)
  - [Scheduled Tasks](#scheduled-tasks)
- [Architecture](#architecture)
  - [Component Overview](#component-overview)
  - [Database Schema](#database-schema)
  - [Authentication Flow](#authentication-flow-1)
  - [Azure Integration](#azure-integration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Project Structure

```
Bank_Reconciliation/
├── alembic/                   # Database migration scripts
├── app/                       # Main application code
│   ├── core/                  # Core functionality (auth, dependencies)
│   ├── models/                # Data models and schemas
│   ├── routes/                # API endpoints
│   │   ├── brain/             # Brain management endpoints
│   │   ├── user_account/      # User management endpoints
│   │   └── xero/              # Xero integration endpoints
│   ├── scheduled_tasks/       # Background processing jobs
│   ├── services/              # Service layer components
│   └── utils/                 # Utility functions
├── docs/                      # Documentation files
│   ├── auth/                  # Authentication documentation
│   ├── xero/                  # Xero integration documentation
│   └── brain/                 # Brain management documentation
├── .env.example               # Example environment variables
├── docker-compose.yml         # Docker configuration
├── Dockerfile                 # Docker build instructions
├── requirements.txt           # Python dependencies
└── run.py                     # Application entry point
```

## Setup and Installation

### Prerequisites

- Python 3.6 or higher
- PostgreSQL database
- Xero developer account
- Docker (optional, for containerized deployment)

### Local Setup

1. Clone the repository:

   ```sh
   git clone https://github.com/DexterousAi/Bank_Reconciliation.git
   cd Bank_Reconciliation
   ```
2. Create a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```
4. Set up environment variables:

   ```sh
   cp .env.example .env
   ```

   Edit the `.env` file with your configuration (see [Environment Variables](#environment-variables))
5. Run database migrations:

   ```sh
   alembic upgrade head
   ```

### Docker Setup

1. Clone the repository:

   ```sh
   git clone https://github.com/DexterousAi/Bank_Reconciliation.git
   cd Bank_Reconciliation
   ```
2. Create your environment file:

   ```sh
   cp .env.example .env
   ```

   Update the values in `.env` with your configuration.
3. Build and start the containers:

   ```sh
   docker-compose up -d
   ```
4. The services will be available at:

   - FastAPI application: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/api/v1/docs`
   - pgAdmin: `http://localhost:5050`

### Environment Variables

Create a `.env` file in the root directory with the following variables (see `.env.example` for a template):

```ini
# OAuth settings
CLIENT_ID="your_client_id"
CLIENT_SECRET_KEY="your_client_secret"
SECRET_KEY="your_secret_key"

# Environment settings
ENV="development"
DEBUG=true

# Brain settings
API_KEY="your_brain_api_key"
BRAIN_BASE_URL="your_brain_base_url"

# Frontend settings
FRONTEND_URL="your_frontend_url"

# SMTP Settings
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your_gmail_account@gmail.com"
SMTP_PASSWORD="16-digit-password"
SMTP_SENDER_EMAIL="your_gmail_account@gmail.com"
SMTP_USE_TLS=true

# JWT settings
JWT_SECRET_KEY="your_jwt_secret"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database settings
DATABASE_URL="postgresql://postgres:postgres@db:5432/fastapi_db"
MAX_LOGIN_ATTEMPTS=3
LOGIN_COOLDOWN_MINUTES=2

# Azure Database Settings
AZURE_POSTGRES_HOST="mycompany.postgres.database.azure.com"
AZURE_POSTGRES_USER="user_name"
AZURE_POSTGRES_PORT=port_number
AZURE_POSTGRES_DATABASE="database_name"
AZURE_POSTGRES_PASSWORD="{your-password}"

# Xero endpoints
XERO_METADATA_URL="https://identity.xero.com/.well-known/openid-configuration"
XERO_TOKEN_ENDPOINT="https://identity.xero.com/connect/token"

# OAuth Xero scope
SCOPE="offline_access openid profile email accounting.transactions accounting.journals.read accounting.transactions payroll.payruns accounting.reports.read files accounting.settings.read accounting.settings accounting.attachments payroll.payslip payroll.settings files.read openid assets.read profile payroll.employees projects.read email accounting.contacts.read accounting.attachments.read projects assets accounting.contacts payroll.timesheets accounting.budgets.read"

# Schedule settings
SCHEDULE_HOUR="*"
SCHEDULE_MINUTE="0"
SCHEDULE_SECOND="0"
SCHEDULE_DAY="*"
SCHEDULE_MONTH="*"
SCHEDULE_DAY_OF_WEEK="*"
```

## Usage

### Running the Application

#### Local Development

1. Activate your virtual environment:

   ```sh
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
2. Start the FastAPI server:

   ```sh
   python run.py
   ```
3. The server will start at `http://127.0.0.1:8000`

#### Docker Deployment

The application can be run using Docker Compose:

```sh
docker-compose up -d
```

Common Docker commands:

```sh
# Stop the containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers after changes
docker-compose build
docker-compose up -d

# Restart services
docker-compose restart
```

### API Documentation

The API documentation is available at:

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

Comprehensive API documentation is also available in the `/docs` directory:

- `/docs/api_reference.md` - Complete API reference for all endpoints
- `/docs/api_reference_brain.md` - Brain management API reference
- `/docs/auth/README.md` - Authentication documentation
- `/docs/xero/README.md` - Xero integration documentation
- `/docs/brain/README.md` - Brain management documentation

### Authentication Flow

The application uses JWT token-based authentication:

1. User registers or logs in with email and password
2. System issues access and refresh tokens
3. Access token used for subsequent API requests
4. Refresh token used to obtain new access tokens when expired
5. Token blacklisting on logout for security

### Xero Integration

The Xero integration uses OAuth 2.0 for authentication:

1. User initiates Xero connection
2. System redirects to Xero for authentication
3. User grants permissions to the application
4. Xero redirects back with authorization code
5. System exchanges code for access and refresh tokens
6. Tokens stored securely for future API calls

### Brain Management

The Brain Management system processes financial documents:

1. User uploads bank statements and invoices
2. Brain processes documents to extract data
3. Matching algorithm identifies potential matches
4. System creates draft reconciliation entries
5. User reviews and verifies matches

### Scheduled Tasks

Scheduled tasks automate data processing:

1. Statement Import - Fetches and processes bank statements
2. Invoice Import - Fetches and processes Xero invoices
3. Reconciliation - Automatically matches statements with invoices
4. Status Updates - Updates reconciliation status

## Architecture

### Component Overview

The Bank Reconciliation application consists of several key components:

1. **FastAPI Backend** - Provides REST API endpoints
2. **PostgreSQL Database** - Stores user data, tokens, and reconciliation entries
3. **Brain Service** - Intelligent document processing and matching
4. **Xero API Integration** - Connects to Xero for accounting data
5. **Scheduler** - Manages background processing tasks

### Database Schema

The application uses SQLAlchemy ORM with the following main models:

- **User** - User accounts and authentication
- **RefreshToken** - JWT refresh tokens for authentication
- **XeroToken** - Encrypted Xero OAuth tokens
- **TenantMetadata** - Xero organization information
- **ScheduledJob** - Background processing job configuration
- **DraftReconciliationEntry** - Matched statement and invoice entries

### Authentication Flow

The authentication system uses JWT tokens with:

1. Short-lived access tokens (30 minutes)
2. Longer-lived refresh tokens (30 days)
3. Token blacklisting for security
4. Account lockout after multiple failed attempts

### Azure Integration

The application supports Azure AD authentication for database connections using the `azure-identity` package. This provides secure, credential-free authentication when deployed to Azure:

1. **DefaultAzureCredential** - Used in database.py to create secure connections
2. **Managed Identity** - Enables credential-free authentication
3. **Key Vault Integration** - Securely stores sensitive credentials

To utilize Azure authentication:

1. Set up Azure AD application registration
2. Configure appropriate permissions
3. Update environment variables with Azure credentials
4. Deploy to Azure with managed identity enabled

## Documentation

Detailed documentation is available in the `/docs` directory:

1. **API References**

   - `api_reference.md` - Complete API reference
   - `api_reference_brain.md` - Brain management endpoints
2. **Topic-specific Documentation**

   - `auth/README.md` - Authentication system
   - `xero/README.md` - Xero integration
   - `brain/README.md` - Brain management
3. **Testing**

   - `Bank_Reconciliation_API.postman_collection.json` - Postman collection for API testing

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary and confidential.
Copyright (c) 2025 Dexterous AI. All rights reserved.
