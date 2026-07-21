import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    cols = db.execute(text(
        "SELECT column_name, data_type, udt_name FROM information_schema.columns "
        "WHERE table_name='orders' AND column_name='status'"
    )).fetchall()
    
    print("Orders 'status' column type:")
    for c in cols:
        print(f"  - {c}")
finally:
    db.close()
