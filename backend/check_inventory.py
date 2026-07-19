"""Check product variants and inventory, then populate if missing."""
import psycopg2
import random

conn = psycopg2.connect(
    "postgresql://postgres.ughxyivuhketqeuqcojg:256525riYad@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres",
    sslmode="require",
)
cur = conn.cursor()

# Check what tables have data
for table in ['products', 'product_variants', 'inventory', 'colors', 'sizes']:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"{table}: {cur.fetchone()[0]} rows")

# Check products
cur.execute("SELECT id, name, base_price, is_active FROM products ORDER BY id LIMIT 10")
products = cur.fetchall()
print(f"\nSample products:")
for p in products:
    print(f"  ID={p[0]}, name={p[1]}, price={p[2]}, active={p[3]}")

# Check colors and sizes
cur.execute("SELECT id, name FROM colors ORDER BY id")
colors = cur.fetchall()
print(f"\nColors: {colors}")

cur.execute("SELECT id, name, category FROM sizes ORDER BY id")
sizes = cur.fetchall()
print(f"\nSizes: {sizes}")

conn.close()
