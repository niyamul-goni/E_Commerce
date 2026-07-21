"""
FashionHub — Product Images Router
Endpoints for listing, uploading, deleting, and bulk-uploading product images.
Works with the existing `product_images` table in the Supabase schema.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db

router = APIRouter(prefix="/products", tags=["product-images"])

_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "products"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
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

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5 MB.")

    # Save to disk
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{product_id}_{uuid.uuid4().hex}{ext}"
    file_path = _UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(content)

    image_url = f"/static/products/{unique_name}"

    # If setting as primary, clear existing primary
    if is_primary:
        db.execute(text(
            "UPDATE product_images SET is_primary = false WHERE product_id = :pid"
        ), {"pid": product_id})

    # Get next sort order
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

    return {"id": new_id, "image_url": image_url, "is_primary": is_primary, "message": "Image uploaded"}


@router.delete(
    "/{product_id}/images/{image_id}",
    dependencies=[Depends(require_admin)],
)
def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    """Delete a product image."""
    row = db.execute(text(
        "SELECT id, image_url FROM product_images WHERE id = :iid AND product_id = :pid"
    ), {"iid": image_id, "pid": product_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete file from disk if it's a local file
    image_url = row[1]
    if image_url and image_url.startswith("/static/"):
        file_path = Path(__file__).resolve().parent.parent.parent / image_url.lstrip("/")
        if file_path.exists():
            file_path.unlink()

    db.execute(text("DELETE FROM product_images WHERE id = :iid"), {"iid": image_id})
    db.commit()
    return {"message": "Image deleted"}
