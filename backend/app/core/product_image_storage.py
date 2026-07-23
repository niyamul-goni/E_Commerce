from __future__ import annotations

import uuid
from pathlib import Path
from urllib.parse import quote, unquote

import httpx

from app.core.config import settings


class ProductImageStorageError(RuntimeError):
    """Raised when an image cannot be stored in the configured backend."""


def _supabase_storage_enabled() -> bool:
    if settings.PRODUCT_IMAGE_STORAGE == "local":
        return False

    configured = bool(
        settings.SUPABASE_URL
        and settings.SUPABASE_SERVICE_ROLE_KEY
        and settings.SUPABASE_STORAGE_BUCKET
    )
    if settings.PRODUCT_IMAGE_STORAGE == "supabase" and not configured:
        raise ProductImageStorageError(
            "Supabase image storage is selected, but its URL, service role key, "
            "or storage bucket is not configured."
        )
    return configured


def _supabase_headers(*, content_type: str = "application/json") -> dict[str, str]:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": content_type,
    }


def _supabase_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"Supabase Storage returned HTTP {response.status_code}"

    if isinstance(payload, dict):
        for field in ("message", "error", "statusCode"):
            if payload.get(field):
                return str(payload[field])
    return str(payload)


async def _ensure_public_bucket(client: httpx.AsyncClient) -> None:
    base_url = settings.SUPABASE_URL.rstrip("/")
    bucket = settings.SUPABASE_STORAGE_BUCKET
    bucket_url = f"{base_url}/storage/v1/bucket/{quote(bucket, safe='')}"

    response = await client.get(bucket_url, headers=_supabase_headers())
    if response.status_code == 200:
        payload = response.json()
        if not payload.get("public", False):
            raise ProductImageStorageError(
                f'Supabase Storage bucket "{bucket}" exists but is private. '
                "Make it public so storefront product images can be displayed."
            )
        return

    bucket_missing = (
        response.status_code in {400, 404}
        and "not found" in _supabase_error(response).lower()
    )
    if not bucket_missing:
        raise ProductImageStorageError(
            f"Could not inspect Supabase Storage bucket: {_supabase_error(response)}"
        )

    create_response = await client.post(
        f"{base_url}/storage/v1/bucket",
        headers=_supabase_headers(),
        json={
            "id": bucket,
            "name": bucket,
            "public": True,
            "file_size_limit": 5 * 1024 * 1024,
            "allowed_mime_types": [
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
            ],
        },
    )
    if create_response.status_code not in {200, 201}:
        # A concurrent request may have created it between GET and POST.
        retry = await client.get(bucket_url, headers=_supabase_headers())
        if retry.status_code != 200 or not retry.json().get("public", False):
            raise ProductImageStorageError(
                f"Could not create Supabase Storage bucket: "
                f"{_supabase_error(create_response)}"
            )


async def store_product_image(
    *,
    product_id: int,
    extension: str,
    content: bytes,
    content_type: str,
    local_dir: Path,
) -> str:
    """Store an image and return the durable URL saved in product_images."""
    unique_name = f"{product_id}_{uuid.uuid4().hex}{extension}"

    if not _supabase_storage_enabled():
        local_dir.mkdir(parents=True, exist_ok=True)
        file_path = local_dir / unique_name
        file_path.write_bytes(content)
        return f"/static/products/{unique_name}"

    base_url = settings.SUPABASE_URL.rstrip("/")
    bucket = settings.SUPABASE_STORAGE_BUCKET
    object_name = f"products/{unique_name}"
    encoded_bucket = quote(bucket, safe="")
    encoded_object = quote(object_name, safe="/")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            await _ensure_public_bucket(client)
            response = await client.post(
                f"{base_url}/storage/v1/object/{encoded_bucket}/{encoded_object}",
                headers={
                    **_supabase_headers(content_type=content_type),
                    "x-upsert": "false",
                },
                content=content,
            )
    except httpx.HTTPError as exc:
        raise ProductImageStorageError(
            "Could not connect to Supabase Storage while uploading the image."
        ) from exc

    if response.status_code not in {200, 201}:
        raise ProductImageStorageError(
            f"Supabase Storage upload failed: {_supabase_error(response)}"
        )

    return (
        f"{base_url}/storage/v1/object/public/"
        f"{encoded_bucket}/{encoded_object}"
    )


async def delete_managed_product_image(image_url: str | None, *, local_dir: Path) -> None:
    """Delete only images managed by this application; ignore all other URLs."""
    if not image_url:
        return

    if image_url.startswith("/static/products/"):
        candidate = local_dir / Path(image_url).name
        try:
            candidate.relative_to(local_dir)
        except ValueError:
            return
        candidate.unlink(missing_ok=True)
        return

    if not _supabase_storage_enabled():
        return

    base_url = settings.SUPABASE_URL.rstrip("/")
    bucket = settings.SUPABASE_STORAGE_BUCKET
    public_prefix = (
        f"{base_url}/storage/v1/object/public/{quote(bucket, safe='')}/"
    )
    if not image_url.startswith(public_prefix):
        return

    object_name = unquote(image_url[len(public_prefix):])
    if not object_name.startswith("products/"):
        return

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.delete(
                f"{base_url}/storage/v1/object/"
                f"{quote(bucket, safe='')}/{quote(object_name, safe='/')}",
                headers=_supabase_headers(),
            )
    except httpx.HTTPError:
        # Cleanup happens after the database has been made consistent. A
        # transient object deletion failure must not turn a valid upload into
        # an apparent failure for the manager.
        return
