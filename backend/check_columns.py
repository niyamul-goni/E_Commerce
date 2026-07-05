from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'customers' ORDER BY ordinal_position"
))
print("customers columns:", [row[0] for row in result.fetchall()])

result2 = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'products' ORDER BY ordinal_position"
))
print("products columns:", [row[0] for row in result2.fetchall()])

result3 = db.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'categories' ORDER BY ordinal_position"
))
print("categories columns:", [row[0] for row in result3.fetchall()])

db.close()
