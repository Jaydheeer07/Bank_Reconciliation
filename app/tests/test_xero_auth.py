import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.oauth import oauth
from app.models.database.schema_models import User
from app.models.xero.xero_state_models import XeroState
from app.utils.xero.state_utils import generate_state_parameter


@pytest.fixture
def test_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="dummy_hash"
    )


@pytest.fixture
def test_state(test_user):
    return XeroState(
        state=generate_state_parameter(),
        user_id=test_user.id,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )


@pytest.fixture
def mock_oauth():
    with patch("app.routes.xero.auth.oauth") as mock:
        mock.xero = AsyncMock()
        yield mock


def test_index_no_token(client, db: Session):
    """Test authentication status when no token exists"""
    response = client.get("/api/v1/xero/auth/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unauthenticated"
    assert data["redirect_url"] == "/api/v1/xero/auth/login"


def test_index_with_expired_token(client, db: Session, mock_token):
    """Test authentication status with expired token"""
    # Setup expired token
    mock_token["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)
    
    response = client.get("/api/v1/xero/auth/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "expired"
    assert data["redirect_url"] == "/api/v1/xero/auth/login"


def test_login_generates_state(client, db: Session, test_user, mock_oauth):
    """Test that login endpoint generates and stores state"""
    response = client.get("/api/v1/xero/auth/login")
    assert response.status_code == 200
    
    # Verify state was stored
    state = db.query(XeroState).first()
    assert state is not None
    assert state.user_id == test_user.id


def test_callback_with_invalid_state(client, db: Session):
    """Test callback with invalid state parameter"""
    response = client.get("/api/v1/xero/auth/callback?state=invalid")
    assert response.status_code == 200  # We return 200 with error message
    data = response.json()
    assert data["status"] == "error"
    assert "Invalid or expired" in data["message"]


def test_callback_with_expired_state(client, db: Session, test_user):
    """Test callback with expired state"""
    # Create expired state
    expired_state = XeroState(
        state=generate_state_parameter(),
        user_id=test_user.id,
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=50)
    )
    db.add(expired_state)
    db.commit()

    response = client.get(f"/api/v1/xero/auth/callback?state={expired_state.state}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "expired" in data["message"].lower()


def test_successful_callback(client, db: Session, test_state, mock_oauth):
    """Test successful OAuth callback"""
    # Add test state to db
    db.add(test_state)
    db.commit()

    # Mock successful token response
    mock_oauth.xero.authorize_access_token.return_value = {
        "access_token": "dummy_token",
        "token_type": "Bearer",
        "expires_in": 1800,
        "refresh_token": "dummy_refresh"
    }

    response = client.get(f"/api/v1/xero/auth/callback?state={test_state.state}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify state was cleaned up
    assert db.query(XeroState).filter_by(state=test_state.state).first() is None
