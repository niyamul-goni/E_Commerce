"""
FashionHub — Product Images Router
Endpoints for listing, uploading, deleting, and bulk-uploading product images.
Works with the existing `product_images` table in the Supabase schema.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.core.product_image_storage import (
    ProductImageStorageError,
    delete_managed_product_image,
    store_product_image,
)
from app.database import get_db

router = APIRouter(prefix="/products", tags=["product-images"])

_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "products"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_IMAGE_TYPES = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("/{product_id}/images")
def list_product_images(product_id: int, db: Session = Depends(get_db)):
    """Return all images for a product, ordered by sort_order."""
    rows = db.execute(text("""
        SELECT id, image_url, alt_text, is_primary, sort_order
        FROM product_images
        WHERE product_id = :pid
        ORDER BY is_primary DESC, sort_order ASC, id ASC
    """), {"pid": product_id}).fetchall()
    return [
        {
            "id": r[0],
            "image_url": r[1],
            "alt_text": r[2],
            "is_primary": r[3],
            "sort_order": r[4],
        }
        for r in rows
    ]


@router.post(
    "/{product_id}/images",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Query(False),
    alt_text: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Upload an image for a product."""
    # Validate product exists
    exists = db.execute(
        text("SELECT id FROM products WHERE id = :pid"), {"pid": product_id}
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate extension
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    if file.content_type not in ALLOWED_IMAGE_TYPES[ext]:
        raise HTTPException(
            status_code=400,
            detail="The selected file's content type does not match its image extension.",
        )

    # Read and validate size
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The selected image is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5 MB.")

    try:
        image_url = await store_product_image(
            product_id=product_id,
            extension=ext,
            content=content,
            content_type=file.content_type,
            local_dir=_UPLOAD_DIR,
        )
    except ProductImageStorageError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        # If setting as primary, clear existing primary.
        if is_primary:
            db.execute(text(
                "UPDATE product_images SET is_primary = false WHERE product_id = :pid"
            ), {"pid": product_id})

        max_sort = db.execute(text(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM product_images WHERE product_id = :pid"
        ), {"pid": product_id}).scalar()

        result = db.execute(text(
            "INSERT INTO product_images (product_id, image_url, alt_text, is_primary, sort_order) "
            "VALUES (:pid, :url, :alt, :primary, :sort) RETURNING id"
        ), {
            "pid": product_id,
            "url": image_url,
            "alt": alt_text or f"Product {product_id} image",
            "primary": is_primary,
            "sort": max_sort,
        })
        db.commit()
        new_id = result.fetchone()[0]
    except Exception:
        db.rollback()
        await delete_managed_product_image(image_url, local_dir=_UPLOAD_DIR)
        raise

    return {"id": new_id, "image_url": image_url, "is_primary": is_primary, "message": "Image uploaded"}


@router.delete(
    "/{product_id}/images/{image_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    """Delete a product image."""
    row = db.execute(text(
        "SELECT id, image_url FROM product_images WHERE id = :iid AND product_id = :pid"
    ), {"iid": image_id, "pid": product_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Image not found")

    image_url = row[1]

    db.execute(text("DELETE FROM product_images WHERE id = :iid"), {"iid": image_id})
    db.commit()
    try:
        await delete_managed_product_image(image_url, local_dir=_UPLOAD_DIR)
    except (OSError, ProductImageStorageError):
        pass
    return {"message": "Image deleted"}
