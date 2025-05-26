import logging
from urllib.parse import quote_plus

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Get the logger configured in main.py
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL either from environment or Azure Key Vault"""
    if settings.env == "development":
        # Use local environment variables in development
        if hasattr(settings, "azure_postgres_password"):
            # Construct URL with properly encoded credentials
            encoded_password = quote_plus(settings.azure_postgres_password)
            return f"postgresql://{settings.azure_postgres_user}:{encoded_password}@{settings.azure_postgres_host}:{settings.azure_postgres_port}/{settings.azure_postgres_database}?sslmode=require"
        return settings.database_url
    else:
        try:
            # Use Azure Key Vault in production
            credential = DefaultAzureCredential()
            key_vault_url = settings.key_vault_url
            secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

            # Fetch database credentials from Key Vault
            db_password = secret_client.get_secret("db-password").value
            db_user = secret_client.get_secret("db-user").value

            # Construct database URL with credentials
            encoded_password = quote_plus(db_password)
            return f"postgresql://{db_user}:{encoded_password}@{settings.azure_postgres_host}:{settings.azure_postgres_port}/{settings.azure_postgres_database}?sslmode=require"
        except Exception as e:
            logger.error(f"Failed to fetch credentials from Key Vault: {str(e)}")
            # Fallback to environment variables if Key Vault access fails
            return settings.database_url


# Get DATABASE_URL
DATABASE_URL = get_database_url()
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables or Key Vault")


# Create engine with logging
logger.info("Attempting to connect to database...")  
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable automatic reconnection
    pool_size=5,  # Set connection pool size
    max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models using SQLAlchemy 2.0 style
Base = declarative_base()
