import psycopg2
from app.core.config import settings
conn = psycopg2.connect(
    settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"),
    sslmode="require",
)
cur = conn.cursor()
cur.execute("""
    SELECT t.typname, e.enumlabel
    FROM pg_enum e 
    JOIN pg_type t ON e.enumtypid = t.oid 
    ORDER BY t.typname, e.enumsortorder
""")
for r in cur.fetchall():
    print(f"{r[0]:30s} {r[1]}")
conn.close()
