import logging
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

# Import your existing components

logger = logging.getLogger(__name__)


def validate_table_name(table_name: str) -> bool:
    """Sanitize table name input using allowlist pattern"""
    # Allow schema-qualified names with hyphens: "schema.table" format
    if not re.match(r"^[a-zA-Z0-9_$-]+(\.[a-zA-Z0-9_$-]+)?$", table_name):
        return False
    return True


async def get_validated_table_name(db: Session, table_name: str) -> str:
    """
    Verify table exists and return properly quoted identifier
    """
    try:
        # Split schema and table name if provided
        parts = table_name.split(".", 1)
        schema = "public"
        table = table_name

        if len(parts) == 2:
            schema, table = parts
            if not validate_table_name(schema) or not validate_table_name(table):
                raise ValueError("Invalid schema or table name format")

        # Check table existence
        result = db.execute(
            text("""
            SELECT schemaname, tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname = :schema 
            AND tablename = :table
        """),
            {"schema": schema, "table": table},
        ).fetchall()

        if not result:
            raise ValueError(f"Table '{schema}.{table}' not found")

        return f'"{schema}"."{table}"'

    except Exception as e:
        logger.error(f"Table validation failed: {str(e)}")
        raise
