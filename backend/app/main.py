"""
GoDrip — FastAPI Application Entry Point
Production-quality e-commerce API demonstrating normalized 45-table PostgreSQL database
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

# Resolve the static upload directory relative to the backend root
BACKEND_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BACKEND_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "products"

from app.core.config import settings
from app.database import init_db
import app.models  # noqa: F401 — ensures all models are registered

# Import routers
from app.routers import (
    addresses_router,
    auth_router,
    cart_items_router,
    categories_router,
    collections_router,
    coupon_validate_router,
    customers_router,
    dashboard_router,
    order_items_router,
    orders_router,
    payments_router,
    products_router,
    profile_router,
    reviews_router,
    shipments_router,
    subcategories_router,
    suppliers_router,
    wishlist_router,
)
from app.routers.auth import manager_router
from app.routers.analytics import router as analytics_router
from app.routers.images import router as images_router


# Extended routers disabled — they reference a normalized schema
# that does not exist in the current Supabase database.
_extended_routers = False

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # Schema DDL must be an explicit opt-in, especially for managed/live DBs.
    if settings.INITIALIZE_DATABASE_ON_STARTUP:
        init_db()
    yield


# ─────────────────────────────────────────────────────────
# App instantiation
# ─────────────────────────────────────────────────────────

app = FastAPI(
    lifespan=lifespan,
    title="GoDrip API",
    description="""
## GoDrip E-Commerce API

Production-quality fashion & lifestyle e-commerce backend demonstrating:
- **45-table normalized PostgreSQL schema** (3NF/BCNF)
- **57 performance indexes** across all major query paths
- **12 PostgreSQL functions** for business logic
- **11 triggers** for data integrity and automation
- **17 views** (14 regular + 3 materialized) for reporting
- **Complete RBAC** with roles and permissions

Designed as a university DBMS course showcase project.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─────────────────────────────────────────────────────────
# Static files — serve uploaded product images
# ─────────────────────────────────────────────────────────

STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ─────────────────────────────────────────────────────────
# Routers — v1
# ─────────────────────────────────────────────────────────

PREFIX = settings.API_V1_STR

# Auth & customers
app.include_router(auth_router,      prefix=PREFIX)
app.include_router(customers_router, prefix=PREFIX)
app.include_router(profile_router,   prefix=PREFIX)
app.include_router(addresses_router, prefix=PREFIX)
app.include_router(wishlist_router,  prefix=PREFIX)

# Catalog
app.include_router(categories_router,   prefix=PREFIX)
app.include_router(subcategories_router, prefix=PREFIX)
app.include_router(collections_router,  prefix=PREFIX)
app.include_router(suppliers_router,    prefix=PREFIX)
app.include_router(products_router,     prefix=PREFIX)
app.include_router(images_router,       prefix=PREFIX)

# Sales
app.include_router(orders_router,      prefix=PREFIX)
app.include_router(order_items_router, prefix=PREFIX)
app.include_router(payments_router,    prefix=PREFIX)
app.include_router(shipments_router,   prefix=PREFIX)
app.include_router(coupon_validate_router, prefix=PREFIX)

# Engagement
app.include_router(reviews_router,    prefix=PREFIX)
app.include_router(cart_items_router, prefix=PREFIX)

# Analytics
app.include_router(dashboard_router,  prefix=PREFIX)
app.include_router(analytics_router,  prefix=PREFIX)

# Manager panel
app.include_router(manager_router,    prefix=PREFIX)


# Extended routers (new modules)
if _extended_routers:
    app.include_router(brands_router,    prefix=PREFIX, tags=["Brands"])
    app.include_router(inventory_router, prefix=PREFIX, tags=["Inventory"])
    app.include_router(coupons_router,   prefix=PREFIX, tags=["Coupons"])
    app.include_router(returns_router,   prefix=PREFIX, tags=["Returns & Refunds"])
    app.include_router(analytics_router, prefix=PREFIX, tags=["Analytics & Reports"])


# ─────────────────────────────────────────────────────────
# Health check endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root() -> dict:
    return {
        "message": "GoDrip E-Commerce API v2.0",
        "docs": "/docs",
        "database_tables": 45,
        "schema_version": "2.0 (3NF/BCNF Normalized)",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"])
def database_health() -> dict:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        result = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        ))
        table_count = result.scalar()
        return {
            "status": "ok",
            "database": "connected",
            "table_count": table_count,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


@app.get("/health/schema", tags=["Health"])
def schema_info() -> dict:
    """Returns database schema statistics"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        stats = {}
        for table in ["products", "customers", "orders", "categories", "suppliers"]:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            stats[table] = count
        return {"status": "ok", "row_counts": stats}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()
