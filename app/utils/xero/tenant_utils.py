import asyncio
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database.tenant_models import TenantMetadata
from app.models.xero.xero_token_models import XeroToken

logger = logging.getLogger(__name__)


async def get_active_tenant_id(db: Session, user_id: str) -> Optional[str]:
    """
    Get the active Xero tenant ID from the XeroToken table.
    The tenant_id in XeroToken represents the currently selected tenant for the user's session.
    """
    try:
        token_record = (
            db.query(XeroToken)
            .filter(
                XeroToken.user_id == user_id,
            )
            .first()
        )

        if token_record and token_record.tenant_id:
            logger.info(
                f"Retrieved active tenant ID from token: {token_record.tenant_id}"
            )
            return token_record.tenant_id

        logger.info("No active tenant found in token record")
        return None

    except Exception as e:
        logger.error(f"Error getting active tenant ID: {str(e)}", exc_info=True)
        return None


async def validate_tenant_access(db: Session, user_id: str, tenant_id: str) -> bool:
    """
    Validate that the user has access to the specified tenant.
    This checks if the tenant exists in our database and belongs to the user.
    """
    try:
        tenant_exists = (
            db.query(TenantMetadata)
            .filter(
                TenantMetadata.user_id == user_id, TenantMetadata.tenant_id == tenant_id
            )
            .first()
            is not None
        )

        if tenant_exists:
            logger.info(
                f"Validated tenant access for user {user_id} and tenant {tenant_id}"
            )
            return True

        logger.warning(f"Tenant {tenant_id} not found for user {user_id}")
        return False

    except Exception as e:
        logger.error(f"Error validating tenant access: {str(e)}", exc_info=True)
        return False


async def create_tenant_metadata(
    db: Session,
    user_id: str,
    tenant_id: str,
    tenant_name: str,
    tenant_short_code: str,
    table_name: str,
) -> TenantMetadata:
    """Create a new tenant metadata entry."""
    try:
        tenant_metadata = TenantMetadata(
            user_id=user_id,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            tenant_short_code=tenant_short_code,
            table_name=table_name,
        )
        db.add(tenant_metadata)
        db.commit()
        db.refresh(tenant_metadata)
        logger.info(f"Created tenant metadata for tenant {tenant_name}")
        return tenant_metadata
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tenant metadata: {str(e)}", exc_info=True)
        raise


async def get_tenant_metadata(db: Session, tenant_id: str, user_id: str) -> Optional[TenantMetadata]:
    """Get tenant metadata by tenant_id."""
    try:
        # Run synchronous database operation in a thread pool
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: db.query(TenantMetadata)
            .filter(TenantMetadata.tenant_id == tenant_id,
                    TenantMetadata.user_id == user_id
            )
            .first(),
        )
    except Exception as e:
        logger.error(f"Error getting tenant metadata: {str(e)}", exc_info=True)
        return None


async def update_tenant_metadata(
    db: Session, tenant_id: str, **kwargs
) -> Optional[TenantMetadata]:
    """Update tenant metadata fields."""
    try:
        tenant = (
            db.query(TenantMetadata)
            .filter(TenantMetadata.tenant_id == tenant_id)
            .first()
        )
        if tenant:
            for key, value in kwargs.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)
            db.commit()
            db.refresh(tenant)
            logger.info(f"Updated tenant metadata for tenant {tenant_id}")
            return tenant
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating tenant metadata: {str(e)}", exc_info=True)
        raise


async def generate_table_name(user_id: str, tenant_name: str) -> str:
    """
    Generate a PostgreSQL-safe table name from user_id and tenant name.

    Format: data_{uuid}_{tenant_name}
    """
    # Clean tenant name: remove spaces and special characters, convert to lowercase
    safe_tenant_name = "".join(c.lower() for c in tenant_name if c.isalnum())
    return f"data_{user_id}_{safe_tenant_name}"
