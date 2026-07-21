from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    print(db.execute(text("SELECT COUNT(*) FROM coupons")).fetchone())
except Exception as e:
    print("Error:", e)
