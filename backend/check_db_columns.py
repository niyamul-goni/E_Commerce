import psycopg2
from app.core.config import settings

conn = psycopg2.connect(
    settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"),
    sslmode="require",
)
cur = conn.cursor()

# Check customers table columns
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name='customers' AND table_schema='public'
    ORDER BY ordinal_position
""")
print("=== CUSTOMERS TABLE COLUMNS ===")
for r in cur.fetchall():
    print(r)

# Check if customer_profiles table exists
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public' AND table_name='customer_profiles'
""")
result = cur.fetchall()
print(f"\n=== customer_profiles table exists: {bool(result)} ===")
if result:
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name='customer_profiles' AND table_schema='public'
        ORDER BY ordinal_position
    """)
    for r in cur.fetchall():
        print(r)

# Check if review_replies table exists
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public' AND table_name='review_replies'
""")
result = cur.fetchall()
print(f"\n=== review_replies table exists: {bool(result)} ===")

# List all public tables
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public' AND table_type='BASE TABLE'
    ORDER BY table_name
""")
print("\n=== ALL PUBLIC TABLES ===")
for r in cur.fetchall():
    print(r[0])

conn.close()
