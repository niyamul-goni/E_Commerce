import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
    print("=== Tables ===")
    for row in r:
        print(row[0])

    print()
    print("=== categories sample ===")
    r2 = conn.execute(text("SELECT id, name FROM categories LIMIT 5"))
    for row in r2:
        print(row)

    print()
    print("=== suppliers sample ===")
    r3 = conn.execute(text("SELECT id, name FROM suppliers LIMIT 5"))
    for row in r3:
        print(row)

    print()
    print("=== products columns ===")
    r4 = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='products' ORDER BY ordinal_position"))
    for row in r4:
        print(row[0])

    print()
    print("=== products count ===")
    r5 = conn.execute(text("SELECT COUNT(*) FROM products"))
    print(r5.scalar())
