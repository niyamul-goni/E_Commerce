import sys
import logging
from sqlalchemy import text
from app.database import engine

with engine.begin() as conn:
    conn.execute(text("SELECT setval('suppliers_id_seq', COALESCE((SELECT MAX(id) FROM suppliers), 1))"))
    print('Sequence updated successfully.')
