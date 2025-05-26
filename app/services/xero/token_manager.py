import json
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.xero.xero_token_models import XeroToken

logger = logging.getLogger(__name__)

class XeroTokenManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(XeroTokenManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the token manager"""
        self._cache = {}
        self._db = None

    def _get_db(self) -> Session:
        """Get database session"""
        if not self._db:
            self._db = SessionLocal()
        return self._db

    def _close_db(self):
        """Close database session"""
        if self._db:
            self._db.close()
            self._db = None

    def get_current_token(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the current token from cache or database.
        If user_id is None, returns the most recently updated valid token.
        """
        try:
            # Try cache first
            if user_id and user_id in self._cache:
                token_dict = self._cache[user_id]
                if not self._is_token_expired(token_dict):
                    logger.debug(f"Using cached token for user {user_id}")
                    return token_dict

            db = self._get_db()
            
            # Query for token
            query = db.query(XeroToken)
            if user_id:
                query = query.filter(XeroToken.user_id == user_id)
            token_record = query.order_by(XeroToken.expires_at.desc()).first()

            if not token_record or not token_record.token_data:
                logger.warning(f"No token found for user {user_id}")
                return None

            token_dict = json.loads(token_record.token_data)
            
            # Check if token is expired
            if self._is_token_expired(token_dict):
                # Try to refresh the token
                new_token = self.refresh_token(token_dict)
                if new_token:
                    # Store the refreshed token
                    self.store_token(new_token, str(token_record.user_id))
                    return new_token
                return None

            # Cache the valid token
            if user_id:
                self._cache[user_id] = token_dict

            return token_dict

        except Exception as e:
            logger.error(f"Error getting token: {str(e)}", exc_info=True)
            return None
        finally:
            self._close_db()

    def store_token(self, token_data: Dict[str, Any], user_id: str) -> bool:
        """Store or update token in database and cache"""
        try:
            db = self._get_db()
            
            # Create token dictionary with expiry
            token_dict = self._create_token_dict(token_data)
            
            # Calculate expires_at for database
            expires_at = datetime.fromtimestamp(token_dict["expires_at"], tz=timezone.utc)
            
            # Update or create token record
            token_record = db.query(XeroToken).filter(XeroToken.user_id == user_id).first()
            if token_record:
                token_record.token_data = json.dumps(token_dict)
                token_record.expires_at = expires_at
            else:
                token_record = XeroToken(
                    user_id=user_id,
                    token_data=json.dumps(token_dict),
                    created_at=datetime.now(timezone.utc),
                    expires_at=expires_at
                )
                db.add(token_record)

            db.commit()
            
            # Update cache
            self._cache[user_id] = token_dict
            
            logger.info(f"Token stored successfully for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing token: {str(e)}", exc_info=True)
            db.rollback()
            return False
        finally:
            self._close_db()

    def refresh_token(self, token_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Refresh the token using the refresh token"""
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }

            data = {
                "grant_type": "refresh_token",
                "refresh_token": token_data.get("refresh_token"),
                "client_id": settings.client_id,
                "client_secret": settings.client_secret_key
            }

            response = requests.post(settings.xero_token_endpoint, headers=headers, data=data)

            if response.status_code == 200:
                new_token = response.json()
                new_token_dict = self._create_token_dict(new_token)
                logger.info("Token refreshed successfully")
                return new_token_dict
            else:
                logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
            return None

    def invalidate_token(self, user_id: str) -> bool:
        """Invalidate token for a user"""
        try:
            # Remove from cache
            self._cache.pop(user_id, None)
            
            # Remove from database
            db = self._get_db()
            token_record = db.query(XeroToken).filter(XeroToken.user_id == user_id).first()
            if token_record:
                db.delete(token_record)
                db.commit()
                logger.info(f"Token invalidated for user {user_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Error invalidating token: {str(e)}", exc_info=True)
            return False
        finally:
            self._close_db()

    def _create_token_dict(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete token dictionary including expiry time"""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 0))
        return {
            "access_token": token_data.get("access_token"),
            "token_type": token_data.get("token_type", "Bearer"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
            "expires_at": expires_at.timestamp(),
            "scope": settings.scope
        }

    def _is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is expired or about to expire in the next 60 seconds"""
        if not token_data or "expires_at" not in token_data:
            return True
        return datetime.now(timezone.utc).timestamp() >= (token_data["expires_at"] - 60)

# Create singleton instance
token_manager = XeroTokenManager()
