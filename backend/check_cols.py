from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

# Check products table columns
result = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'products' AND table_schema = 'public' "
    "ORDER BY ordinal_position"
))
print("products columns:", [r[0] for r in result])

# Check categories table columns
result = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'categories' AND table_schema = 'public' "
    "ORDER BY ordinal_position"
))
print("categories columns:", [r[0] for r in result])

# Check customers table columns
result = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'customers' AND table_schema = 'public' "
    "ORDER BY ordinal_position"
))
print("customers columns:", [r[0] for r in result])

db.close()
