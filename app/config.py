import logging
import os
from typing import Dict
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from starlette.middleware.sessions import SessionMiddleware

# Try to load .env from current directory, if not found, try parent directory
env_path = Path('.env')
if not env_path.exists():
    env_path = Path('../.env')

load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # OAuth settings
    client_id: str
    client_secret_key: str
    secret_key: str

    # Environment settings
    env: str
    debug: bool

    # Azure Key Vault settings
    key_vault_url: str | None = None

    # Brain settings
    api_key: str
    brain_base_url: str

    # Frontend settings
    frontend_url: str

    # SMTP Settings
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender_email: str
    smtp_use_tls: bool

    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    # Database settings
    database_url: str
    max_login_attempts: int
    login_cooldown_minutes: int

    # Azure Database Settings
    azure_postgres_host: str
    azure_postgres_user: str
    azure_postgres_port: int
    azure_postgres_database: str
    azure_postgres_password: str

    # Xero endpoints
    xero_metadata_url: str
    xero_token_endpoint: str

    # OAuth Xero scope
    scope: str

    # Cron settings
    schedule_hour: str  
    schedule_minute: str
    schedule_second: str
    schedule_day: str
    schedule_month: str
    schedule_day_of_week: str

    @property
    def brain_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env

    def __init__(self):
        super().__init__()
        logger.info("Loaded environment variables:")
        logger.info(f"CLIENT_ID: {self.client_id}")
        logger.info(f"SCOPE: {self.scope}")
        logger.info(f"XERO_METADATA_URL: {self.xero_metadata_url}")


class AppConfig:
    def __init__(self):
        self.settings = Settings()
        self.app = FastAPI(
            title="Xero FastAPI Integration",
            version="1.0.0",
            docs_url="/api/v1/docs",  # Swagger UI path
            openapi_url="/api/v1/openapi.json",  # OpenAPI schema path
            redoc_url="/api/v1/redoc",  # ReDoc path
        )
        self._configure_middleware()
        self._configure_oauth()

    def _configure_middleware(self):
        """Configure middleware for the application."""
        # Add session middleware with secure configuration
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=self.settings.secret_key,
            session_cookie="xero_auth_session",
            max_age=3600,  # 1 hour
            same_site="none" if self.settings.env != "development" else "lax",
            https_only=self.settings.env != "development"  # Set to True in production
        )

    def _configure_oauth(self):
        if self.settings.env == "development":
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


# Create single instance
config = AppConfig()
app = config.app
settings = config.settings
