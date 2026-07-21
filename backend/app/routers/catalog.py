"""
Catalog routers — Categories, Suppliers, Products.
SQL queries are written against the ACTUAL Supabase schema (45-table normalized).
Products use: brands, subcategories, categories, product_variants, inventory tables.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.crud.catalog import category, product, supplier
from app.database import get_db
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    Message,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)

categories_router = APIRouter(prefix="/categories", tags=["categories"])
suppliers_router  = APIRouter(prefix="/suppliers",  tags=["suppliers"])
products_router   = APIRouter(prefix="/products",   tags=["products"])
customers_router  = APIRouter(prefix="/customers",  tags=["customers"])


# ── Categories — map to actual `categories` table ────────────────────────────

@categories_router.get("", response_model=list[dict])
def list_categories(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, name, slug, description, is_active, created_at, updated_at "
        "FROM categories WHERE is_active = true ORDER BY sort_order, name"
    )).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "slug": r[2],
            "description": r[3], "is_active": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "updated_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]


@categories_router.post(
    "", response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)):
    return category.create(db, obj_in=category_in)


@categories_router.get("/{category_id}", response_model=dict)
def get_category(category_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT id, name, slug, description, is_active FROM categories WHERE id = :id"
    ), {"id": category_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return {"id": row[0], "name": row[1], "slug": row[2], "description": row[3], "is_active": row[4]}


@categories_router.put(
    "/{category_id}", response_model=CategoryRead,
    dependencies=[Depends(require_admin)],
)
def update_category(category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = category.get(db, category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category.update(db, db_obj=db_category, obj_in=category_in)


@categories_router.delete(
    "/{category_id}", response_model=Message,
    dependencies=[Depends(require_admin)],
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    deleted = category.remove(db, object_id=category_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return Message(message="Category deleted successfully")


# ── Suppliers — actual `suppliers` table ─────────────────────────────────────

@suppliers_router.get("", response_model=list[dict])
def list_suppliers(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, name, contact_email, contact_phone, address, is_active "
        "FROM suppliers WHERE is_active = true ORDER BY name"
    )).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "contact_email": r[2],
            "contact_phone": r[3], "address": r[4], "is_active": r[5],
        }
        for r in rows
    ]


@suppliers_router.post(
    "", response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_supplier(supplier_in: SupplierCreate, db: Session = Depends(get_db)):
    return supplier.create(db, obj_in=supplier_in)


@suppliers_router.get("/{supplier_id}", response_model=dict)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT id, name, contact_email, contact_phone, address, is_active "
        "FROM suppliers WHERE id = :id"
    ), {"id": supplier_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return {"id": row[0], "name": row[1], "contact_email": row[2],
            "contact_phone": row[3], "address": row[4], "is_active": row[5]}


@suppliers_router.put(
    "/{supplier_id}", response_model=SupplierRead,
    dependencies=[Depends(require_admin)],
)
def update_supplier(supplier_id: int, supplier_in: SupplierUpdate, db: Session = Depends(get_db)):
    db_supplier = supplier.get(db, supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier.update(db, db_obj=db_supplier, obj_in=supplier_in)


@suppliers_router.delete(
    "/{supplier_id}", response_model=Message,
    dependencies=[Depends(require_admin)],
)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    deleted = supplier.remove(db, object_id=supplier_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return Message(message="Supplier deleted successfully")


# ── Products — raw SQL against actual 45-table Supabase schema ───────────────

def _product_row_to_dict(row) -> dict:
    """Convert a raw SQL row to a product dict for JSON response."""
    return {
        "id":              row[0],
        "name":            row[1],
        "sku":             row[2] or "",
        "description":     row[3],
        "price":           float(row[4]) if row[4] is not None else 0.0,
        "stock_quantity":  int(row[5]) if row[5] is not None else 0,
        "is_active":       bool(row[6]),
        "category_id":     row[7],
        "supplier_id":     row[8],
        "brand_name":      row[9],
        "category_name":   row[10],
        "available_sizes": row[11],
        "is_featured":     bool(row[12]) if row[12] is not None else False,
        "created_at":      row[13].isoformat() if row[13] else None,
        "updated_at":      row[14].isoformat() if row[14] else None,
        "image_url":       row[15],
        "discount_price":  float(row[16]) if row[16] is not None else None,
        "short_description": row[17] or "",
        "tags":            row[18] or "",
        "avg_rating":      float(row[19]) if row[19] is not None else None,
        "review_count":    int(row[20]) if row[20] is not None else 0,
        "is_trending":     bool(row[21]) if row[21] is not None else False,
        "is_new_arrival":  bool(row[22]) if row[22] is not None else False,
    }


# Base query — uses brands, subcategories→categories, product_variants, inventory
_BASE_QUERY = """
    SELECT
        p.id,
        p.name,
        p.slug          AS sku,
        p.description,
        p.base_price    AS price,
        COALESCE((
            SELECT SUM(inv.current_stock)
            FROM product_variants pv
            JOIN inventory inv ON inv.variant_id = pv.id
            WHERE pv.product_id = p.id
        ), 0)           AS stock_quantity,
        p.is_active,
        c.id            AS category_id,
        p.supplier_id,
        b.name          AS brand_name,
        c.name          AS category_name,
        p.available_sizes,
        p.is_featured,
        p.created_at,
        p.updated_at,
        (SELECT pi.image_url FROM product_images pi WHERE pi.product_id = p.id AND pi.is_primary = true LIMIT 1) AS image_url,
        p.discount_price,
        p.short_description,
        p.tags,
        COALESCE((
            SELECT ROUND(AVG(r.rating)::numeric, 1)
            FROM reviews r
            JOIN product_variants rpv ON rpv.id = r.variant_id
            WHERE rpv.product_id = p.id
        ), NULL)         AS avg_rating,
        COALESCE((
            SELECT COUNT(r.id)
            FROM reviews r
            JOIN product_variants rpv ON rpv.id = r.variant_id
            WHERE rpv.product_id = p.id
        ), 0)            AS review_count,
        p.is_trending,
        p.is_new_arrival
    FROM products p
    LEFT JOIN brands b        ON b.id  = p.brand_id
    LEFT JOIN subcategories sc ON sc.id = p.subcategory_id
    LEFT JOIN categories c    ON c.id  = sc.category_id
    WHERE p.is_active = true
"""


@products_router.get("/brands", tags=["products"])
def list_brands(db: Session = Depends(get_db)):
    """Return all brands that have at least one active product."""
    rows = db.execute(text(
        "SELECT DISTINCT b.id, b.name FROM brands b "
        "JOIN products p ON p.brand_id = b.id "
        "WHERE p.is_active = true ORDER BY b.name"
    )).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


@products_router.get("/search", tags=["products"])
def search_products_endpoint(
    db: Session = Depends(get_db),
    query:       Optional[str]   = Query(None),
    category_id: Optional[int]   = Query(None),
    brand_id:    Optional[int]   = Query(None),
    supplier_id: Optional[int]   = Query(None),
    size:        Optional[str]   = Query(None),
    min_price:   Optional[float] = Query(None),
    max_price:   Optional[float] = Query(None),
    limit:       int             = Query(60),
):
    """Search/filter products — uses the real Supabase 45-table schema."""
    sql: str = _BASE_QUERY
    params: dict = {}

    if query:
        sql += " AND (p.name ILIKE :q OR b.name ILIKE :q OR p.description ILIKE :q)"
        params["q"] = f"%{query}%"

    if category_id is not None:
        sql += " AND c.id = :cat_id"
        params["cat_id"] = category_id

    if brand_id is not None:
        sql += " AND p.brand_id = :brand_id"
        params["brand_id"] = brand_id

    if supplier_id is not None:
        sql += " AND p.supplier_id = :sup_id"
        params["sup_id"] = supplier_id

    if min_price is not None:
        sql += " AND p.base_price >= :min_price"
        params["min_price"] = min_price

    if max_price is not None:
        sql += " AND p.base_price <= :max_price"
        params["max_price"] = max_price

    if size:
        sql += " AND p.available_sizes ILIKE :sz"
        params["sz"] = f"%{size}%"

    sql += " ORDER BY p.is_featured DESC, p.name ASC LIMIT :limit"
    params["limit"] = limit

    rows = db.execute(text(sql), params).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.get("", tags=["products"])
def list_products(db: Session = Depends(get_db), skip: int = 0, limit: int = 60):
    sql = _BASE_QUERY + " ORDER BY p.is_featured DESC, p.name ASC LIMIT :limit OFFSET :skip"
    rows = db.execute(text(sql), {"limit": limit, "skip": skip}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.get("/category/{category_id}", tags=["products"])
def filter_products_by_category(category_id: int, db: Session = Depends(get_db)):
    sql = _BASE_QUERY + " AND c.id = :cat_id ORDER BY p.name ASC LIMIT 60"
    rows = db.execute(text(sql), {"cat_id": category_id}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.post(
    "", response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    return product.create(db, obj_in=product_in)


@products_router.get("/featured", tags=["products"])
def get_featured_products(db: Session = Depends(get_db), limit: int = Query(12, le=50)):
    """Return featured products."""
    sql = _BASE_QUERY + " AND p.is_featured = true ORDER BY p.updated_at DESC LIMIT :limit"
    rows = db.execute(text(sql), {"limit": limit}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.get("/trending", tags=["products"])
def get_trending_products(db: Session = Depends(get_db), limit: int = Query(12, le=50)):
    """Return trending products."""
    sql = _BASE_QUERY + " AND p.is_trending = true ORDER BY p.updated_at DESC LIMIT :limit"
    rows = db.execute(text(sql), {"limit": limit}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.get("/new-arrivals", tags=["products"])
def get_new_arrival_products(db: Session = Depends(get_db), limit: int = Query(12, le=50)):
    """Return newest products."""
    sql = _BASE_QUERY + " AND p.is_new_arrival = true ORDER BY p.created_at DESC LIMIT :limit"
    rows = db.execute(text(sql), {"limit": limit}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.get("/top-rated", tags=["products"])
def get_top_rated_products(db: Session = Depends(get_db), limit: int = Query(12, le=50)):
    """Return top-rated products (by average review score)."""
    sql = _BASE_QUERY + """
        AND EXISTS (
            SELECT 1 FROM reviews rv
            JOIN product_variants rpv ON rpv.id = rv.variant_id
            WHERE rpv.product_id = p.id
        )
        ORDER BY (
            SELECT AVG(rv.rating)
            FROM reviews rv
            JOIN product_variants rpv ON rpv.id = rv.variant_id
            WHERE rpv.product_id = p.id
        ) DESC NULLS LAST
        LIMIT :limit
    """
    rows = db.execute(text(sql), {"limit": limit}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.get("/{product_id}", tags=["products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    sql = _BASE_QUERY + " AND p.id = :pid"
    row = db.execute(text(sql), {"pid": product_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product_dict = _product_row_to_dict(row)
    # Attach full image gallery
    images = db.execute(text(
        "SELECT id, image_url, alt_text, is_primary, sort_order "
        "FROM product_images WHERE product_id = :pid "
        "ORDER BY is_primary DESC, sort_order ASC, id ASC"
    ), {"pid": product_id}).fetchall()
    product_dict["images"] = [
        {"id": im[0], "image_url": im[1], "alt_text": im[2], "is_primary": im[3], "sort_order": im[4]}
        for im in images
    ]
    return product_dict


@products_router.get("/{product_id}/related", tags=["products"])
def get_related_products(product_id: int, db: Session = Depends(get_db), limit: int = Query(8, le=20)):
    """Return products in the same category or brand, excluding this product."""
    sql = _BASE_QUERY + """
        AND p.id != :pid
        AND (
            sc.category_id = (SELECT sc2.category_id FROM products p2
                              LEFT JOIN subcategories sc2 ON sc2.id = p2.subcategory_id
                              WHERE p2.id = :pid)
            OR p.brand_id = (SELECT p3.brand_id FROM products p3 WHERE p3.id = :pid)
        )
        ORDER BY p.is_featured DESC, RANDOM()
        LIMIT :limit
    """
    rows = db.execute(text(sql), {"pid": product_id, "limit": limit}).fetchall()
    return [_product_row_to_dict(r) for r in rows]


@products_router.put(
    "/{product_id}", response_model=ProductRead,
    dependencies=[Depends(require_admin)],
)
def update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    db_product = product.get(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product.update(db, db_obj=db_product, obj_in=product_in)


@products_router.delete(
    "/{product_id}", response_model=Message,
    dependencies=[Depends(require_admin)],
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    deleted = product.remove(db, object_id=product_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return Message(message="Product deleted successfully")


# ── Product Image Upload ──────────────────────────────────────────────────────

# Resolve the upload directory (same as main.py)
_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "products"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@products_router.post("/{product_id}/image", tags=["products"])
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image for a product and set it as the primary image."""

    # Validate the product exists
    exists = db.execute(
        text("SELECT id FROM products WHERE id = :pid"), {"pid": product_id}
    ).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate file extension
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content (enforce max size)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB.")

    # Save to disk with a unique filename
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{product_id}_{uuid.uuid4().hex}{ext}"
    file_path = _UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(content)

    # Build the URL path the frontend will use to display the image
    image_url = f"/static/products/{unique_name}"

    # Upsert into product_images table
    existing = db.execute(
        text("SELECT id FROM product_images WHERE product_id = :pid AND is_primary = true"),
        {"pid": product_id},
    ).fetchone()

    if existing:
        db.execute(
            text("UPDATE product_images SET image_url = :url WHERE id = :id"),
            {"url": image_url, "id": existing[0]},
        )
    else:
        db.execute(
            text(
                "INSERT INTO product_images (product_id, image_url, is_primary, sort_order) "
                "VALUES (:pid, :url, true, 0)"
            ),
            {"pid": product_id, "url": image_url},
        )

    db.commit()

    return {"message": "Image uploaded successfully", "image_url": image_url}


# ── Subcategories ─────────────────────────────────────────────────────────────

subcategories_router = APIRouter(prefix="/subcategories", tags=["subcategories"])


@subcategories_router.get("", response_model=list[dict])
def list_subcategories(category_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List active subcategories, optionally filtered by parent category_id."""
    sql = (
        "SELECT sc.id, sc.name, sc.slug, sc.category_id, c.name AS category_name, "
        "sc.description, sc.is_active, sc.sort_order "
        "FROM subcategories sc "
        "LEFT JOIN categories c ON c.id = sc.category_id "
        "WHERE sc.is_active = true"
    )
    params: dict = {}
    if category_id is not None:
        sql += " AND sc.category_id = :cat_id"
        params["cat_id"] = category_id
    sql += " ORDER BY sc.sort_order, sc.name"
    rows = db.execute(text(sql), params).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "slug": r[2],
            "category_id": r[3], "category_name": r[4],
            "description": r[5], "is_active": r[6], "sort_order": r[7],
        }
        for r in rows
    ]


@categories_router.get("/{category_id}/subcategories", response_model=list[dict])
def get_category_subcategories(category_id: int, db: Session = Depends(get_db)):
    """Get all subcategories for a given category."""
    rows = db.execute(text(
        "SELECT id, name, slug, description, is_active FROM subcategories "
        "WHERE category_id = :cat_id AND is_active = true ORDER BY sort_order, name"
    ), {"cat_id": category_id}).fetchall()
    return [
        {"id": r[0], "name": r[1], "slug": r[2], "description": r[3], "is_active": r[4]}
        for r in rows
    ]


# ── Collections ───────────────────────────────────────────────────────────────

collections_router = APIRouter(prefix="/collections", tags=["collections"])


@collections_router.get("", response_model=list[dict])
def list_collections(db: Session = Depends(get_db)):
    """List all active collections with season name."""
    rows = db.execute(text(
        "SELECT c.id, c.name, c.slug, c.description, c.banner_url, "
        "c.start_date, c.end_date, c.is_active, s.name AS season_name "
        "FROM collections c "
        "LEFT JOIN seasons s ON s.id = c.season_id "
        "WHERE c.is_active = true ORDER BY c.start_date DESC NULLS LAST, c.name"
    )).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "slug": r[2], "description": r[3],
            "banner_url": r[4],
            "start_date": r[5].isoformat() if r[5] else None,
            "end_date": r[6].isoformat() if r[6] else None,
            "is_active": r[7], "season_name": r[8],
        }
        for r in rows
    ]


# ── Product Variants ──────────────────────────────────────────────────────────

@products_router.get("/{product_id}/variants", tags=["products"])
def get_product_variants(product_id: int, db: Session = Depends(get_db)):
    """
    Return all active variants for a product, enriched with color/size/material
    names and total available inventory across all warehouses.
    """
    rows = db.execute(text("""
        SELECT
            pv.id,
            pv.sku,
            pv.price_override,
            pv.weight_grams,
            pv.is_active,
            pv.image_url,
            co.id   AS color_id,
            co.name AS color_name,
            co.hex_code,
            sz.id   AS size_id,
            sz.name AS size_name,
            sz.size_category,
            mt.id   AS material_id,
            mt.name AS material_name,
            COALESCE(SUM(inv.current_stock - inv.reserved_stock), 0) AS available_stock
        FROM product_variants pv
        LEFT JOIN colors    co  ON co.id  = pv.color_id
        LEFT JOIN sizes     sz  ON sz.id  = pv.size_id
        LEFT JOIN materials mt  ON mt.id  = pv.material_id
        LEFT JOIN inventory inv ON inv.variant_id = pv.id
        WHERE pv.product_id = :pid AND pv.is_active = true
        GROUP BY pv.id, pv.image_url, co.id, co.name, co.hex_code,
                 sz.id, sz.name, sz.size_category,
                 mt.id, mt.name
        ORDER BY sz.sort_order NULLS LAST, co.name, pv.id
    """), {"pid": product_id}).fetchall()

    return [
        {
            "id": r[0],
            "sku": r[1],
            "price_override": float(r[2]) if r[2] is not None else None,
            "weight_grams": r[3],
            "is_active": r[4],
            "image_url": r[5],
            "color_id": r[6],
            "color_name": r[7],
            "hex_code": r[8],
            "size_id": r[9],
            "size_name": r[10],
            "size_category": r[11],
            "material_id": r[12],
            "material_name": r[13],
            "available_stock": int(r[14]),
        }
        for r in rows
    ]

