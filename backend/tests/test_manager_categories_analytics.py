from app.routers import analytics, catalog
from app.schemas import CategoryCreate, SubcategoryCreate


class _Result:
    def __init__(self, *, row=None, rows=None, scalar_value=None, mapping=None):
        self._row = row
        self._rows = rows or []
        self._scalar = scalar_value
        self._mapping = mapping

    def fetchone(self):
        return self._row

    def scalar(self):
        return self._scalar

    def mappings(self):
        return self

    def one(self):
        return self._mapping

    def all(self):
        return self._rows


class _CatalogDatabase:
    def __init__(self):
        self.statements = []
        self.committed = False
        self.rolled_back = False

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split())
        self.statements.append((sql, parameters or {}))
        if sql.startswith("LOCK TABLE"):
            return _Result()
        if sql.startswith("SELECT setval"):
            return _Result(scalar_value=10)
        if sql.startswith("SELECT id FROM categories WHERE slug"):
            return _Result(row=None)
        if sql.startswith("SELECT id FROM categories WHERE id"):
            return _Result(row=(2,))
        if sql.startswith("SELECT id FROM subcategories WHERE slug"):
            return _Result(row=None)
        if sql.startswith("INSERT INTO categories"):
            return _Result(mapping={
                "id": 11,
                "name": "New Category",
                "slug": "new-category",
                "description": None,
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            })
        if sql.startswith("INSERT INTO subcategories"):
            return _Result(mapping={
                "id": 11,
                "name": "New Subcategory",
                "slug": "new-subcategory",
                "category_id": 2,
                "description": None,
                "is_active": True,
                "sort_order": 0,
                "created_at": None,
                "updated_at": None,
            })
        raise AssertionError(f"Unexpected SQL in isolated test: {sql}")

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class _AnalyticsDatabase:
    def __init__(self):
        self.sql = ""
        self.parameters = {}

    def execute(self, statement, parameters=None):
        self.sql = " ".join(str(statement).split())
        self.parameters = parameters or {}
        return _Result(rows=[
            {
                "month_label": "2026-07",
                "order_count": 6,
                "total_revenue": 19772,
            },
            {
                "month_label": "2026-06",
                "order_count": 0,
                "total_revenue": 0,
            },
        ])


def test_category_create_repairs_stale_sequence_before_insert():
    db = _CatalogDatabase()

    result = catalog.create_category(
        CategoryCreate(name="New Category", is_active=True),
        db,
    )

    assert result["id"] == 11
    assert db.committed is True
    assert db.statements[0][0] == "LOCK TABLE categories IN SHARE ROW EXCLUSIVE MODE"
    assert db.statements[1][0].startswith("SELECT setval")


def test_manager_can_create_a_subcategory_with_sequence_protection():
    db = _CatalogDatabase()

    result = catalog.create_subcategory(
        SubcategoryCreate(category_id=2, name="New Subcategory"),
        db,
    )

    assert result["category_id"] == 2
    assert db.committed is True
    assert any(
        sql == "LOCK TABLE subcategories IN SHARE ROW EXCLUSIVE MODE"
        for sql, _ in db.statements
    )


def test_monthly_revenue_returns_a_complete_parameterized_month_axis():
    db = _AnalyticsDatabase()

    result = analytics.monthly_revenue(months=6, db=db)

    assert len(result) == 2
    assert db.parameters == {"months": 6}
    assert "generate_series" in db.sql
    assert "LEFT JOIN monthly_sales_view" in db.sql
    assert "ORDER BY axis.month_start DESC" in db.sql
