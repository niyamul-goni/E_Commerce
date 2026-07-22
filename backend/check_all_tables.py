import psycopg2
from app.core.config import settings

conn = psycopg2.connect(
    settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"),
    sslmode="require",
)
cur = conn.cursor()

# Check cart_items table columns
tables_to_check = ['cart_items', 'carts', 'reviews', 'orders', 'order_items', 'payments', 'shipments', 'wishlist_items', 'wishlists']

for table in tables_to_check:
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name=%s AND table_schema='public'
        ORDER BY ordinal_position
    """, (table,))
    rows = cur.fetchall()
    if rows:
        print(f"\n=== {table} ===")
        for r in rows:
            print(f"  {r[0]:25s} {r[1]:25s} nullable={r[2]}")

conn.close()
