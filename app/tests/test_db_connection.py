import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine
from app.core.deps import get_db

# Import your existing components
from app.scheduled_tasks.statement_processor import fetch_statements
from app.utils.database.statement_utils import get_validated_table_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test")


@router.get("/db-connection")
async def test_db_connection():
    """Test endpoint to verify database connection configuration."""
    logger.info(f"Attempting to connect with DATABASE_URL: {engine.url}")
    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            logger.info("Database connection successful!")
            logger.info(f"Connected to database: {db_info[0]}")
            logger.info(f"Connected as user: {db_info[1]}")
            return {
                "status": "success",
                "message": "Database connection successful",
                "database": db_info[0],
                "user": db_info[1],
            }
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}


@router.get("/db-operations")
async def test_db_operations(db: Session = Depends(get_db)):
    """Test endpoint to verify database operations with automatic rollback."""
    try:
        # Start a transaction that will be rolled back
        with db.begin():
            # Test create operation
            db.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, test_column TEXT)"
                )
            )

            # Test insert operation
            db.execute(
                text("INSERT INTO test_table (test_column) VALUES ('test_value')")
            )

            # Test select operation
            result = db.execute(text("SELECT * FROM test_table"))
            test_data = result.fetchall()

            # Test update operation
            db.execute(
                text(
                    "UPDATE test_table SET test_column = 'updated_value' WHERE test_column = 'test_value'"
                )
            )

            # Get the results of our operations
            final_result = db.execute(text("SELECT * FROM test_table")).fetchall()

            return {
                "status": "success",
                "message": "All database operations successful (changes will be rolled back)",
                "operations": {
                    "create": "Created test_table",
                    "insert": "Inserted test record",
                    "select": [dict(row._mapping) for row in test_data],
                    "update": "Updated test record",
                    "final_state": [dict(row._mapping) for row in final_result],
                },
            }
            # Transaction will be automatically rolled back when the context exits

    except Exception as e:
        logger.error(f"Database operations failed: {str(e)}")
        return {"status": "error", "message": f"Database operations failed: {str(e)}"}


@router.get("/fetch-statements", response_model=Dict[str, Any])
async def test_fetch_statements_endpoint(
    table_name: str = Query(
        ...,
        min_length=3,
        max_length=63,
        example="public.data_f5ad9e2d_democompanyglobal",
        description="Table name in format schema.table",
    ),
    limit: int = Query(5, gt=0, le=100),
    db: Session = Depends(get_db),
):
    """
    Test endpoint to fetch statements from specified table
    """
    try:
        # Validate and sanitize table name
        full_table_name = await get_validated_table_name(db, table_name)

        # Fetch statements with optional limit for testing
        statements = await fetch_statements(db, full_table_name)

        return {
            "success": True,
            "table": full_table_name,
            "count": len(statements),
            "sample": statements[:limit],
            "schema": {
                "client_name": "string",
                "account_name": "string",
                "transaction_date": "date",
                "payee": "string",
                "particulars": "string",
                "received": "float",
                "file_name": "string",
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "suggestion": "Check table name format and existence",
            },
        )
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Database operation failed",
                "suggestion": "Check server logs for details",
            },
        )
