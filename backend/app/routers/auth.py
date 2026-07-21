from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.crud.auth import get_customer_by_email
from app.database import get_db
from app.core.supabase import SupabaseAuthError, create_supabase_user, login_supabase_user
from app.schemas import CustomerRead, RegisterRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(register_in: RegisterRequest, db: Session = Depends(get_db)) -> Token:
    # ── 1. Check email uniqueness via raw SQL (avoids ORM column issues) ──────
    try:
        existing = db.execute(
            text("SELECT id FROM customers WHERE email = :email LIMIT 1"),
            {"email": register_in.email},
        ).fetchone()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    # ── 2. Create user in Supabase Auth ───────────────────────────────────────
    try:
        create_supabase_user(
            email=register_in.email,
            password=register_in.password,
            user_metadata={
                "first_name": register_in.first_name,
                "last_name":  register_in.last_name,
                "phone":      register_in.phone,
            },
        )
    except SupabaseAuthError as exc:
        # 422 = user already exists in Supabase (allow through)
        if exc.status_code != 422:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    # ── 3. Log in to get token ─────────────────────────────────────────────────
    try:
        session = login_supabase_user(email=register_in.email, password=register_in.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    # ── 4. Ensure a row exists in the local `customers` table ─────────────────
    # Supabase may not have synced it yet — insert or ignore
    try:
        db.execute(text(
            "INSERT INTO customers (email, password_hash, is_active, is_admin) "
            "VALUES (:email, 'supabase_managed', true, :is_admin) "
            "ON CONFLICT (email) DO NOTHING"
        ), {
            "email":    register_in.email,
            "is_admin": (register_in.role == "manager"),
        })
        db.commit()
    except Exception:
        db.rollback()

    # ── 5. If manager, set is_admin = true ────────────────────────────────────
    if (register_in.role or "customer") == "manager":
        try:
            db.execute(
                text("UPDATE customers SET is_admin = true WHERE email = :email"),
                {"email": register_in.email},
            )
            db.commit()
        except Exception:
            db.rollback()

    # ── 6. Populate customer_profiles (name / phone) ──────────────────────────
    try:
        db.execute(text(
            "INSERT INTO customer_profiles (customer_id, first_name, last_name, phone) "
            "SELECT c.id, :fn, :ln, :phone FROM customers c WHERE c.email = :email "
            "ON CONFLICT (customer_id) DO UPDATE SET "
            "first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name"
        ), {
            "email": register_in.email,
            "fn":    register_in.first_name or "User",
            "ln":    register_in.last_name  or "",
            "phone": register_in.phone,
        })
        db.commit()
    except Exception:
        db.rollback()

    return Token(access_token=session["access_token"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    try:
        session = login_supabase_user(email=form_data.username, password=form_data.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return Token(access_token=session["access_token"])


@router.get("/me", response_model=CustomerRead)
def read_current_user(current_user=Depends(get_current_user)) -> CustomerRead:
    return current_user


# ── Manager-only endpoints ────────────────────────────────────────────────────

manager_router = APIRouter(prefix="/manager", tags=["manager"])


@manager_router.get("/customers", dependencies=[Depends(require_admin)])
def list_all_customers(db: Session = Depends(get_db)):
    """All customers with order count and total spend."""
    rows = db.execute(text("""
        SELECT
            c.id, c.email, c.is_active, c.is_admin,
            cp.first_name, cp.last_name, cp.phone,
            COUNT(DISTINCT o.id) AS order_count,
            COALESCE(SUM(o.total_amount) FILTER (WHERE o.status != 'cancelled'), 0) AS total_spend,
            c.created_at
        FROM customers c
        LEFT JOIN customer_profiles cp ON cp.customer_id = c.id
        LEFT JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id, cp.first_name, cp.last_name, cp.phone
        ORDER BY c.created_at DESC
    """)).fetchall()
    return [
        {
            "id": r[0], "email": r[1], "is_active": r[2], "is_manager": r[3],
            "first_name": r[4], "last_name": r[5], "phone": r[6],
            "order_count": int(r[7]), "total_spend": float(r[8]),
            "created_at": r[9].isoformat() if r[9] else None,
        }
        for r in rows
    ]


@manager_router.get("/inventory", dependencies=[Depends(require_admin)])
def get_inventory_levels(db: Session = Depends(get_db)):
    """All products with variant-level inventory — highlights low/out-of-stock."""
    rows = db.execute(text("""
        SELECT
            p.id, p.name AS product_name, b.name AS brand_name, cat.name AS category_name,
            p.base_price, p.is_active,
            COALESCE(SUM(inv.current_stock), 0) AS total_stock,
            COALESCE(SUM(inv.reserved_stock), 0) AS reserved_stock,
            COALESCE(SUM(inv.current_stock - inv.reserved_stock), 0) AS available_stock,
            COUNT(DISTINCT pv.id) AS variant_count
        FROM products p
        LEFT JOIN brands b ON b.id = p.brand_id
        LEFT JOIN subcategories sc ON sc.id = p.subcategory_id
        LEFT JOIN categories cat ON cat.id = sc.category_id
        LEFT JOIN product_variants pv ON pv.product_id = p.id
        LEFT JOIN inventory inv ON inv.variant_id = pv.id
        GROUP BY p.id, b.name, cat.name
        ORDER BY available_stock ASC, p.name
    """)).fetchall()
    return [
        {
            "product_id": r[0], "product_name": r[1], "brand_name": r[2],
            "category_name": r[3], "base_price": float(r[4]) if r[4] else 0,
            "is_active": r[5], "total_stock": int(r[6]),
            "reserved_stock": int(r[7]), "available_stock": int(r[8]),
            "variant_count": int(r[9]),
            "stock_status": (
                "out_of_stock" if int(r[8]) <= 0
                else "low_stock" if int(r[8]) < 10
                else "ok"
            ),
        }
        for r in rows
    ]


@manager_router.get("/reviews", dependencies=[Depends(require_admin)])
def list_all_reviews(db: Session = Depends(get_db)):
    """All reviews across all products, with customer email and reply status."""
    rows = db.execute(text("""
        SELECT r.id, r.customer_id, p.id AS product_id, r.rating,
               COALESCE(r.title, '') || CASE WHEN r.body IS NOT NULL THEN ': ' || r.body ELSE '' END AS comment,
               r.created_at,
               c.email AS customer_email, p.name AS product_name,
               rr.body AS reply_text, rr.id AS reply_id
        FROM reviews r
        JOIN product_variants pv ON pv.id = r.variant_id
        JOIN products p ON p.id = pv.product_id
        LEFT JOIN customers c ON c.id = r.customer_id
        LEFT JOIN review_replies rr ON rr.review_id = r.id
        ORDER BY r.created_at DESC
    """)).fetchall()
    return [
        {
            "id": r[0], "customer_id": r[1], "product_id": r[2],
            "rating": r[3], "comment": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "customer_email": r[6], "product_name": r[7],
            "reply_text": r[8], "has_reply": r[9] is not None,
        }
        for r in rows
    ]


@manager_router.post("/reviews/{review_id}/reply", dependencies=[Depends(require_admin)])
def reply_to_review(review_id: int, payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Post or update a manager reply on a review."""
    reply_text = (payload.get("reply_text") or "").strip()
    if not reply_text:
        raise HTTPException(status_code=400, detail="Reply text is required")

    existing = db.execute(text(
        "SELECT id FROM review_replies WHERE review_id = :rid"
    ), {"rid": review_id}).fetchone()

    if existing:
        db.execute(text(
            "UPDATE review_replies SET body=:text, updated_at=now() WHERE review_id=:rid"
        ), {"text": reply_text, "rid": review_id})
    else:
        db.execute(text(
            "INSERT INTO review_replies (review_id, admin_id, body) VALUES (:rid, :aid, :text)"
        ), {"rid": review_id, "aid": current_user.id, "text": reply_text})

    db.commit()
    return {"message": "Reply saved"}


@manager_router.get("/returns", dependencies=[Depends(require_admin)])
def list_all_returns(db: Session = Depends(get_db)):
    """All return requests with customer and order details."""
    rows = db.execute(text("""
        SELECT rr.id, rr.order_id, rr.reason, rr.status, rr.created_at,
               c.email AS customer_email, o.order_number, o.total_amount
        FROM return_requests rr
        JOIN orders o    ON o.id = rr.order_id
        JOIN customers c ON c.id = o.customer_id
        ORDER BY rr.created_at DESC
    """)).fetchall()
    return [
        {
            "id": r[0], "order_id": r[1], "reason": r[2], "status": r[3],
            "created_at": r[4].isoformat() if r[4] else None,
            "customer_email": r[5], "order_number": r[6],
            "total_amount": float(r[7]) if r[7] else 0,
        }
        for r in rows
    ]


@manager_router.put("/returns/{return_id}/status", dependencies=[Depends(require_admin)])
def update_return_status(return_id: int, payload: dict, db: Session = Depends(get_db)):
    db.execute(text(
        "UPDATE return_requests SET status=:status WHERE id=:id"
    ), {"status": payload.get("status", "pending"), "id": return_id})
    db.commit()
    return {"message": "Return status updated"}


@manager_router.put("/shipments/{shipment_id}", dependencies=[Depends(require_admin)])
def update_shipment(shipment_id: int, payload: dict, db: Session = Depends(get_db)):
    """Update shipment tracking info."""
    db.execute(text(
        "UPDATE shipments SET tracking_number=:tn, carrier=:carrier, status=:status WHERE id=:id"
    ), {
        "tn": payload.get("tracking_number"), "carrier": payload.get("carrier"),
        "status": payload.get("status", "processing"), "id": shipment_id,
    })
    db.commit()
    return {"message": "Shipment updated"}
