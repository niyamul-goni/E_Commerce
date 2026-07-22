from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db

orders_router = APIRouter(prefix="/orders", tags=["orders"])
order_items_router = APIRouter(prefix="/orders", tags=["order-items"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
shipments_router = APIRouter(prefix="/shipments", tags=["shipments"])
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])
cart_items_router = APIRouter(prefix="/cart-items", tags=["cart-items"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

ORDER_STATUSES = {"pending", "confirmed", "packed", "shipped", "delivered", "cancelled", "returned", "refunded"}
PAYMENT_STATUSES = {"pending", "paid", "failed", "refunded"}
SHIPMENT_STATUSES = {"pending", "packed", "in_transit", "delivered", "returned"}
ORDER_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"packed", "cancelled"},
    "packed": {"shipped", "cancelled"},
    "shipped": {"delivered", "returned"},
    "delivered": {"returned"},
    "returned": {"refunded"},
    "cancelled": set(),
    "refunded": set(),
}


def _coupon_discount(row, subtotal: Decimal) -> Decimal:
    """Validate a locked coupon row and calculate its authoritative discount."""
    now = datetime.now(timezone.utc)
    coupon_type = str(row[1])
    value = Decimal(str(row[2]))
    min_amount = Decimal(str(row[3] or 0))
    max_discount = Decimal(str(row[4])) if row[4] is not None else None
    valid_from, valid_until, max_uses, used_count = row[5], row[6], row[7], row[8]
    if valid_from and valid_from > now:
        raise HTTPException(status_code=400, detail="This coupon is not active yet")
    if valid_until and valid_until < now:
        raise HTTPException(status_code=400, detail="This coupon has expired")
    if subtotal < min_amount:
        raise HTTPException(status_code=400, detail=f"Minimum order amount is {min_amount} BDT")
    if max_uses is not None and used_count >= max_uses:
        raise HTTPException(status_code=400, detail="This coupon has reached its usage limit")
    discount = subtotal * value / Decimal("100") if coupon_type == "percentage" else value
    if max_discount is not None:
        discount = min(discount, max_discount)
    return min(discount, subtotal).quantize(Decimal("0.01"))


def _order_items(db: Session, order_id: int) -> list[dict]:
    rows = db.execute(text("""
        SELECT oi.id, oi.variant_id, pv.product_id, oi.quantity, oi.unit_price, oi.line_total,
               p.name, pv.sku, co.name, sz.name
        FROM order_items oi
        JOIN product_variants pv ON pv.id = oi.variant_id
        JOIN products p ON p.id = pv.product_id
        LEFT JOIN colors co ON co.id = pv.color_id
        LEFT JOIN sizes sz ON sz.id = pv.size_id
        WHERE oi.order_id = :oid
        ORDER BY oi.id
    """), {"oid": order_id}).fetchall()
    return [
        {
            "id": row[0], "variant_id": row[1], "product_id": row[2], "quantity": row[3],
            "unit_price": float(row[4]), "line_total": float(row[5]),
            "product_name": row[6], "sku": row[7], "color_name": row[8], "size_name": row[9],
        }
        for row in rows
    ]


def _address_from_notes(notes: str | None) -> str | None:
    if not notes or not notes.startswith("Shipping: "):
        return None
    return notes.removeprefix("Shipping: ").split(" | ", 1)[0] or None


@orders_router.post("", status_code=status.HTTP_201_CREATED)
def place_order(order_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Place a new order using the cart contents (raw SQL for Supabase schema)."""
    from app.utils.generators import generate_order_number

    shipping_address = order_in.get("shipping_address", "")
    billing_address = order_in.get("billing_address", "")
    shipping_address_id = order_in.get("shipping_address_id")
    billing_address_id = order_in.get("billing_address_id")
    coupon_id = order_in.get("coupon_id")
    notes = order_in.get("notes", "")
    items = order_in.get("items", [])

    if not items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    for address_id, label in ((shipping_address_id, "shipping"), (billing_address_id, "billing")):
        if address_id and db.execute(text(
            "SELECT id FROM customer_addresses WHERE id = :aid AND customer_id = :cid"
        ), {"aid": address_id, "cid": current_user.id}).fetchone() is None:
            raise HTTPException(status_code=400, detail=f"Invalid {label} address")

    order_number = generate_order_number()
    subtotal = Decimal("0.00")

    resolved_items = []
    for item in items:
        vid = item.get("variant_id")
        pid = item.get("product_id")
        try:
            qty = int(item.get("quantity", 1))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Item quantity must be an integer") from exc
        if qty < 1:
            raise HTTPException(status_code=400, detail="Item quantity must be at least 1")

        if not vid and pid:
            first_variant = db.execute(text(
                "SELECT pv.id FROM product_variants pv "
                "LEFT JOIN inventory inv ON inv.variant_id = pv.id "
                "WHERE pv.product_id = :pid AND pv.is_active = true "
                "GROUP BY pv.id "
                "ORDER BY COALESCE(SUM(inv.current_stock - inv.reserved_stock), 0) DESC, pv.id ASC LIMIT 1"
            ), {"pid": pid}).fetchone()
            if first_variant:
                vid = first_variant[0]

        if not vid:
            raise HTTPException(status_code=400, detail=f"Could not resolve variant for item: {item}")

        price_row = db.execute(text(
            "SELECT COALESCE(pv.price_override, p.base_price), p.is_active, pv.is_active "
            "FROM product_variants pv JOIN products p ON p.id = pv.product_id "
            "WHERE pv.id = :vid"
        ), {"vid": vid}).fetchone()
        if not price_row or not price_row[1] or not price_row[2]:
            raise HTTPException(status_code=400, detail=f"Variant {vid} not found")

        available = db.execute(text(
            "SELECT COALESCE(SUM(current_stock - reserved_stock), 0) FROM inventory WHERE variant_id = :vid"
        ), {"vid": vid}).scalar() or 0
        if int(available) < qty:
            raise HTTPException(status_code=409, detail=f"Only {int(available)} units are available for variant {vid}")

        unit_price = Decimal(str(price_row[0]))
        resolved_items.append({"vid": vid, "qty": qty, "unit_price": unit_price})
        subtotal += unit_price * qty

    discount_amount = Decimal("0.00")
    if coupon_id:
        coupon = db.execute(text("""
            SELECT id, coupon_type::text, value, min_order_amount, max_discount_amount,
                   valid_from, valid_until, max_uses, used_count
            FROM coupons WHERE id = :coupon_id AND is_active = true
            FOR UPDATE
        """), {"coupon_id": coupon_id}).fetchone()
        if coupon is None:
            raise HTTPException(status_code=400, detail="Invalid coupon")
        already_used = db.execute(text(
            "SELECT id FROM coupon_usages WHERE coupon_id = :coupon_id AND customer_id = :customer_id"
        ), {"coupon_id": coupon_id, "customer_id": current_user.id}).fetchone()
        if already_used:
            raise HTTPException(status_code=400, detail="You have already used this coupon")
        discount_amount = _coupon_discount(coupon, subtotal)

    shipping_cost = max(Decimal("0"), Decimal(str(order_in.get("shipping_cost", 0) or 0)))
    tax_amount = max(Decimal("0"), Decimal(str(order_in.get("tax_amount", 0) or 0)))
    total_amount = subtotal - discount_amount + shipping_cost + tax_amount

    # Build notes with address info
    full_notes = ""
    if shipping_address:
        full_notes += f"Shipping: {shipping_address}"
    if billing_address:
        full_notes += f" | Billing: {billing_address}"
    if notes:
        full_notes += f" | {notes}"

    try:
        order_id = db.execute(text("""
            INSERT INTO orders (order_number, customer_id, shipping_address_id,
                billing_address_id, coupon_id, status, subtotal, discount_amount,
                shipping_cost, tax_amount, total_amount, notes)
            VALUES (:on, :cid, :said, :baid, :cpid, 'pending', :sub, :disc,
                :ship, :tax, :total, :notes)
            RETURNING id
        """), {
            "on": order_number, "cid": current_user.id,
            "said": shipping_address_id, "baid": billing_address_id,
            "cpid": coupon_id, "sub": subtotal, "disc": discount_amount,
            "ship": shipping_cost, "tax": tax_amount,
            "total": total_amount, "notes": full_notes or None,
        }).scalar_one()

        for item in resolved_items:
            db.execute(text(
                "INSERT INTO order_items (order_id, variant_id, quantity, unit_price, discount_amount) "
                "VALUES (:oid, :vid, :qty, :up, 0)"
            ), {"oid": order_id, "vid": item["vid"], "qty": item["qty"], "up": item["unit_price"]})

        if coupon_id:
            db.execute(text("""
                INSERT INTO coupon_usages (coupon_id, customer_id, order_id, discount_applied)
                VALUES (:coupon_id, :customer_id, :order_id, :discount)
            """), {
                "coupon_id": coupon_id, "customer_id": current_user.id,
                "order_id": order_id, "discount": discount_amount,
            })

        db.execute(text(
            "DELETE FROM cart_items WHERE cart_id = (SELECT id FROM carts WHERE customer_id = :cid)"
        ), {"cid": current_user.id})
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        detail = "A saved shipping address is required" if shipping_address_id is None else "Order data conflicts with an existing record"
        raise HTTPException(status_code=409, detail=detail) from exc

    return {
        "id": order_id, "order_number": order_number,
        "subtotal": float(subtotal), "discount_amount": float(discount_amount),
        "total_amount": float(total_amount), "status": "pending",
    }


@orders_router.get("/me")
def get_my_orders(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return all orders for the current user."""
    rows = db.execute(text("""
        SELECT o.id, o.order_number, o.status::text, o.subtotal, o.discount_amount,
               o.shipping_cost, o.tax_amount, o.total_amount, o.notes,
               o.order_date, o.created_at,
               (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) AS item_count,
               CONCAT_WS(', ', sa.line1, NULLIF(sa.line2, ''), sa.city,
                         NULLIF(sa.state, ''), NULLIF(sa.postal_code, ''), sa.country) AS saved_address
        FROM orders o
        LEFT JOIN customer_addresses sa ON sa.id = o.shipping_address_id
        WHERE o.customer_id = :cid
        ORDER BY o.order_date DESC
    """), {"cid": current_user.id}).fetchall()
    orders = []
    for row in rows:
        orders.append({
            "id": row[0], "order_number": row[1], "status": row[2],
            "subtotal": float(row[3] or 0), "discount_amount": float(row[4] or 0),
            "shipping_cost": float(row[5] or 0), "tax_amount": float(row[6] or 0),
            "total_amount": float(row[7] or 0), "notes": row[8],
            "order_date": row[9].isoformat() if row[9] else None,
            "created_at": row[10].isoformat() if row[10] else None,
            "item_count": int(row[11]),
            "shipping_address": row[12] or _address_from_notes(row[8]),
            "items": _order_items(db, row[0]),
        })
    return orders


@orders_router.get("", dependencies=[Depends(require_admin)])
def list_all_orders(db: Session = Depends(get_db)):
    """Return all orders (admin only)."""
    rows = db.execute(text("""
        SELECT o.id, o.order_number, o.customer_id, o.status::text,
               o.subtotal, o.discount_amount, o.shipping_cost, o.tax_amount,
               o.total_amount, o.notes, o.order_date, o.created_at,
               c.email AS customer_email,
               (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) AS item_count,
               CONCAT_WS(', ', sa.line1, NULLIF(sa.line2, ''), sa.city,
                         NULLIF(sa.state, ''), NULLIF(sa.postal_code, ''), sa.country) AS saved_address
        FROM orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        LEFT JOIN customer_addresses sa ON sa.id = o.shipping_address_id
        ORDER BY o.order_date DESC
    """)).fetchall()
    orders = []
    for row in rows:
        orders.append({
            "id": row[0], "order_number": row[1], "customer_id": row[2], "status": row[3],
            "subtotal": float(row[4] or 0), "discount_amount": float(row[5] or 0),
            "shipping_cost": float(row[6] or 0), "tax_amount": float(row[7] or 0),
            "total_amount": float(row[8] or 0), "notes": row[9],
            "order_date": row[10].isoformat() if row[10] else None,
            "created_at": row[11].isoformat() if row[11] else None,
            "customer_email": row[12], "item_count": int(row[13]),
            "shipping_address": row[14] or _address_from_notes(row[9]),
            "items": _order_items(db, row[0]),
        })
    return orders


@orders_router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get a single order with its items."""
    order = db.execute(text("""
        SELECT o.id, o.order_number, o.customer_id, o.status::text,
               o.subtotal, o.discount_amount, o.shipping_cost, o.tax_amount,
               o.total_amount, o.notes, o.order_date, o.created_at,
               CONCAT_WS(', ', sa.line1, NULLIF(sa.line2, ''), sa.city,
                         NULLIF(sa.state, ''), NULLIF(sa.postal_code, ''), sa.country)
        FROM orders o
        LEFT JOIN customer_addresses sa ON sa.id = o.shipping_address_id
        WHERE o.id = :oid
    """), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[2] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this order")

    return {
        "id": order[0], "order_number": order[1], "customer_id": order[2],
        "status": order[3],
        "subtotal": float(order[4]) if order[4] else 0,
        "discount_amount": float(order[5]) if order[5] else 0,
        "shipping_cost": float(order[6]) if order[6] else 0,
        "tax_amount": float(order[7]) if order[7] else 0,
        "total_amount": float(order[8]) if order[8] else 0,
        "notes": order[9],
        "order_date": order[10].isoformat() if order[10] else None,
        "created_at": order[11].isoformat() if order[11] else None,
        "shipping_address": order[12] or _address_from_notes(order[9]),
        "items": _order_items(db, order_id),
    }


@orders_router.put("/{order_id}/status", dependencies=[Depends(require_admin)])
def change_order_status(order_id: int, status_in: dict, db: Session = Depends(get_db)):
    """Update order status (admin only)."""
    new_status = status_in.get("status", "pending")
    if new_status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid order status")
    try:
        current_status = db.execute(text(
            "SELECT status::text FROM orders WHERE id = :oid FOR UPDATE"
        ), {"oid": order_id}).scalar()
        if current_status is None:
            db.rollback()
            raise HTTPException(status_code=404, detail="Order not found")
        if new_status != current_status and new_status not in ORDER_TRANSITIONS[current_status]:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Order cannot move from {current_status} to {new_status}",
            )
        result = db.execute(text(
            "UPDATE orders SET status = CAST(:status AS order_status), updated_at = now() WHERE id = :oid RETURNING id"
        ), {"status": new_status, "oid": order_id}).fetchone()
        db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": order_id, "status": new_status, "message": "Order status updated"}


@order_items_router.post("/{order_id}/items", status_code=status.HTTP_201_CREATED)
def add_item_to_order(order_id: int, item_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add an item to an existing order (raw SQL)."""
    from sqlalchemy import text as _text
    # Verify order exists and belongs to user
    order = db.execute(_text(
        "SELECT customer_id, status::text FROM orders WHERE id = :oid"
    ), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this order")
    if order[1] != "pending":
        raise HTTPException(status_code=409, detail="Only pending orders can be modified")

    vid = item_in.get("variant_id")
    try:
        qty = int(item_in.get("quantity", 1))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Quantity must be an integer") from exc
    if qty < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    price_row = db.execute(_text(
        "SELECT COALESCE(pv.price_override, p.base_price) "
        "FROM product_variants pv JOIN products p ON p.id = pv.product_id "
        "WHERE pv.id = :vid AND pv.is_active = true AND p.is_active = true"
    ), {"vid": vid}).fetchone()
    if not price_row:
        raise HTTPException(status_code=400, detail=f"Variant {vid} not found")
    available = db.execute(_text(
        "SELECT COALESCE(SUM(current_stock - reserved_stock), 0) FROM inventory WHERE variant_id = :vid"
    ), {"vid": vid}).scalar() or 0
    if int(available) < qty:
        raise HTTPException(status_code=409, detail=f"Only {int(available)} units are available for variant {vid}")
    unit_price = Decimal(str(price_row[0]))

    try:
        result = db.execute(_text(
            "INSERT INTO order_items (order_id, variant_id, quantity, unit_price, discount_amount) "
            "VALUES (:oid, :vid, :qty, :up, 0) RETURNING id"
        ), {"oid": order_id, "vid": vid, "qty": qty, "up": unit_price})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This variant is already in the order") from exc
    return {"id": result.fetchone()[0], "order_id": order_id, "variant_id": vid, "quantity": qty}


@order_items_router.delete("/{order_id}/items/{order_item_id}")
def remove_item_from_order(order_id: int, order_item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Remove an item from an order."""
    from sqlalchemy import text as _text
    order = db.execute(_text(
        "SELECT customer_id FROM orders WHERE id = :oid"
    ), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this order")
    result = db.execute(_text(
        "DELETE FROM order_items WHERE id = :iid AND order_id = :oid RETURNING id"
    ), {"iid": order_item_id, "oid": order_id}).fetchone()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    db.commit()
    return {"message": "Order item removed successfully"}


@payments_router.post("", status_code=status.HTTP_201_CREATED)
def create_payment(payment_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Record a payment for an order."""
    order_id = payment_in.get("order_id")
    order = db.execute(text(
        "SELECT customer_id, total_amount FROM orders WHERE id = :oid"
    ), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to pay for this order")

    payment_status = payment_in.get("payment_status", "pending")
    if payment_status not in PAYMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid payment status")
    amount = Decimal(str(order[1]))

    try:
        payment_id = db.execute(text("""
            INSERT INTO payments (order_id, payment_method, payment_status, amount, transaction_ref, paid_at)
            VALUES (:oid, :method, CAST(:payment_status AS payment_status), :amount, :ref,
                    CASE WHEN :payment_status = 'paid' THEN now() ELSE NULL END)
            ON CONFLICT (order_id) DO UPDATE SET
                payment_method = EXCLUDED.payment_method,
                payment_status = EXCLUDED.payment_status,
                amount = EXCLUDED.amount,
                transaction_ref = EXCLUDED.transaction_ref,
                paid_at = EXCLUDED.paid_at,
                updated_at = now()
            RETURNING id
        """), {
            "oid": order_id,
            "method": payment_in.get("payment_method", "cash_on_delivery"),
            "payment_status": payment_status,
            "amount": amount,
            "ref": payment_in.get("transaction_reference") or payment_in.get("transaction_ref"),
        }).scalar_one()

        if payment_status == "paid":
            db.execute(text(
                "UPDATE orders SET status = 'confirmed', updated_at = now() WHERE id = :oid AND status = 'pending'"
            ), {"oid": order_id})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Payment could not be recorded: {exc}") from exc
    return {
        "id": payment_id, "order_id": order_id, "amount": float(amount),
        "payment_status": payment_status, "message": "Payment recorded",
    }


@payments_router.get("/order/{order_id}")
def get_payment_by_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get payment info for an order."""
    from sqlalchemy import text as _text
    row = db.execute(_text(
        "SELECT p.id, p.order_id, p.payment_method, p.payment_status::text, "
        "p.amount, p.transaction_ref, p.paid_at, p.created_at "
        "FROM payments p WHERE p.order_id = :oid"
    ), {"oid": order_id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    # Check order ownership
    order = db.execute(_text("SELECT customer_id FROM orders WHERE id = :oid"), {"oid": order_id}).fetchone()
    if order and not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this payment")

    return {
        "id": row[0], "order_id": row[1], "payment_method": row[2],
        "payment_status": row[3], "amount": float(row[4]) if row[4] else 0,
        "transaction_ref": row[5],
        "paid_at": row[6].isoformat() if row[6] else None,
        "created_at": row[7].isoformat() if row[7] else None,
    }


@shipments_router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_shipment_endpoint(shipment_in: dict, db: Session = Depends(get_db)):
    """Create a shipment for an order (admin only)."""
    from sqlalchemy import text as _text
    
    # Convert empty strings to None to avoid unique constraint violations on tracking_number
    tn = shipment_in.get("tracking_number")
    if tn == "":
        tn = None
        
    carrier = shipment_in.get("carrier")
    if carrier == "":
        carrier = None
        
    # Frontend might send "status" instead of "shipment_status"
    status_val = shipment_in.get("status") or shipment_in.get("shipment_status", "in_transit")
    if status_val not in SHIPMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid shipment status")
    
    try:
        result = db.execute(_text(
            "INSERT INTO shipments (order_id, tracking_number, carrier_name, shipment_status) "
            "VALUES (:oid, :tn, :carrier, CAST(:status AS shipment_status)) "
            "ON CONFLICT (order_id) DO UPDATE SET "
            "tracking_number = EXCLUDED.tracking_number, "
            "carrier_name = EXCLUDED.carrier_name, "
            "shipment_status = EXCLUDED.shipment_status, "
            "updated_at = now() "
            "RETURNING id"
        ), {
            "oid": shipment_in.get("order_id"),
            "tn": tn,
            "carrier": carrier,
            "status": status_val,
        })
        shipment_id = result.scalar_one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Shipment conflicts with an order or tracking number") from exc
    return {"id": shipment_id, "status": status_val, "shipment_status": status_val, "message": "Shipment saved"}


@shipments_router.get("/order/{order_id}")
def get_shipment_by_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get shipment info for an order."""
    from sqlalchemy import text as _text
    row = db.execute(_text(
        "SELECT s.id, s.order_id, s.tracking_number, s.carrier_name, "
        "s.shipment_status::text, s.shipped_at, s.estimated_delivery, "
        "s.delivered_at, s.created_at "
        "FROM shipments s WHERE s.order_id = :oid"
    ), {"oid": order_id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")

    order = db.execute(_text("SELECT customer_id FROM orders WHERE id = :oid"), {"oid": order_id}).fetchone()
    if order and not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this shipment")

    return {
        "id": row[0], "order_id": row[1], "tracking_number": row[2],
        "carrier": row[3], "status": row[4], "shipment_status": row[4],
        "shipped_at": row[5].isoformat() if row[5] else None,
        "estimated_delivery": row[6].isoformat() if row[6] else None,
        "delivered_at": row[7].isoformat() if row[7] else None,
        "created_at": row[8].isoformat() if row[8] else None,
    }


@reviews_router.post("", status_code=status.HTTP_201_CREATED)
def create_review(review_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Submit a product review."""
    variant_id = review_in.get("variant_id")
    product_id = review_in.get("product_id")
    if not variant_id and product_id:
        variant_id = db.execute(text("""
            SELECT pv.id FROM product_variants pv
            WHERE pv.product_id = :product_id AND pv.is_active = true
            ORDER BY pv.id LIMIT 1
        """), {"product_id": product_id}).scalar()
    if not variant_id:
        raise HTTPException(status_code=400, detail="A valid product variant is required")

    variant = db.execute(text(
        "SELECT product_id FROM product_variants WHERE id = :variant_id AND is_active = true"
    ), {"variant_id": variant_id}).fetchone()
    if variant is None or (product_id and int(product_id) != int(variant[0])):
        raise HTTPException(status_code=400, detail="Variant does not belong to the selected product")

    try:
        rating = int(review_in.get("rating"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Rating must be an integer from 1 to 5") from exc
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    order_id = review_in.get("order_id")
    if order_id:
        purchased = db.execute(text("""
            SELECT 1 FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.id = :order_id AND o.customer_id = :customer_id AND oi.variant_id = :variant_id
        """), {
            "order_id": order_id, "customer_id": current_user.id, "variant_id": variant_id,
        }).fetchone()
        if purchased is None:
            raise HTTPException(status_code=403, detail="The order does not contain this variant")

    try:
        review_id = db.execute(text(
            "INSERT INTO reviews (customer_id, variant_id, order_id, rating, title, body) "
            "VALUES (:cid, :vid, :oid, :rating, :title, :body) RETURNING id"
        ), {
            "cid": current_user.id, "vid": variant_id, "oid": order_id, "rating": rating,
            "title": review_in.get("title"),
            "body": review_in.get("body", review_in.get("comment")),
        }).scalar_one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already reviewed this product variant") from exc
    return {"id": review_id, "variant_id": variant_id, "message": "Review submitted"}


@reviews_router.get("/product/{product_id}")
def list_reviews_for_product(product_id: int, db: Session = Depends(get_db)):
    """Return all reviews for a product using raw SQL for schema compatibility."""
    rows = db.execute(text(
        "SELECT r.id, r.customer_id, p.id AS product_id, r.rating, "
        "COALESCE(NULLIF(r.title, '') || ': ', '') || COALESCE(r.body, '') AS comment, "
        "r.created_at, c.email as customer_email, rr.body AS reply_text, r.variant_id "
        "FROM reviews r "
        "JOIN product_variants pv ON pv.id = r.variant_id "
        "JOIN products p ON p.id = pv.product_id "
        "LEFT JOIN customers c ON c.id = r.customer_id "
        "LEFT JOIN review_replies rr ON rr.review_id = r.id "
        "WHERE p.id = :pid "
        "ORDER BY r.created_at DESC NULLS LAST"
    ), {"pid": product_id}).fetchall()
    return [
        {
            "id":           row[0],
            "customer_id":  row[1],
            "product_id":   row[2],
            "rating":       row[3],
            "comment":      row[4] or "",
            "created_at":   row[5].isoformat() if row[5] else None,
            "customer_email": row[6],
            "reply_text": row[7],
            "variant_id": row[8],
        }
        for row in rows
    ]


@cart_items_router.post("", status_code=status.HTTP_201_CREATED)
def add_to_cart(cart_item_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add a variant to the current user's cart (raw SQL for Supabase schema)."""
    from sqlalchemy import text as _text
    variant_id = cart_item_in.get("variant_id")
    try:
        quantity = int(cart_item_in.get("quantity", 1))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Quantity must be an integer") from exc
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    # If product_id is provided but not variant_id, find the first available variant
    if not variant_id:
        product_id = cart_item_in.get("product_id")
        if product_id:
            first_variant = db.execute(_text(
                "SELECT pv.id FROM product_variants pv "
                "LEFT JOIN inventory inv ON inv.variant_id = pv.id "
                "WHERE pv.product_id = :pid AND pv.is_active = true "
                "ORDER BY COALESCE(inv.current_stock - inv.reserved_stock, 0) DESC, pv.id ASC "
                "LIMIT 1"
            ), {"pid": product_id}).fetchone()
            if first_variant:
                variant_id = first_variant[0]
    if not variant_id:
        raise HTTPException(status_code=400, detail="variant_id or product_id is required")

    variant = db.execute(_text(
        "SELECT pv.id, COALESCE(SUM(inv.current_stock - inv.reserved_stock), 0) "
        "FROM product_variants pv JOIN products p ON p.id = pv.product_id "
        "LEFT JOIN inventory inv ON inv.variant_id = pv.id "
        "WHERE pv.id = :vid AND pv.is_active = true AND p.is_active = true GROUP BY pv.id"
    ), {"vid": variant_id}).fetchone()
    if not variant:
        raise HTTPException(status_code=400, detail="Product variant is not available")

    # Ensure a cart row exists for this customer
    db.execute(_text(
        "INSERT INTO carts (customer_id) VALUES (:cid) ON CONFLICT (customer_id) DO NOTHING"
    ), {"cid": current_user.id})
    db.commit()

    cart_id = db.execute(_text(
        "SELECT id FROM carts WHERE customer_id = :cid"
    ), {"cid": current_user.id}).scalar()

    # Check if variant already in cart
    existing = db.execute(_text(
        "SELECT id, quantity FROM cart_items WHERE cart_id = :cid AND variant_id = :vid"
    ), {"cid": cart_id, "vid": variant_id}).fetchone()

    if existing:
        new_qty = existing[1] + quantity
        if new_qty > int(variant[1]):
            raise HTTPException(status_code=409, detail=f"Only {int(variant[1])} units are available")
        db.execute(_text(
            "UPDATE cart_items SET quantity = :qty, updated_at = now() WHERE id = :iid"
        ), {"qty": new_qty, "iid": existing[0]})
        db.commit()
        return {"id": existing[0], "variant_id": variant_id, "quantity": new_qty, "message": "Cart updated"}
    else:
        if quantity > int(variant[1]):
            raise HTTPException(status_code=409, detail=f"Only {int(variant[1])} units are available")
        result = db.execute(_text(
            "INSERT INTO cart_items (cart_id, variant_id, quantity) VALUES (:cid, :vid, :qty) RETURNING id"
        ), {"cid": cart_id, "vid": variant_id, "qty": quantity})
        db.commit()
        new_id = result.fetchone()[0]
        return {"id": new_id, "variant_id": variant_id, "quantity": quantity, "message": "Added to cart"}


@cart_items_router.get("/me")
def list_my_cart_items(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return all cart items for the current user with product & variant details."""
    from sqlalchemy import text as _text
    rows = db.execute(_text("""
        SELECT
            ci.id,
            ci.variant_id,
            ci.quantity,
            pv.sku,
            p.id            AS product_id,
            p.name           AS product_name,
            COALESCE(pv.price_override, p.base_price) AS unit_price,
            ci.quantity * COALESCE(pv.price_override, p.base_price) AS subtotal,
            co.name          AS color_name,
            sz.name          AS size_name,
            (SELECT pi.image_url FROM product_images pi
             WHERE pi.product_id = p.id AND pi.is_primary = true LIMIT 1) AS primary_image_url,
            COALESCE((SELECT SUM(inv.current_stock - inv.reserved_stock)
                      FROM inventory inv WHERE inv.variant_id = pv.id), 0) AS available_stock
        FROM carts c
        JOIN cart_items ci ON ci.cart_id = c.id
        JOIN product_variants pv ON pv.id = ci.variant_id
        JOIN products p ON p.id = pv.product_id
        LEFT JOIN colors co ON co.id = pv.color_id
        LEFT JOIN sizes  sz ON sz.id = pv.size_id
        WHERE c.customer_id = :cid
        ORDER BY ci.added_at DESC
    """), {"cid": current_user.id}).fetchall()

    return [
        {
            "id":               r[0],
            "variant_id":       r[1],
            "quantity":         r[2],
            "sku":              r[3],
            "product_id":       r[4],
            "product_name":     r[5],
            "unit_price":       float(r[6]) if r[6] else 0,
            "subtotal":         float(r[7]) if r[7] else 0,
            "color_name":       r[8],
            "size_name":        r[9],
            "primary_image_url": r[10],
            "available_stock":  int(r[11]) if r[11] else 0,
        }
        for r in rows
    ]


@cart_items_router.put("/{cart_item_id}")
def update_cart_item(cart_item_id: int, cart_item_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update the quantity of a cart item."""
    from sqlalchemy import text as _text
    try:
        quantity = int(cart_item_in.get("quantity", 1))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Quantity must be an integer") from exc
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    # Verify ownership
    row = db.execute(_text(
        "SELECT ci.id, COALESCE((SELECT SUM(inv.current_stock - inv.reserved_stock) "
        "FROM inventory inv WHERE inv.variant_id = ci.variant_id), 0) FROM cart_items ci "
        "JOIN carts c ON c.id = ci.cart_id "
        "WHERE ci.id = :iid AND c.customer_id = :cid"
    ), {"iid": cart_item_id, "cid": current_user.id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    if quantity > int(row[1]):
        raise HTTPException(status_code=409, detail=f"Only {int(row[1])} units are available")
    db.execute(_text(
        "UPDATE cart_items SET quantity = :qty, updated_at = now() WHERE id = :iid"
    ), {"qty": quantity, "iid": cart_item_id})
    db.commit()
    return {"id": cart_item_id, "quantity": quantity, "message": "Cart item updated"}


@cart_items_router.delete("/{cart_item_id}")
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Remove a cart item."""
    from sqlalchemy import text as _text
    row = db.execute(_text(
        "SELECT ci.id FROM cart_items ci "
        "JOIN carts c ON c.id = ci.cart_id "
        "WHERE ci.id = :iid AND c.customer_id = :cid"
    ), {"iid": cart_item_id, "cid": current_user.id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.execute(_text("DELETE FROM cart_items WHERE id = :iid"), {"iid": cart_item_id})
    db.commit()
    return {"message": "Cart item removed successfully"}


@dashboard_router.get("/summary", dependencies=[Depends(require_admin)])
def dashboard_summary(db: Session = Depends(get_db)):
    """Dashboard KPIs using raw SQL for actual Supabase schema."""
    from sqlalchemy import text as _text
    row = db.execute(_text("""
        SELECT
            (SELECT COUNT(*) FROM customers) AS total_customers,
            (SELECT COUNT(*) FROM categories) AS total_categories,
            (SELECT COUNT(*) FROM suppliers) AS total_suppliers,
            (SELECT COUNT(*) FROM products) AS total_products,
            (SELECT COUNT(*) FROM orders) AS total_orders,
            (SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'cancelled') AS total_sales,
            (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_status = 'paid') AS total_payments,
            (SELECT COALESCE(SUM(ci.quantity), 0) FROM cart_items ci) AS total_cart_items,
            (SELECT COALESCE(AVG(total_amount), 0) FROM orders WHERE status != 'cancelled') AS average_order_value,
            (SELECT COUNT(*) FROM inventory WHERE (current_stock - reserved_stock) < 10) AS low_stock_products,
            (SELECT COUNT(*) FROM reviews WHERE rating >= 4) AS top_rated_products,
            (SELECT COUNT(*) FROM orders WHERE status = 'pending') AS pending_orders,
            (SELECT COUNT(*) FROM orders WHERE status = 'shipped') AS shipped_orders
    """)).fetchone()
    return {
        "total_customers": int(row[0]),
        "total_categories": int(row[1]),
        "total_suppliers": int(row[2]),
        "total_products": int(row[3]),
        "total_orders": int(row[4]),
        "total_sales": float(row[5]),
        "total_payments": float(row[6]),
        "total_cart_items": int(row[7]),
        "average_order_value": float(row[8]),
        "low_stock_products": int(row[9]),
        "top_rated_products": int(row[10]),
        "pending_orders": int(row[11]),
        "shipped_orders": int(row[12]),
    }


# ── Wishlist ──────────────────────────────────────────────────────────────────

wishlist_router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@wishlist_router.get("", summary="Get my wishlist")
def get_my_wishlist(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return all wishlist items for the current user with product & variant details."""
    from sqlalchemy import text as _text
    rows = db.execute(_text("""
        SELECT
            wi.id         AS item_id,
            wi.variant_id,
            wi.added_at,
            pv.sku,
            p.id          AS product_id,
            p.name        AS product_name,
            p.base_price,
            COALESCE(pv.price_override, p.base_price) AS effective_price,
            co.name       AS color_name,
            co.hex_code,
            sz.name       AS size_name,
            (SELECT pi.image_url FROM product_images pi
             WHERE pi.product_id = p.id AND pi.is_primary = true LIMIT 1) AS image_url
        FROM wishlists wl
        JOIN wishlist_items wi ON wi.wishlist_id = wl.id
        JOIN product_variants pv ON pv.id = wi.variant_id
        JOIN products p ON p.id = pv.product_id
        LEFT JOIN colors co ON co.id = pv.color_id
        LEFT JOIN sizes  sz ON sz.id = pv.size_id
        WHERE wl.customer_id = :cid
        ORDER BY wi.added_at DESC
    """), {"cid": current_user.id}).fetchall()

    return [
        {
            "id":             r[0],
            "variant_id":     r[1],
            "added_at":       r[2].isoformat() if r[2] else None,
            "sku":            r[3],
            "product_id":     r[4],
            "product_name":   r[5],
            "base_price":     float(r[6]) if r[6] else 0,
            "effective_price": float(r[7]) if r[7] else 0,
            "color_name":     r[8],
            "hex_code":       r[9],
            "size_name":      r[10],
            "image_url":      r[11],
        }
        for r in rows
    ]


@wishlist_router.post("/{variant_id}", status_code=201, summary="Add variant to wishlist")
def add_to_wishlist(variant_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    # Ensure wishlist exists
    db.execute(_text(
        "INSERT INTO wishlists (customer_id) VALUES (:cid) ON CONFLICT (customer_id) DO NOTHING"
    ), {"cid": current_user.id})
    db.commit()

    wl_id = db.execute(_text(
        "SELECT id FROM wishlists WHERE customer_id = :cid"
    ), {"cid": current_user.id}).scalar()

    # Check not already in wishlist
    existing = db.execute(_text(
        "SELECT id FROM wishlist_items WHERE wishlist_id = :wid AND variant_id = :vid"
    ), {"wid": wl_id, "vid": variant_id}).fetchone()
    if existing:
        return {"message": "Already in wishlist", "id": existing[0]}

    result = db.execute(_text(
        "INSERT INTO wishlist_items (wishlist_id, variant_id) VALUES (:wid, :vid) RETURNING id"
    ), {"wid": wl_id, "vid": variant_id})
    db.commit()
    new_id = result.fetchone()[0]
    return {"message": "Added to wishlist", "id": new_id, "variant_id": variant_id}


@wishlist_router.delete("/{item_id}", summary="Remove item from wishlist")
def remove_from_wishlist(item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    # Verify ownership
    row = db.execute(_text(
        "SELECT wi.id FROM wishlist_items wi "
        "JOIN wishlists wl ON wl.id = wi.wishlist_id "
        "WHERE wi.id = :iid AND wl.customer_id = :cid"
    ), {"iid": item_id, "cid": current_user.id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
    db.execute(_text("DELETE FROM wishlist_items WHERE id = :iid"), {"iid": item_id})
    db.commit()
    return {"message": "Removed from wishlist"}


# ── Customer Addresses ────────────────────────────────────────────────────────

addresses_router = APIRouter(prefix="/addresses", tags=["addresses"])


@addresses_router.get("", summary="Get my addresses")
def get_my_addresses(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    rows = db.execute(_text(
        "SELECT id, label, recipient_name, phone, line1, line2, city, state, "
        "postal_code, country, is_default, created_at "
        "FROM customer_addresses WHERE customer_id = :cid ORDER BY is_default DESC, id ASC"
    ), {"cid": current_user.id}).fetchall()
    return [
        {
            "id": r[0], "label": r[1], "recipient_name": r[2], "phone": r[3],
            "line1": r[4], "line2": r[5], "city": r[6], "state": r[7],
            "postal_code": r[8], "country": r[9], "is_default": r[10],
            "created_at": r[11].isoformat() if r[11] else None,
        }
        for r in rows
    ]


@addresses_router.post("", status_code=201, summary="Add address")
def add_address(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    # If this is default, clear other defaults first
    if payload.get("is_default"):
        db.execute(_text(
            "UPDATE customer_addresses SET is_default = false WHERE customer_id = :cid"
        ), {"cid": current_user.id})

    result = db.execute(_text(
        "INSERT INTO customer_addresses "
        "(customer_id, label, recipient_name, phone, line1, line2, city, state, postal_code, country, is_default) "
        "VALUES (:cid, :label, :name, :phone, :line1, :line2, :city, :state, :postal, :country, :is_default) "
        "RETURNING id"
    ), {
        "cid":       current_user.id,
        "label":     payload.get("label", "Home"),
        "name":      payload.get("recipient_name", ""),
        "phone":     payload.get("phone"),
        "line1":     payload.get("line1", ""),
        "line2":     payload.get("line2"),
        "city":      payload.get("city", ""),
        "state":     payload.get("state"),
        "postal":    payload.get("postal_code"),
        "country":   payload.get("country", "Bangladesh"),
        "is_default": bool(payload.get("is_default", False)),
    })
    db.commit()
    new_id = result.fetchone()[0]
    return {"id": new_id, "message": "Address saved"}


@addresses_router.put("/{address_id}", summary="Update address")
def update_address(address_id: int, payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    row = db.execute(_text(
        "SELECT id FROM customer_addresses WHERE id = :aid AND customer_id = :cid"
    ), {"aid": address_id, "cid": current_user.id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Address not found")

    if payload.get("is_default"):
        db.execute(_text(
            "UPDATE customer_addresses SET is_default = false WHERE customer_id = :cid"
        ), {"cid": current_user.id})

    db.execute(_text(
        "UPDATE customer_addresses SET "
        "label=:label, recipient_name=:name, phone=:phone, line1=:line1, line2=:line2, "
        "city=:city, state=:state, postal_code=:postal, country=:country, is_default=:is_default "
        "WHERE id = :aid"
    ), {
        "label":     payload.get("label", "Home"),
        "name":      payload.get("recipient_name", ""),
        "phone":     payload.get("phone"),
        "line1":     payload.get("line1", ""),
        "line2":     payload.get("line2"),
        "city":      payload.get("city", ""),
        "state":     payload.get("state"),
        "postal":    payload.get("postal_code"),
        "country":   payload.get("country", "Bangladesh"),
        "is_default": bool(payload.get("is_default", False)),
        "aid":       address_id,
    })
    db.commit()
    return {"id": address_id, "message": "Address updated"}


@addresses_router.delete("/{address_id}", summary="Delete address")
def delete_address(address_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    row = db.execute(_text(
        "SELECT id FROM customer_addresses WHERE id = :aid AND customer_id = :cid"
    ), {"aid": address_id, "cid": current_user.id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Address not found")
    db.execute(_text("DELETE FROM customer_addresses WHERE id = :aid"), {"aid": address_id})
    db.commit()
    return {"message": "Address deleted"}


# ── Customer Profile ──────────────────────────────────────────────────────────

profile_router = APIRouter(prefix="/profile", tags=["profile"])


@profile_router.get("", summary="Get my profile")
def get_my_profile(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    row = db.execute(_text(
        "SELECT cp.first_name, cp.last_name, cp.phone, cp.date_of_birth, "
        "cp.avatar_url, g.name AS gender "
        "FROM customer_profiles cp "
        "LEFT JOIN genders g ON g.id = cp.gender_id "
        "WHERE cp.customer_id = :cid"
    ), {"cid": current_user.id}).fetchone()

    base = {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
    }
    if row:
        base.update({
            "first_name": row[0], "last_name": row[1], "phone": row[2],
            "date_of_birth": row[3].isoformat() if row[3] else None,
            "avatar_url": row[4], "gender": row[5],
        })
    return base


@profile_router.put("", summary="Update my profile")
def update_my_profile(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from sqlalchemy import text as _text
    db.execute(_text(
        "INSERT INTO customer_profiles (customer_id, first_name, last_name, phone) "
        "VALUES (:cid, :fn, :ln, :phone) "
        "ON CONFLICT (customer_id) DO UPDATE SET "
        "first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, "
        "phone = EXCLUDED.phone, updated_at = now()"
    ), {
        "cid":   current_user.id,
        "fn":    payload.get("first_name", ""),
        "ln":    payload.get("last_name", ""),
        "phone": payload.get("phone"),
    })
    db.commit()
    return {"message": "Profile updated"}


# ── Coupon Validation ─────────────────────────────────────────────────────────

coupon_validate_router = APIRouter(prefix="/coupons", tags=["coupons"])


@coupon_validate_router.post("/validate", summary="Validate a coupon code")
def validate_coupon_code(payload: dict, db: Session = Depends(get_db)):
    from sqlalchemy import text as _text
    code = (payload.get("code") or "").strip().upper()
    subtotal = float(payload.get("subtotal", 0))
    if not code:
        raise HTTPException(status_code=400, detail="Coupon code is required")

    row = db.execute(_text(
        "SELECT id, coupon_type, value, min_order_amount, max_discount_amount, "
        "valid_from, valid_until, max_uses, used_count, description "
        "FROM coupons WHERE code = :code AND is_active = true"
    ), {"code": code}).fetchone()

    if not row:
        return {"valid": False, "message": "Invalid or expired coupon code", "discount": 0}

    try:
        discount = _coupon_discount(row[:9], Decimal(str(subtotal)))
    except HTTPException as exc:
        return {"valid": False, "message": exc.detail, "discount": 0}
    coupon_id, description = row[0], row[9]

    return {
        "valid": True,
        "coupon_id": coupon_id,
        "discount": float(discount),
        "message": description or f"Coupon applied! You save {float(discount):.2f} BDT",
    }


@coupon_validate_router.get("/list", dependencies=[Depends(require_admin)])
def list_coupons_admin(db: Session = Depends(get_db)):
    from sqlalchemy import text as _text
    rows = db.execute(_text(
        "SELECT id, code, coupon_type, value, min_order_amount, max_discount_amount, "
        "max_uses, used_count, valid_until, is_active, description "
        "FROM coupons ORDER BY created_at DESC"
    )).fetchall()
    return [
        {
            "id": r[0], "code": r[1], "coupon_type": r[2], "value": float(r[3]),
            "min_order_amount": float(r[4]) if r[4] is not None else None,
            "max_discount_amount": float(r[5]) if r[5] is not None else None,
            "max_uses": r[6], "used_count": r[7],
            "valid_until": r[8].isoformat() if r[8] else None,
            "is_active": r[9], "description": r[10],
        }
        for r in rows
    ]


@coupon_validate_router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_coupon_admin(payload: dict, db: Session = Depends(get_db)):
    from sqlalchemy import text as _text
    code = (payload.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
        
    existing = db.execute(_text("SELECT id FROM coupons WHERE code = :code"), {"code": code}).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Coupon code already exists")
        
    coupon_type = payload.get("coupon_type", "percentage")
    if coupon_type == "fixed":
        coupon_type = "fixed_amount"
    if coupon_type not in {"percentage", "fixed_amount"}:
        raise HTTPException(status_code=400, detail="Coupon type must be percentage or fixed_amount")
    try:
        coupon_value = Decimal(str(payload.get("value")))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Coupon value must be a number") from exc
    if coupon_value <= 0 or (coupon_type == "percentage" and coupon_value > 100):
        raise HTTPException(status_code=400, detail="Coupon value must be positive and percentage cannot exceed 100")
    try:
        result = db.execute(_text("""
            INSERT INTO coupons (
                code, coupon_type, value, min_order_amount, max_discount_amount,
                max_uses, valid_until, description, is_active
            ) VALUES (
                :code, CAST(:type AS coupon_type), :value, :min_amt, :max_disc,
                :max_uses, :valid, :desc, :active
            ) RETURNING id
        """), {
            "code": code, "type": coupon_type, "value": coupon_value,
            "min_amt": payload.get("min_order_amount") or 0,
            "max_disc": payload.get("max_discount_amount"), "max_uses": payload.get("max_uses"),
            "valid": payload.get("valid_until"), "desc": payload.get("description"),
            "active": payload.get("is_active", True),
        })
        coupon_id = result.scalar_one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Coupon conflicts with an existing code or invalid values") from exc
    return {"id": coupon_id, "message": "Coupon created"}


@coupon_validate_router.put("/{coupon_id}", dependencies=[Depends(require_admin)])
def update_coupon_admin(coupon_id: int, payload: dict, db: Session = Depends(get_db)):
    from sqlalchemy import text as _text
    if "is_active" in payload:
        db.execute(_text("UPDATE coupons SET is_active = :active, updated_at = now() WHERE id = :id"), 
                   {"active": payload["is_active"], "id": coupon_id})
        db.commit()
    return {"id": coupon_id, "message": "Coupon updated"}
