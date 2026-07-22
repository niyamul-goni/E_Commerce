from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import auth


class _Result:
    def __init__(self, row=None, rows=None, scalar_value=None):
        self._row = row
        self._rows = rows or []
        self._scalar = scalar_value

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def scalar(self):
        return self._scalar


class _RoleDatabase:
    def __init__(self, role_row):
        self.role_row = role_row

    def execute(self, statement, parameters):
        assert "FROM customers" in str(statement)
        return _Result(row=self.role_row)


class _InventoryDatabase:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.updates = []

    def execute(self, statement, parameters=None):
        sql = str(statement)
        if "SELECT id FROM products" in sql:
            return _Result(row=(7,))
        if "FROM inventory inv" in sql and "FOR UPDATE" in sql:
            return _Result(rows=[(101, 12, 2), (102, 8, 3)])
        if "UPDATE inventory" in sql:
            self.updates.append(parameters)
            return _Result()
        raise AssertionError(f"Unexpected SQL in isolated test: {sql}")

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _credentials():
    return SimpleNamespace(username="manager@example.com", password="correct-password")


def test_manager_login_requires_database_manager_role(monkeypatch):
    monkeypatch.setattr(auth, "login_supabase_user", lambda **_: {"access_token": "safe-test-token"})

    response = auth.manager_login(_credentials(), _RoleDatabase((True, True)))
    assert response.access_token == "safe-test-token"

    with pytest.raises(HTTPException) as exc_info:
        auth.manager_login(_credentials(), _RoleDatabase((False, True)))
    assert exc_info.value.status_code == 403


def test_customer_login_rejects_manager_account(monkeypatch):
    monkeypatch.setattr(auth, "login_supabase_user", lambda **_: {"access_token": "safe-test-token"})

    with pytest.raises(HTTPException) as exc_info:
        auth.customer_login(_credentials(), _RoleDatabase((True, True)))
    assert exc_info.value.status_code == 403
    assert "manager login" in exc_info.value.detail.lower()


def test_inventory_reduction_preserves_reserved_stock():
    db = _InventoryDatabase()

    result = auth.update_inventory_level(
        product_id=7,
        payload=auth.ManagerInventoryUpdate(available_stock=4),
        db=db,
    )

    assert db.committed is True
    assert db.rolled_back is False
    assert db.updates == [
        {"amount": 10, "inventory_id": 101},
        {"amount": 1, "inventory_id": 102},
    ]
    assert result["available_stock"] == 4
    assert result["reserved_stock"] == 5
    assert result["total_stock"] == 9
    assert result["stock_status"] == "low_stock"
