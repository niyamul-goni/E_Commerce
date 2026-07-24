import pytest
from fastapi import HTTPException

from app.routers import commerce


class _Result:
    def __init__(self, row=None, scalar_value=None):
        self._row = row
        self._scalar = scalar_value

    def fetchone(self):
        return self._row

    def scalar(self):
        return self._scalar

    def scalar_one(self):
        if self._scalar is None:
            raise AssertionError("Expected a scalar result")
        return self._scalar


class _OrderDatabase:
    def __init__(self, current_status="confirmed"):
        self.current_status = current_status
        self.transitions = []
        self.queries = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.queries.append((sql, parameters))

        if "SELECT status::text FROM orders" in sql:
            return _Result(scalar_value=self.current_status)
        if "UPDATE orders" in sql and "RETURNING id" in sql:
            self.current_status = parameters["status"]
            self.transitions.append(self.current_status)
            return _Result(row=(parameters["oid"],))
        if "INSERT INTO shipments" in sql:
            return _Result(scalar_value=701)
        if "UPDATE payments" in sql:
            return _Result()

        raise AssertionError(f"Unexpected SQL in isolated test: {sql}")

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_all_manager_fulfillment_statuses_work_in_sequence():
    db = _OrderDatabase("confirmed")

    for expected_status in (
        "packed",
        "shipped",
        "delivered",
        "returned",
        "refunded",
    ):
        response = commerce.change_order_status(
            order_id=25,
            status_in={"status": expected_status},
            db=db,
        )
        assert response["status"] == expected_status
        assert response["allowed_statuses"][0] == expected_status

    assert db.transitions == [
        "packed",
        "shipped",
        "delivered",
        "returned",
        "refunded",
    ]
    assert db.commits == 5
    assert any("UPDATE payments" in sql for sql, _ in db.queries)


def test_manager_cannot_skip_an_order_transition():
    db = _OrderDatabase("confirmed")

    with pytest.raises(HTTPException) as exc_info:
        commerce.change_order_status(
            order_id=25,
            status_in={"status": "delivered"},
            db=db,
        )

    assert exc_info.value.status_code == 409
    assert "available next status" in exc_info.value.detail
    assert db.current_status == "confirmed"
    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.parametrize(
    ("current_status", "expected_options"),
    [
        ("confirmed", ["confirmed", "packed", "cancelled"]),
        ("packed", ["packed", "shipped", "cancelled"]),
        ("shipped", ["shipped", "delivered", "returned"]),
        ("delivered", ["delivered", "returned"]),
        ("returned", ["returned", "refunded"]),
        ("refunded", ["refunded"]),
    ],
)
def test_api_returns_only_valid_manager_status_options(
    current_status,
    expected_options,
):
    assert commerce._allowed_order_statuses(current_status) == expected_options


def test_in_transit_shipment_advances_confirmed_order_to_shipped():
    db = _OrderDatabase("confirmed")

    response = commerce.create_shipment_endpoint(
        {
            "order_id": 25,
            "tracking_number": "TRACK-25",
            "carrier": "Test Carrier",
            "status": "in_transit",
        },
        db=db,
    )

    assert response["shipment_status"] == "in_transit"
    assert response["order_status"] == "shipped"
    assert db.transitions == ["packed", "shipped"]
    assert db.current_status == "shipped"
    assert db.commits == 1
