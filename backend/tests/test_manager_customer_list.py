from datetime import datetime, timezone

from app.routers import auth


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _CustomerDatabase:
    def __init__(self):
        joined = datetime(2026, 7, 24, tzinfo=timezone.utc)
        self.rows = [
            (1, "customer@example.com", True, False, "Real", "Customer", None, 2, 500, joined),
            (2, "manager@example.com", True, True, "Store", "Manager", None, 0, 0, joined),
        ]
        self.sql = ""

    def execute(self, statement):
        self.sql = str(statement)
        return _Result(self.rows)


def test_customer_section_excludes_manager_accounts():
    db = _CustomerDatabase()

    customers = auth.list_all_customers(db)

    assert "WHERE c.is_admin = false" in db.sql
    assert [customer["email"] for customer in customers] == [
        "customer@example.com"
    ]
    assert all(customer["is_manager"] is False for customer in customers)
