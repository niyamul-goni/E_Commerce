from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.supabase import SupabaseAuthError
from app.routers import auth


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Database:
    def __init__(self, row=None, error=None):
        self.row = row
        self.error = error
        self.queries = []

    def execute(self, statement, parameters=None):
        self.queries.append((str(statement), parameters))
        if self.error:
            raise self.error
        return _Result(self.row)


def _credentials(email="customer@example.com", password="customer-password"):
    return SimpleNamespace(username=email, password=password)


def _registration(email="customer@example.com"):
    return SimpleNamespace(
        first_name="Customer",
        last_name="Example",
        email=email,
        phone=None,
        password="customer-password",
    )


def _raised_http_error(call):
    with pytest.raises(HTTPException) as exc_info:
        call()
    return exc_info.value


def test_registration_existing_customer_returns_exact_conflict(monkeypatch):
    monkeypatch.setattr(
        auth,
        "create_supabase_user",
        lambda **_: pytest.fail("Supabase must not be called for an existing customer"),
    )

    error = _raised_http_error(
        lambda: auth.register(_registration(), _Database(row=(17,)))
    )

    assert error.status_code == 409
    assert error.detail == auth.REGISTRATION_EMAIL_EXISTS


def test_registration_supabase_duplicate_returns_same_exact_conflict(monkeypatch):
    def duplicate_user(**_):
        raise SupabaseAuthError(
            "A user with this email address has already been registered",
            422,
        )

    monkeypatch.setattr(auth, "create_supabase_user", duplicate_user)

    error = _raised_http_error(
        lambda: auth.register(_registration(), _Database(row=None))
    )

    assert error.status_code == 409
    assert error.detail == auth.REGISTRATION_EMAIL_EXISTS


def test_registration_database_failure_is_safe_generic_500():
    error = _raised_http_error(
        lambda: auth.register(
            _registration(),
            _Database(error=RuntimeError("private database detail")),
        )
    )

    assert error.status_code == 500
    assert error.detail == auth.CUSTOMER_AUTH_SERVER_ERROR
    assert "private database detail" not in error.detail


def test_customer_login_unknown_email_returns_exact_401(monkeypatch):
    monkeypatch.setattr(
        auth,
        "login_supabase_user",
        lambda **_: pytest.fail("Supabase must not be called for an unknown email"),
    )

    error = _raised_http_error(
        lambda: auth.customer_login(_credentials(), _Database(row=None))
    )

    assert error.status_code == 401
    assert error.detail == auth.CUSTOMER_EMAIL_NOT_FOUND
    assert error.headers == {"WWW-Authenticate": "Bearer"}


def test_customer_login_wrong_password_returns_exact_401(monkeypatch):
    def wrong_password(**_):
        raise SupabaseAuthError("Invalid login credentials", 400)

    monkeypatch.setattr(auth, "login_supabase_user", wrong_password)

    error = _raised_http_error(
        lambda: auth.customer_login(
            _credentials(password="wrong-password"),
            _Database(row=(False, True)),
        )
    )

    assert error.status_code == 401
    assert error.detail == auth.CUSTOMER_INCORRECT_PASSWORD
    assert error.headers == {"WWW-Authenticate": "Bearer"}


def test_customer_login_disabled_account_returns_exact_403(monkeypatch):
    monkeypatch.setattr(
        auth,
        "login_supabase_user",
        lambda **_: pytest.fail("Disabled accounts must be rejected before Supabase"),
    )

    error = _raised_http_error(
        lambda: auth.customer_login(
            _credentials(),
            _Database(row=(False, False)),
        )
    )

    assert error.status_code == 403
    assert error.detail == auth.CUSTOMER_ACCOUNT_DISABLED


@pytest.mark.parametrize(
    "failure",
    [
        SupabaseAuthError("upstream unavailable", 503),
        RuntimeError("unexpected private detail"),
    ],
)
def test_customer_login_unexpected_auth_failure_is_safe_generic_500(
    monkeypatch,
    failure,
):
    def fail_login(**_):
        raise failure

    monkeypatch.setattr(auth, "login_supabase_user", fail_login)

    error = _raised_http_error(
        lambda: auth.customer_login(
            _credentials(),
            _Database(row=(False, True)),
        )
    )

    assert error.status_code == 500
    assert error.detail == auth.CUSTOMER_AUTH_SERVER_ERROR


def test_customer_login_database_failure_is_safe_generic_500():
    error = _raised_http_error(
        lambda: auth.customer_login(
            _credentials(),
            _Database(error=RuntimeError("private database detail")),
        )
    )

    assert error.status_code == 500
    assert error.detail == auth.CUSTOMER_AUTH_SERVER_ERROR


def test_customer_login_success_and_legacy_alias(monkeypatch):
    monkeypatch.setattr(
        auth,
        "login_supabase_user",
        lambda **_: {"access_token": "customer-test-token"},
    )
    db = _Database(row=(False, True))

    customer_response = auth.customer_login(_credentials(), db)
    legacy_response = auth.login(_credentials(), db)

    assert customer_response.access_token == "customer-test-token"
    assert legacy_response.access_token == "customer-test-token"


def test_manager_login_supabase_error_behavior_is_unchanged(monkeypatch):
    def manager_failure(**_):
        raise SupabaseAuthError("Original manager authentication response", 418)

    monkeypatch.setattr(auth, "login_supabase_user", manager_failure)

    error = _raised_http_error(
        lambda: auth.manager_login(_credentials(), _Database(row=(True, True)))
    )

    assert error.status_code == 418
    assert error.detail == "Original manager authentication response"
