import os
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()


class Settings(BaseSettings):
    # OAuth settings
    client_id: str
    client_secret_key: str
    secret_key: str

    # Environment settings
    env: str
    debug: bool

    # Brain settings
    api_key: str
    brain_base_url: str

    # Frontend settings
    frontend_url: str

    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    # Database settings
    database_url: str
    max_login_attempts: int
    login_cooldown_minutes: int

    # Xero endpoints
    xero_metadata_url: str
    xero_token_endpoint: str

    # OAuth Xero scope
    scope: str

    @property
    def brain_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    class Config:
        env_file = ".env"
        case_sensitive = False


class AppConfig:
    def __init__(self):
        self.settings = Settings()
        self.app = FastAPI(title="Xero FastAPI Integration")
        self._configure_middleware()
        self._configure_oauth()

    def _configure_middleware(self):
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=self.settings.secret_key,
            session_cookie="session",
        )

    def _configure_oauth(self):
        if self.settings.env != "production":
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


# Create single instance
config = AppConfig()
app = config.app
settings = config.settings
