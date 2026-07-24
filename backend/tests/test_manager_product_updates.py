import pytest
from fastapi import HTTPException

from app.routers import catalog
from app.schemas import ProductUpdate


class _Result:
    def __init__(self, *, row=None, rows=None, scalar_value=None):
        self._row = row
        self._rows = rows or []
        self._scalar = scalar_value

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def scalar(self):
        return self._scalar


class _UpdateDatabase:
    def __init__(self, *, conflict=False):
        self.conflict = conflict
        self.statements = []
        self.committed = False
        self.rolled_back = False

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split())
        self.statements.append((sql, parameters or {}))
        if sql.startswith("SELECT id, slug FROM products"):
            return _Result(row=(33, "easy-oversized-tee-bro-m"))
        if sql.startswith("SELECT id, sku FROM product_variants"):
            return _Result(row=(319, "easy-oversized-tee-bro-M"))
        if "WHERE lower(sku) = lower(:sku)" in sql:
            return _Result(row=(999,) if self.conflict else None)
        if sql.startswith("UPDATE products SET"):
            return _Result()
        if sql.startswith("UPDATE product_variants SET"):
            return _Result()
        raise AssertionError(f"Unexpected SQL in isolated test: {sql}")

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class _StockDatabase:
    def __init__(self):
        self.updates = []

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split())
        if sql.startswith("SELECT id FROM product_variants"):
            return _Result(scalar_value=319)
        if "FROM inventory inv" in sql and "FOR UPDATE" in sql:
            return _Result(rows=[(10, 12, 2), (11, 8, 3)])
        if sql.startswith("UPDATE inventory"):
            self.updates.append(parameters)
            return _Result()
        raise AssertionError(f"Unexpected SQL in isolated test: {sql}")


def test_product_edit_does_not_rewrite_unchanged_sku(monkeypatch):
    db = _UpdateDatabase()
    monkeypatch.setattr(catalog, "get_product", lambda product_id, db: {"id": product_id})

    result = catalog.update_product(
        33,
        ProductUpdate(name="Updated product name", sku="easy-oversized-tee-bro-M"),
        db,
    )

    assert result == {"id": 33}
    assert db.committed is True
    assert not any(sql.startswith("UPDATE product_variants") for sql, _ in db.statements)
    product_update = next(params for sql, params in db.statements if sql.startswith("UPDATE products SET"))
    assert product_update["name"] == "Updated product name"
    assert "slug" not in product_update


def test_product_edit_reports_a_specific_sku_conflict():
    db = _UpdateDatabase(conflict=True)

    with pytest.raises(HTTPException) as exc_info:
        catalog.update_product(
            33,
            ProductUpdate(sku="sku-owned-by-another-variant"),
            db,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "This SKU is already used by another product variant."
    assert db.committed is False
    assert not any(sql.startswith("UPDATE product_variants") for sql, _ in db.statements)


def test_product_stock_reduction_is_distributed_without_touching_reservations():
    db = _StockDatabase()

    catalog._set_product_stock(db, product_id=33, desired_stock=4, sku="primary-sku")

    assert db.updates == [
        {"amount": 10, "id": 10},
        {"amount": 1, "id": 11},
    ]
