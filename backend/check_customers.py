from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text(
    "SELECT column_name, data_type FROM information_schema.columns "
    "WHERE table_name='customers' ORDER BY ordinal_position"
))
cols = result.fetchall()
print("=== customers table columns ===")
for c in cols:
    print(f"  {c[0]} - {c[1]}")
db.close()
