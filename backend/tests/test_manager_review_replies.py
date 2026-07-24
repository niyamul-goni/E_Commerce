from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import auth


class _Result:
    def __init__(self, *, row=None, scalar_value=None):
        self._row = row
        self._scalar = scalar_value

    def fetchone(self):
        return self._row

    def scalar(self):
        return self._scalar


class _ReviewReplyDatabase:
    def __init__(self, *, review_exists=True, admin_active=True):
        self.review_exists = review_exists
        self.admin_active = admin_active
        self.statements = []
        self.committed = False
        self.rolled_back = False

    def execute(self, statement, parameters=None):
        sql = " ".join(str(statement).split())
        self.statements.append((sql, parameters or {}))
        if sql.startswith("SELECT id FROM reviews"):
            return _Result(row=(96,) if self.review_exists else None)
        if sql.startswith("INSERT INTO roles"):
            return _Result(scalar_value=3)
        if sql.startswith("INSERT INTO admins"):
            return _Result(row=(14, self.admin_active))
        if sql.startswith("INSERT INTO review_replies"):
            return _Result()
        raise AssertionError(f"Unexpected SQL in isolated test: {sql}")

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _manager():
    return SimpleNamespace(
        email="Manager@Example.com",
        first_name="Store",
        last_name="Manager",
        is_admin=True,
    )


def test_manager_reply_bootstraps_profile_and_upserts_reply():
    db = _ReviewReplyDatabase()

    result = auth.reply_to_review(
        review_id=96,
        payload=auth.ManagerReviewReply(reply_text="  Thank you for your feedback.  "),
        db=db,
        current_user=_manager(),
    )

    assert db.committed is True
    assert db.rolled_back is False
    assert result == {
        "message": "Reply saved",
        "review_id": 96,
        "reply_text": "Thank you for your feedback.",
        "has_reply": True,
    }
    admin_params = next(
        params for sql, params in db.statements if sql.startswith("INSERT INTO admins")
    )
    assert admin_params["email"] == "manager@example.com"
    assert admin_params["full_name"] == "Store Manager"
    reply_sql, reply_params = next(
        (sql, params)
        for sql, params in db.statements
        if sql.startswith("INSERT INTO review_replies")
    )
    assert "ON CONFLICT (review_id) DO UPDATE" in reply_sql
    assert reply_params == {
        "review_id": 96,
        "admin_id": 14,
        "body": "Thank you for your feedback.",
    }


def test_manager_reply_rejects_unknown_review_without_creating_profiles():
    db = _ReviewReplyDatabase(review_exists=False)

    with pytest.raises(HTTPException) as exc_info:
        auth.reply_to_review(
            review_id=999,
            payload=auth.ManagerReviewReply(reply_text="Thanks"),
            db=db,
            current_user=_manager(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Review not found"
    assert db.rolled_back is True
    assert not any(sql.startswith("INSERT INTO roles") for sql, _ in db.statements)


def test_manager_reply_does_not_reactivate_an_inactive_admin_profile():
    db = _ReviewReplyDatabase(admin_active=False)

    with pytest.raises(HTTPException) as exc_info:
        auth.reply_to_review(
            review_id=96,
            payload=auth.ManagerReviewReply(reply_text="Thanks"),
            db=db,
            current_user=_manager(),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "This manager profile is inactive"
    assert db.rolled_back is True
    assert db.committed is False
