import asyncio
import logging
from functools import partial
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.utils.http_client import post_json
from app.config import settings

logger = logging.getLogger(__name__)


async def fetch_statements(db: Session, tenant_id: str) -> List[Dict[Any, Any]]:
    """
    Fetches statements from the 'statements' table in the database.
    Args:
        db: Database session
        tenant_id: ID of the tenant to fetch statements for
    """
    try:
        logger.info(f"Attempting to fetch statements for tenant: {tenant_id}")

        # SQL query to fetch required columns
        query = text(
            """
            SELECT 
                client_name,
                account_name,
                transaction_date,
                payee,
                particulars,
                received,
                file_name
            FROM statements
            WHERE tenant_id = :tenant_id
            """
        )

        # Execute query with tenant_id parameter
        result = db.execute(query, {"tenant_id": tenant_id})

        # Convert to list of dictionaries
        statements = []
        for row in result:
            statement = {
                "client_name": row.client_name,
                "account_name": row.account_name,
                "transaction_date": row.transaction_date.isoformat()
                if row.transaction_date
                else None,
                "payee": row.payee,
                "particulars": row.particulars,
                "received": float(row.received) if row.received else 0.0,
                "file_name": row.file_name,
            }
            statements.append(statement)

        logger.info(
            f"Successfully fetched {len(statements)} statements for tenant: {tenant_id}"
        )
        return statements

    except Exception as e:
        logger.error(
            f"Error fetching statements for tenant: {tenant_id}: {str(e)}",
            exc_info=True,
        )
        raise


async def process_bank_statements(brain_id: str, tenant_id: str, db: Session):
    """
    Fetches statements from database and processes them through the brain API.
    """
    try:
        logger.info(f"Starting statement processing for brain_id: {brain_id}, tenant_id: {tenant_id}")

        # Fetch statements from database
        statements = await fetch_statements(db, tenant_id)

        # Log the number of statements fetched
        num_statements = len(statements)
        logger.info(f"Fetched {num_statements} statements for tenant: {tenant_id}")

        if not statements:
            logger.info("No statements found to process")
            return

        # Process the statements through the Xero processing endpoint
        payload = {
            "data": statements,
            "brainId": brain_id,
            "documentType": "statement"
        }
        
        # Send the request to the Xero processing endpoint
        result = await post_json(
            f"{settings.brain_base_url}/v1/file/xero/process",
            json=payload,
            log_message="process bank statements",
        )
        
        logger.info(
            f"Successfully processed {num_statements} statements for brain_id: {brain_id}, tenant_id: {tenant_id}"
        )
        logger.info(f"Brain API response: {result}")
        return result

    except Exception as e:
        logger.error(f"Error processing statements: {str(e)}", exc_info=True)


def process_bank_statements_wrapper(brain_id: str, tenant_id: str, db: Session):
    """
    Wrapper function to properly handle async execution in background threads.
    """
    loop = None
    thread_db = None
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create a new database session for this thread
        SessionLocal = sessionmaker(bind=db.bind, autocommit=False, autoflush=False)
        thread_db = SessionLocal()

        try:
            # Create partial function with args
            coro = partial(process_bank_statements, brain_id, tenant_id, thread_db)

            # Run with timeout to prevent hanging
            future = asyncio.wait_for(coro(), timeout=300)  # 5 minute timeout
            result = loop.run_until_complete(future)
            return result
        finally:
            # Close the thread-specific database session
            if thread_db:
                thread_db.close()
                
            # Make sure we clean up properly
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    except asyncio.TimeoutError:
        logger.error(f"Statement processing timed out for brain_id: {brain_id}, tenant_id: {tenant_id}")
    except Exception as e:
        logger.error(f"Error processing statements: {str(e)}", exc_info=True)
    finally:
        # Ensure the database session is closed
        if thread_db:
            try:
                thread_db.close()
            except Exception:
                pass
                
        # Ensure the loop is properly cleaned up
        if loop and not loop.is_closed():
            try:
                if loop.is_running():
                    loop.stop()
                loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {str(e)}")
