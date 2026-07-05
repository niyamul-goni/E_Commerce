"""Inspect what tables and columns currently exist in Supabase"""
import sys, os
sys.path.insert(0, '.')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL, connect_args={'sslmode': 'require'}, pool_pre_ping=True)

with engine.connect() as conn:
    # Tables
    tables_result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"
    ))
    tables = [r[0] for r in tables_result]
    print(f"=== Tables in Supabase ({len(tables)}) ===")
    for t in tables:
        print(f"  - {t}")

    print()

    # Check columns of 'categories' to see old vs new schema
    if 'categories' in tables:
        col_result = conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='categories' ORDER BY ordinal_position"
        ))
        print("=== categories columns ===")
        for row in col_result:
            print(f"  {row[0]}: {row[1]}")
