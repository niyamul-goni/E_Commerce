"""Run seed_products.sql against the Supabase database - statement by statement."""
import sys
from pathlib import Path
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

SEED_FILE = Path(__file__).resolve().parent.parent / "database" / "seed_products.sql"

db = SessionLocal()
try:
    sql = SEED_FILE.read_text(encoding="utf-8")
    
    # Split into statements and run each one
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    errors = []
    executed = 0
    
    for i, stmt in enumerate(statements):
        # Skip BEGIN/COMMIT/comments
        clean = stmt.strip()
        if not clean or clean.startswith('--') or clean.upper() in ('BEGIN', 'COMMIT'):
            continue
        try:
            db.execute(text(clean))
            executed += 1
        except Exception as e:
            err_msg = str(e).split('\n')[0][:120]
            if 'duplicate' in err_msg.lower() or 'already exists' in err_msg.lower() or 'unique' in err_msg.lower():
                pass  # OK — ON CONFLICT DO NOTHING should handle this
            else:
                errors.append(f"Statement {i}: {err_msg}")
                db.rollback()
                # Start a new transaction for next statements
                continue
    
    db.commit()
    
    # Verify
    count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
    imgs = db.execute(text("SELECT COUNT(*) FROM product_images")).scalar()
    variants = db.execute(text("SELECT COUNT(*) FROM product_variants")).scalar()
    reviews = db.execute(text("SELECT COUNT(*) FROM reviews")).scalar()
    brands = db.execute(text("SELECT COUNT(*) FROM brands")).scalar()
    cats = db.execute(text("SELECT COUNT(*) FROM categories")).scalar()
    print(f"[OK] Database seeded ({executed} statements):")
    print(f"  Brands:     {brands}")
    print(f"  Categories: {cats}")
    print(f"  Products:   {count}")
    print(f"  Images:     {imgs}")
    print(f"  Variants:   {variants}")
    print(f"  Reviews:    {reviews}")
    
    if errors:
        print(f"\n[WARN] {len(errors)} errors:")
        for e in errors[:10]:
            print(f"  {e}")
except Exception as e:
    db.rollback()
    print(f"[ERROR] {e}")
    raise
finally:
    db.close()
