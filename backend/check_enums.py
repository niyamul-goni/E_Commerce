import psycopg2
conn = psycopg2.connect(
    "postgresql://postgres.ughxyivuhketqeuqcojg:256525riYad@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres",
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
