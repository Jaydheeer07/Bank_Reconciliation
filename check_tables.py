from sqlalchemy import inspect
from app.database import engine

inspector = inspect(engine)
schemas = inspector.get_schema_names()

for schema in schemas:
    print(f"Schema: {schema}")
    for table_name in inspector.get_table_names(schema=schema):
        print(f"\nTable: {table_name}")
        for column in inspector.get_columns(table_name, schema=schema):
            print(f"Column: {column['name']}, Type: {column['type']}")
