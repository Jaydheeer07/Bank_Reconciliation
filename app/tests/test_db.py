import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine
from app.scheduled_tasks.statement_processor import fetch_statements

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test if we can connect to the database and execute a simple query."""
    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            logger.info("Database connection successful!")
            logger.info("[SUCCESS] Database connection successful!")
            logger.info(f"Connected to database: {db_info[0]}")
            logger.info(f"Connected as user: {db_info[1]}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def check_table_structure(db: Session, table_name: str):
    """Check if the table exists and show its structure."""
    try:
        # Check if table exists in any schema
        query = text("""
            SELECT schemaname, tablename 
            FROM pg_catalog.pg_tables 
            WHERE tablename = :table_name;
        """)
        result = db.execute(query, {"table_name": table_name}).fetchall()
        
        if result:
            for row in result:
                schema_name = row.schemaname
                logger.info(f"Table '{table_name}' exists in schema '{schema_name}'")
                
                # Get table structure
                query = text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = :schema_name 
                    AND table_name = :table_name
                    ORDER BY ordinal_position;
                """)
                columns = db.execute(query, {
                    "schema_name": schema_name,
                    "table_name": table_name
                }).fetchall()
                
                logger.info(f"Table structure in schema '{schema_name}':")
                for col in columns:
                    logger.info(f"  {col.column_name}: {col.data_type}")
                
                # Also check row count
                count_query = text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
                count = db.execute(count_query).scalar()
                logger.info(f"Total rows in table: {count}")
                
                return schema_name
        else:
            logger.error(f"Table '{table_name}' does not exist in any schema")
            return None
            
    except Exception as e:
        logger.error(f"Error checking table structure: {str(e)}", exc_info=True)
        return None

def list_all_tables(db: Session):
    """List all tables in the database."""
    try:
        query = text("""
            SELECT schemaname, tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename;
        """)
        result = db.execute(query).fetchall()
        
        logger.info("\nAvailable tables in database:")
        for row in result:
            logger.info(f"  {row.schemaname}.{row.tablename}")
            
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}", exc_info=True)

async def test_fetch_statements():
    """Test if we can fetch statements from a specified table."""
    try:
        # Create a database session
        with Session(engine) as db:
            # Remove quotes if present in the table name
            raw_table_name = 'data_f5ad9e2d-f491-4350-b0e7-683b51f7599b_democompanyglobal'
            
            # Get the schema name first
            schema_name = check_table_structure(db, raw_table_name)
            if not schema_name:
                logger.error("Could not find table in any schema")
                return None
                
            # Use fully qualified table name with proper quoting
            full_table_name = f'"{schema_name}"."{raw_table_name}"'
            logger.info(f"Using fully qualified table name: {full_table_name}")
            
            try:
                statements = await fetch_statements(db, full_table_name)
                
                if statements:
                    logger.info(f"\nSuccessfully fetched {len(statements)} statements")
                    logger.info("First statement details:")
                    # Only show the first statement to avoid overwhelming output
                    if len(statements) > 0:
                        for key, value in statements[0].items():
                            logger.info(f"  {key}: {value}")
                        if len(statements) > 1:
                            logger.info(f"... and {len(statements)-1} more statements")
                else:
                    logger.info("No statements found in the table")
                
                return statements
            except Exception as e:
                logger.error(f"Error in fetch_statements: {str(e)}", exc_info=True)
                return None
                
    except Exception as e:
        logger.error(f"Error in test_fetch_statements: {str(e)}", exc_info=True)
        return None

async def main():
    logger.info("Testing database connection...")
    test_database_connection()
    
    with Session(engine) as db:
        logger.info("\nListing all tables...")
        list_all_tables(db)
    
    logger.info("\nTesting fetch statements...")
    await test_fetch_statements()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
