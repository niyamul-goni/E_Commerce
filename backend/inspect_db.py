"""Inspect actual database schema for categories and products tables."""
from app.core.config import settings
from sqlalchemy import create_engine, inspect

e = create_engine(settings.DATABASE_URL, connect_args={"sslmode": "require"})
i = inspect(e)

tables = i.get_table_names()
print(f"Total tables: {len(tables)}")
print(f"Tables: {tables}\n")

for table_name in ["categories", "products", "suppliers", "customers", "orders"]:
    if table_name in tables:
        cols = i.get_columns(table_name)
        print(f"=== {table_name} ===")
        for c in cols:
            print(f"  {c['name']}: {c['type']}")
        print()
    else:
        print(f"=== {table_name} === NOT FOUND\n")
