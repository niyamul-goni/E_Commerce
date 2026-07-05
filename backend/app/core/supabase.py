from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class SupabaseAuthError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _base_url() -> str:
    if not settings.SUPABASE_URL:
        raise SupabaseAuthError("Supabase URL is not configured", 503)
    return settings.SUPABASE_URL.rstrip("/")


def _header_value(key: str) -> dict[str, str]:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Supabase request failed"

    for field in ("msg", "error_description", "message"):
        detail = payload.get(field)
        if detail:
            return str(detail)
    return str(payload)


def create_supabase_user(*, email: str, password: str, user_metadata: dict[str, Any]) -> dict[str, Any]:
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise SupabaseAuthError("Supabase service role key is not configured", 503)

    response = httpx.post(
        f"{_base_url()}/auth/v1/admin/users",
        headers=_header_value(settings.SUPABASE_SERVICE_ROLE_KEY),
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": user_metadata,
        },
        timeout=15.0,
    )
    if response.status_code not in (200, 201):
        raise SupabaseAuthError(_error_detail(response), response.status_code)
    return response.json()


def login_supabase_user(*, email: str, password: str) -> dict[str, Any]:
    if not settings.SUPABASE_ANON_KEY:
        raise SupabaseAuthError("Supabase anon key is not configured", 503)

    response = httpx.post(
        f"{_base_url()}/auth/v1/token?grant_type=password",
        headers=_header_value(settings.SUPABASE_ANON_KEY),
        json={"email": email, "password": password},
        timeout=15.0,
    )
    if response.status_code != 200:
        raise SupabaseAuthError(_error_detail(response), response.status_code)
    return response.json()


def get_supabase_user(access_token: str) -> dict[str, Any]:
    if not settings.SUPABASE_ANON_KEY:
        raise SupabaseAuthError("Supabase anon key is not configured", 503)

    response = httpx.get(
        f"{_base_url()}/auth/v1/user",
        headers={
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=15.0,
    )
    if response.status_code != 200:
        raise SupabaseAuthError(_error_detail(response), response.status_code)
    return response.json()