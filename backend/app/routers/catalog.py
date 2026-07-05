"""
Catalog routers — Categories, Suppliers, Products.
SQL queries are written against the ACTUAL Supabase schema (45-table normalized).
Products use: brands, subcategories, categories, product_variants, inventory tables.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
        (SELECT pi.image_url FROM product_images pi WHERE pi.product_id = p.id AND pi.is_primary = true LIMIT 1) AS image_url
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


@products_router.get("/{product_id}", tags=["products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    sql = _BASE_QUERY + " AND p.id = :pid"
    row = db.execute(text(sql), {"pid": product_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _product_row_to_dict(row)


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
