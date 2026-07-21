import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Add missing columns to products
    migrations = [
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_price NUMERIC(12,2)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description TEXT",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_trending BOOLEAN DEFAULT FALSE",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_new_arrival BOOLEAN DEFAULT FALSE",
    ]
    for sql in migrations:
        print(f"Running: {sql}")
        db.execute(text(sql))
    db.commit()
    print("\n[OK] All migrations applied successfully")

    # Verify
    cols = db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='products' ORDER BY ordinal_position"
    )).fetchall()
    print("\nProducts columns now:")
    for c in cols:
        print(f"  - {c[0]}")

    # Check reviews table
    print("\nReviews columns:")
    rev_cols = db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='reviews' ORDER BY ordinal_position"
    )).fetchall()
    for c in rev_cols:
        print(f"  - {c[0]}")

    # Check product_images table
    print("\nProduct_images columns:")
    img_cols = db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='product_images' ORDER BY ordinal_position"
    )).fetchall()
    for c in img_cols:
        print(f"  - {c[0]}")
finally:
    db.close()
