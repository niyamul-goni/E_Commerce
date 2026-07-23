"""
Catalog routers — Categories, Suppliers, Products.
SQL queries are written against the ACTUAL Supabase schema (45-table normalized).
Products use: brands, subcategories, categories, product_variants, inventory tables.
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.core.product_image_storage import (
    ProductImageStorageError,
    delete_managed_product_image,
    store_product_image,
)
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


def _slugify(value: str) -> str:
    """Create a stable URL slug without relying on database extensions."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or uuid.uuid4().hex[:12]


def _available_slug(db: Session, table: str, value: str, *, exclude_id: int | None = None) -> str:
    """Return a unique slug for one of the two allow-listed catalog tables."""
    if table not in {"categories", "products"}:
        raise ValueError("Unsupported slug table")
    base = _slugify(value)
    candidate = base
    suffix = 2
    while True:
        sql = f"SELECT id FROM {table} WHERE slug = :slug"
        params: dict = {"slug": candidate}
        if exclude_id is not None:
            sql += " AND id != :exclude_id"
            params["exclude_id"] = exclude_id
        if db.execute(text(sql), params).fetchone() is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


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


@categories_router.get("/manage/all", response_model=list[dict], dependencies=[Depends(require_admin)])
def list_categories_for_manager(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, name, slug, description, is_active, created_at, updated_at "
        "FROM categories ORDER BY sort_order, name"
    )).mappings().all()
    return [dict(row) for row in rows]


@categories_router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)):
    slug = _available_slug(db, "categories", category_in.name)
    try:
        row = db.execute(text("""
            INSERT INTO categories (name, slug, description, is_active)
            VALUES (:name, :slug, :description, :is_active)
            RETURNING id, name, slug, description, is_active, created_at, updated_at
        """), {**category_in.model_dump(), "slug": slug}).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name or slug already exists") from exc


@categories_router.get("/{category_id}", response_model=dict)
def get_category(category_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT id, name, slug, description, is_active FROM categories WHERE id = :id"
    ), {"id": category_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return {"id": row[0], "name": row[1], "slug": row[2], "description": row[3], "is_active": row[4]}


@categories_router.put("/{category_id}", dependencies=[Depends(require_admin)])
def update_category(category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT id, name FROM categories WHERE id = :id"), {"id": category_id}).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    data = category_in.model_dump(exclude_unset=True)
    if "name" in data:
        data["slug"] = _available_slug(db, "categories", data["name"], exclude_id=category_id)
    allowed = {"name", "slug", "description", "is_active"}
    updates = {key: value for key, value in data.items() if key in allowed}
    try:
        if updates:
            assignments = ", ".join(f"{key} = :{key}" for key in updates)
            db.execute(text(f"UPDATE categories SET {assignments}, updated_at = now() WHERE id = :id"), {**updates, "id": category_id})
            db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name or slug already exists") from exc
    row = db.execute(text(
        "SELECT id, name, slug, description, is_active, created_at, updated_at FROM categories WHERE id = :id"
    ), {"id": category_id}).mappings().one()
    return dict(row)


@categories_router.delete(
    "/{category_id}", response_model=Message,
    dependencies=[Depends(require_admin)],
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id FROM categories WHERE id = :id"), {"id": category_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    db.execute(text("UPDATE categories SET is_active = false, updated_at = now() WHERE id = :id"), {"id": category_id})
    db.commit()
    return Message(message="Category deactivated successfully")


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


@suppliers_router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_supplier(supplier_in: SupplierCreate, db: Session = Depends(get_db)):
    try:
        row = db.execute(text("""
            INSERT INTO suppliers (name, contact_email, contact_phone, address, is_active)
            VALUES (:name, :contact_email, :contact_phone, :address, :is_active)
            RETURNING id, name, contact_email, contact_phone, address, is_active, created_at, updated_at
        """), supplier_in.model_dump()).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Supplier name or contact details already exist") from exc


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


@suppliers_router.put("/{supplier_id}", dependencies=[Depends(require_admin)])
def update_supplier(supplier_id: int, supplier_in: SupplierUpdate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT id FROM suppliers WHERE id = :id"), {"id": supplier_id}).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    data = supplier_in.model_dump(exclude_unset=True)
    allowed = {"name", "contact_email", "contact_phone", "address", "is_active"}
    updates = {key: value for key, value in data.items() if key in allowed}
    if updates:
        assignments = ", ".join(f"{key} = :{key}" for key in updates)
        db.execute(text(f"UPDATE suppliers SET {assignments}, updated_at = now() WHERE id = :id"), {**updates, "id": supplier_id})
        db.commit()
    row = db.execute(text(
        "SELECT id, name, contact_email, contact_phone, address, is_active, created_at, updated_at FROM suppliers WHERE id = :id"
    ), {"id": supplier_id}).mappings().one()
    return dict(row)


@suppliers_router.delete(
    "/{supplier_id}", response_model=Message,
    dependencies=[Depends(require_admin)],
)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT id FROM suppliers WHERE id = :id"), {"id": supplier_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    db.execute(text("UPDATE suppliers SET is_active = false, updated_at = now() WHERE id = :id"), {"id": supplier_id})
    db.commit()
    return Message(message="Supplier deactivated successfully")


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
        "brand_id":        row[23],
        "subcategory_id":  row[24],
    }


# Base query — uses brands, subcategories→categories, product_variants, inventory
_BASE_QUERY = """
    SELECT
        p.id,
        p.name,
        COALESCE((
            SELECT pv.sku
            FROM product_variants pv
            WHERE pv.product_id = p.id
            ORDER BY pv.is_active DESC, pv.id
            LIMIT 1
        ), p.slug)      AS sku,
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
        p.is_new_arrival,
        p.brand_id,
        p.subcategory_id
    FROM products p
    LEFT JOIN brands b        ON b.id  = p.brand_id
    LEFT JOIN subcategories sc ON sc.id = p.subcategory_id
    LEFT JOIN categories c    ON c.id  = sc.category_id
    WHERE p.is_active = true
"""


@products_router.get("/brands", tags=["products"])
def list_brands(db: Session = Depends(get_db)):
    """Return active brands, including brands available for a new product."""
    rows = db.execute(text(
        "SELECT b.id, b.name FROM brands b WHERE b.is_active = true ORDER BY b.name"
    )).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


@products_router.get("/manage/all", tags=["products"], dependencies=[Depends(require_admin)])
def list_products_for_manager(db: Session = Depends(get_db), skip: int = 0, limit: int = Query(200, le=500)):
    sql = _BASE_QUERY.replace("WHERE p.is_active = true", "WHERE true")
    sql += " ORDER BY p.updated_at DESC, p.name ASC LIMIT :limit OFFSET :skip"
    rows = db.execute(text(sql), {"limit": limit, "skip": skip}).fetchall()
    return [_product_row_to_dict(row) for row in rows]


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


def _resolve_product_references(db: Session, data: dict) -> tuple[int, int, int]:
    """Resolve normalized brand/subcategory/supplier references for manager writes."""
    supplier_id = data.get("supplier_id")
    brand_id = data.get("brand_id")
    subcategory_id = data.get("subcategory_id")
    category_id = data.get("category_id")

    if not brand_id:
        brand_id = db.execute(text("SELECT id FROM brands WHERE is_active = true ORDER BY id LIMIT 1")).scalar()
    if not subcategory_id and category_id:
        subcategory_id = db.execute(text(
            "SELECT id FROM subcategories WHERE category_id = :category_id AND is_active = true ORDER BY sort_order, id LIMIT 1"
        ), {"category_id": category_id}).scalar()

    if not supplier_id or not brand_id or not subcategory_id:
        raise HTTPException(
            status_code=400,
            detail="Supplier, brand, and subcategory are required for the normalized product schema",
        )
    references = db.execute(text("""
        SELECT
            EXISTS (SELECT 1 FROM suppliers WHERE id = :supplier_id AND is_active = true),
            EXISTS (SELECT 1 FROM brands WHERE id = :brand_id AND is_active = true),
            EXISTS (
                SELECT 1 FROM subcategories
                WHERE id = :subcategory_id AND is_active = true
                  AND (:category_id IS NULL OR category_id = :category_id)
            )
    """), {
        "supplier_id": supplier_id, "brand_id": brand_id,
        "subcategory_id": subcategory_id, "category_id": category_id,
    }).one()
    if not all(references):
        raise HTTPException(status_code=400, detail="Invalid supplier, brand, or category/subcategory selection")
    return int(brand_id), int(subcategory_id), int(supplier_id)


def _set_product_stock(db: Session, product_id: int, desired_stock: int, sku: str) -> None:
    """Adjust aggregate available stock through one inventory row, preserving reservations."""
    variant_id = db.execute(text(
        "SELECT id FROM product_variants WHERE product_id = :pid ORDER BY is_active DESC, id LIMIT 1"
    ), {"pid": product_id}).scalar()
    if variant_id is None:
        variant_id = db.execute(text(
            "INSERT INTO product_variants (product_id, sku, is_active) VALUES (:pid, :sku, true) RETURNING id"
        ), {"pid": product_id, "sku": sku}).scalar()

    inventory_rows = db.execute(text("""
        SELECT inv.id, inv.current_stock, inv.reserved_stock
        FROM inventory inv
        JOIN product_variants pv ON pv.id = inv.variant_id
        WHERE pv.product_id = :pid
        ORDER BY inv.id
        FOR UPDATE
    """), {"pid": product_id}).fetchall()

    if not inventory_rows:
        warehouse_id = db.execute(text(
            "SELECT id FROM warehouses WHERE is_active = true ORDER BY id LIMIT 1"
        )).scalar()
        if warehouse_id is None:
            if desired_stock:
                raise HTTPException(status_code=400, detail="Create an active warehouse before assigning product stock")
            return
        db.execute(text("""
            INSERT INTO inventory (variant_id, warehouse_id, current_stock, reserved_stock, reorder_level)
            VALUES (:variant_id, :warehouse_id, :stock, 0, 10)
        """), {"variant_id": variant_id, "warehouse_id": warehouse_id, "stock": desired_stock})
        return

    current_available = sum(int(row[1]) - int(row[2]) for row in inventory_rows)
    delta = desired_stock - current_available
    primary = inventory_rows[0]
    next_current = int(primary[1]) + delta
    if next_current < int(primary[2]):
        raise HTTPException(status_code=409, detail="Requested stock is below currently reserved stock")
    db.execute(text(
        "UPDATE inventory SET current_stock = :stock, updated_at = now() WHERE id = :id"
    ), {"stock": next_current, "id": primary[0]})


@products_router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    data = product_in.model_dump()
    brand_id, subcategory_id, supplier_id = _resolve_product_references(db, data)
    slug = _available_slug(db, "products", data.get("sku") or data["name"])
    variant_sku = (data.get("sku") or slug).strip()
    try:
        product_id = db.execute(text("""
            INSERT INTO products (
                name, slug, brand_id, supplier_id, subcategory_id, base_price,
                description, is_active, available_sizes
            ) VALUES (
                :name, :slug, :brand_id, :supplier_id, :subcategory_id, :price,
                :description, :is_active, :available_sizes
            ) RETURNING id
        """), {
            **data,
            "slug": slug,
            "brand_id": brand_id,
            "subcategory_id": subcategory_id,
            "supplier_id": supplier_id,
        }).scalar_one()
        db.execute(text(
            "INSERT INTO product_variants (product_id, sku, is_active) VALUES (:pid, :sku, true)"
        ), {"pid": product_id, "sku": variant_sku})
        _set_product_stock(db, product_id, int(data.get("stock_quantity") or 0), variant_sku)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product slug or SKU already exists") from exc
    if data.get("is_active") is False:
        return {"id": product_id, "is_active": False, "message": "Product created"}
    return get_product(product_id, db)


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


@products_router.put("/{product_id}", dependencies=[Depends(require_admin)])
def update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT id, slug FROM products WHERE id = :id"), {"id": product_id}).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    data = product_in.model_dump(exclude_unset=True)
    if "category_id" in data and "subcategory_id" not in data:
        resolved_subcategory = db.execute(text(
            "SELECT id FROM subcategories WHERE category_id = :category_id AND is_active = true ORDER BY sort_order, id LIMIT 1"
        ), {"category_id": data["category_id"]}).scalar()
        if resolved_subcategory is None:
            raise HTTPException(status_code=400, detail="Selected category has no active subcategory")
        data["subcategory_id"] = resolved_subcategory
    if any(key in data for key in ("supplier_id", "brand_id", "subcategory_id", "category_id")):
        current_refs = db.execute(text(
            "SELECT brand_id, subcategory_id, supplier_id FROM products WHERE id = :id"
        ), {"id": product_id}).one()
        reference_data = {
            "brand_id": data.get("brand_id", current_refs[0]),
            "subcategory_id": data.get("subcategory_id", current_refs[1]),
            "supplier_id": data.get("supplier_id", current_refs[2]),
            "category_id": data.get("category_id"),
        }
        _resolve_product_references(db, reference_data)
    updates: dict = {}
    field_map = {
        "name": "name",
        "description": "description",
        "price": "base_price",
        "supplier_id": "supplier_id",
        "brand_id": "brand_id",
        "subcategory_id": "subcategory_id",
        "is_active": "is_active",
        "available_sizes": "available_sizes",
    }
    for source, target in field_map.items():
        if source in data:
            updates[target] = data[source]

    variant_sku = data.get("sku")
    if variant_sku:
        updates["slug"] = _available_slug(db, "products", variant_sku, exclude_id=product_id)

    try:
        if updates:
            assignments = ", ".join(f"{column} = :{column}" for column in updates)
            db.execute(text(f"UPDATE products SET {assignments}, updated_at = now() WHERE id = :id"), {**updates, "id": product_id})
        if variant_sku:
            db.execute(text("""
                UPDATE product_variants SET sku = :sku, updated_at = now()
                WHERE id = (SELECT id FROM product_variants WHERE product_id = :pid ORDER BY id LIMIT 1)
            """), {"sku": variant_sku.strip(), "pid": product_id})
        if "stock_quantity" in data and data["stock_quantity"] is not None:
            _set_product_stock(db, product_id, int(data["stock_quantity"]), variant_sku or existing[1])
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product slug or SKU already exists") from exc

    if data.get("is_active") is False:
        return {"id": product_id, "is_active": False, "message": "Product updated"}
    return get_product(product_id, db)


@products_router.delete(
    "/{product_id}", response_model=Message,
    dependencies=[Depends(require_admin)],
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).fetchone()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.execute(text("UPDATE products SET is_active = false, updated_at = now() WHERE id = :id"), {"id": product_id})
    db.commit()
    return Message(message="Product deactivated successfully")


# ── Product Image Upload ──────────────────────────────────────────────────────

# Resolve the upload directory (same as main.py)
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


@products_router.post("/{product_id}/image", tags=["products"], dependencies=[Depends(require_admin)])
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image for a product and set it as the primary image."""

    # Validate the product exists
    product = db.execute(
        text("SELECT id, name FROM products WHERE id = :pid"), {"pid": product_id}
    ).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate file extension
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

    # Read file content (enforce max size)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The selected image is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB.")

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

    # Upsert into product_images table
    existing = db.execute(
        text("SELECT id, image_url FROM product_images WHERE product_id = :pid AND is_primary = true"),
        {"pid": product_id},
    ).fetchone()
    previous_image_url = existing[1] if existing else None

    try:
        if existing:
            db.execute(
                text("UPDATE product_images SET image_url = :url, alt_text = :alt WHERE id = :id"),
                {"url": image_url, "alt": product[1], "id": existing[0]},
            )
        else:
            db.execute(
                text(
                    "INSERT INTO product_images (product_id, image_url, alt_text, is_primary, sort_order) "
                    "VALUES (:pid, :url, :alt, true, 0)"
                ),
                {"pid": product_id, "url": image_url, "alt": product[1]},
            )
        db.commit()
    except Exception:
        db.rollback()
        await delete_managed_product_image(image_url, local_dir=_UPLOAD_DIR)
        raise

    # A replacement should not leave the previous managed upload orphaned.
    # Remote URLs outside this application's bucket are never touched.
    if previous_image_url != image_url:
        try:
            await delete_managed_product_image(
                previous_image_url,
                local_dir=_UPLOAD_DIR,
            )
        except (OSError, ProductImageStorageError):
            # The database already points at the new valid upload. Cleanup
            # failure must not make the manager see a false upload failure.
            pass

    return {
        "message": "Image uploaded successfully",
        "product_id": product_id,
        "image_url": image_url,
    }


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
