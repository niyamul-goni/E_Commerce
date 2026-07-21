from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
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


@orders_router.post("", status_code=status.HTTP_201_CREATED)
def place_order(order_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Place a new order using the cart contents (raw SQL for Supabase schema)."""
    from sqlalchemy import text as _text
    from app.utils.generators import generate_order_number

    # Accept text address fields (no address ID required)
    shipping_address = order_in.get("shipping_address", "")
    billing_address = order_in.get("billing_address", "")
    shipping_address_id = order_in.get("shipping_address_id")  # optional FK
    billing_address_id = order_in.get("billing_address_id")    # optional FK
    coupon_id = order_in.get("coupon_id")
    notes = order_in.get("notes", "")
    items = order_in.get("items", [])

    if not items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    # Ensure shipping_address_id column is nullable (one-time migration)
    try:
        db.execute(_text("ALTER TABLE orders ALTER COLUMN shipping_address_id DROP NOT NULL"))
        db.commit()
    except Exception:
        db.rollback()  # Already nullable or migration not needed

    order_number = generate_order_number()
    subtotal = 0.0

    # Resolve items: accept either variant_id or product_id
    resolved_items = []
    for item in items:
        vid = item.get("variant_id")
        pid = item.get("product_id")
        qty = item.get("quantity", 1)

        # If only product_id given, find the first active variant
        if not vid and pid:
            first_variant = db.execute(_text(
                "SELECT pv.id FROM product_variants pv "
                "WHERE pv.product_id = :pid AND pv.is_active = true "
                "ORDER BY pv.id ASC LIMIT 1"
            ), {"pid": pid}).fetchone()
            if first_variant:
                vid = first_variant[0]

        if not vid:
            raise HTTPException(status_code=400, detail=f"Could not resolve variant for item: {item}")

        price_row = db.execute(_text(
            "SELECT COALESCE(pv.price_override, p.base_price) "
            "FROM product_variants pv JOIN products p ON p.id = pv.product_id "
            "WHERE pv.id = :vid"
        ), {"vid": vid}).fetchone()
        if not price_row:
            raise HTTPException(status_code=400, detail=f"Variant {vid} not found")

        unit_price = float(price_row[0])
        resolved_items.append({"vid": vid, "qty": qty, "unit_price": unit_price})
        subtotal += unit_price * qty

    discount_amount = float(order_in.get("discount_amount", 0))
    shipping_cost = float(order_in.get("shipping_cost", 0))
    tax_amount = float(order_in.get("tax_amount", 0))
    total_amount = subtotal - discount_amount + shipping_cost + tax_amount

    # Build notes with address info
    full_notes = ""
    if shipping_address:
        full_notes += f"Shipping: {shipping_address}"
    if billing_address:
        full_notes += f" | Billing: {billing_address}"
    if notes:
        full_notes += f" | {notes}"

    # Create order (shipping_address_id is now optional)
    result = db.execute(_text("""
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
    })
    order_id = result.fetchone()[0]

    # Create order items & update inventory
    for ri in resolved_items:
        db.execute(_text(
            "INSERT INTO order_items (order_id, variant_id, quantity, unit_price, discount_amount) "
            "VALUES (:oid, :vid, :qty, :up, 0)"
        ), {"oid": order_id, "vid": ri["vid"], "qty": ri["qty"], "up": ri["unit_price"]})

        # Reserve stock
        db.execute(_text(
            "UPDATE inventory SET reserved_stock = reserved_stock + :qty WHERE variant_id = :vid"
        ), {"qty": ri["qty"], "vid": ri["vid"]})

    # Clear cart after order
    db.execute(_text(
        "DELETE FROM cart_items WHERE cart_id = (SELECT id FROM carts WHERE customer_id = :cid)"
    ), {"cid": current_user.id})

    db.commit()
    return {"id": order_id, "order_number": order_number, "total_amount": total_amount, "status": "pending"}


@orders_router.get("/me")
def get_my_orders(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return all orders for the current user."""
    from sqlalchemy import text as _text
    rows = db.execute(_text("""
        SELECT o.id, o.order_number, o.status::text, o.subtotal, o.discount_amount,
               o.shipping_cost, o.tax_amount, o.total_amount, o.notes,
               o.order_date, o.created_at,
               COUNT(oi.id) AS item_count
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        WHERE o.customer_id = :cid
        GROUP BY o.id
        ORDER BY o.order_date DESC
    """), {"cid": current_user.id}).fetchall()
    return [
        {
            "id": r[0], "order_number": r[1], "status": r[2],
            "subtotal": float(r[3]) if r[3] else 0,
            "discount_amount": float(r[4]) if r[4] else 0,
            "shipping_cost": float(r[5]) if r[5] else 0,
            "tax_amount": float(r[6]) if r[6] else 0,
            "total_amount": float(r[7]) if r[7] else 0,
            "notes": r[8],
            "order_date": r[9].isoformat() if r[9] else None,
            "created_at": r[10].isoformat() if r[10] else None,
            "item_count": int(r[11]),
        }
        for r in rows
    ]


@orders_router.get("", dependencies=[Depends(require_admin)])
def list_all_orders(db: Session = Depends(get_db)):
    """Return all orders (admin only)."""
    from sqlalchemy import text as _text
    rows = db.execute(_text("""
        SELECT o.id, o.order_number, o.customer_id, o.status::text,
               o.subtotal, o.discount_amount, o.shipping_cost, o.tax_amount,
               o.total_amount, o.order_date, o.created_at,
               c.email AS customer_email,
               COUNT(oi.id) AS item_count
        FROM orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id, c.email
        ORDER BY o.order_date DESC
    """)).fetchall()
    return [
        {
            "id": r[0], "order_number": r[1], "customer_id": r[2], "status": r[3],
            "subtotal": float(r[4]) if r[4] else 0,
            "discount_amount": float(r[5]) if r[5] else 0,
            "shipping_cost": float(r[6]) if r[6] else 0,
            "tax_amount": float(r[7]) if r[7] else 0,
            "total_amount": float(r[8]) if r[8] else 0,
            "order_date": r[9].isoformat() if r[9] else None,
            "created_at": r[10].isoformat() if r[10] else None,
            "customer_email": r[11],
            "item_count": int(r[12]),
        }
        for r in rows
    ]


@orders_router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get a single order with its items."""
    from sqlalchemy import text as _text
    order = db.execute(_text("""
        SELECT o.id, o.order_number, o.customer_id, o.status::text,
               o.subtotal, o.discount_amount, o.shipping_cost, o.tax_amount,
               o.total_amount, o.notes, o.order_date, o.created_at
        FROM orders o WHERE o.id = :oid
    """), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[2] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this order")

    items = db.execute(_text("""
        SELECT oi.id, oi.variant_id, oi.quantity, oi.unit_price, oi.line_total,
               p.name AS product_name, pv.sku,
               co.name AS color_name, sz.name AS size_name
        FROM order_items oi
        JOIN product_variants pv ON pv.id = oi.variant_id
        JOIN products p ON p.id = pv.product_id
        LEFT JOIN colors co ON co.id = pv.color_id
        LEFT JOIN sizes  sz ON sz.id = pv.size_id
        WHERE oi.order_id = :oid
    """), {"oid": order_id}).fetchall()

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
        "items": [
            {
                "id": it[0], "variant_id": it[1], "quantity": it[2],
                "unit_price": float(it[3]) if it[3] else 0,
                "line_total": float(it[4]) if it[4] else 0,
                "product_name": it[5], "sku": it[6],
                "color_name": it[7], "size_name": it[8],
            }
            for it in items
        ],
    }


@orders_router.put("/{order_id}/status", dependencies=[Depends(require_admin)])
def change_order_status(order_id: int, status_in: dict, db: Session = Depends(get_db)):
    """Update order status (admin only)."""
    from sqlalchemy import text as _text
    new_status = status_in.get("status", "pending")
    db.execute(_text(
        "UPDATE orders SET status = :status::order_status, updated_at = now() WHERE id = :oid"
    ), {"status": new_status, "oid": order_id})
    db.commit()
    return {"id": order_id, "status": new_status, "message": "Order status updated"}


@order_items_router.post("/{order_id}/items", status_code=status.HTTP_201_CREATED)
def add_item_to_order(order_id: int, item_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add an item to an existing order (raw SQL)."""
    from sqlalchemy import text as _text
    # Verify order exists and belongs to user
    order = db.execute(_text(
        "SELECT customer_id FROM orders WHERE id = :oid"
    ), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to modify this order")

    vid = item_in.get("variant_id")
    qty = item_in.get("quantity", 1)
    price_row = db.execute(_text(
        "SELECT COALESCE(pv.price_override, p.base_price) "
        "FROM product_variants pv JOIN products p ON p.id = pv.product_id "
        "WHERE pv.id = :vid"
    ), {"vid": vid}).fetchone()
    if not price_row:
        raise HTTPException(status_code=400, detail=f"Variant {vid} not found")
    unit_price = float(price_row[0])
    line_total = unit_price * qty

    result = db.execute(_text(
        "INSERT INTO order_items (order_id, variant_id, quantity, unit_price, discount_amount, line_total) "
        "VALUES (:oid, :vid, :qty, :up, 0, :lt) RETURNING id"
    ), {"oid": order_id, "vid": vid, "qty": qty, "up": unit_price, "lt": line_total})
    db.commit()
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
    from sqlalchemy import text as _text
    order_id = payment_in.get("order_id")
    order = db.execute(_text(
        "SELECT customer_id FROM orders WHERE id = :oid"
    ), {"oid": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin and order[0] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to pay for this order")

    result = db.execute(_text(
        "INSERT INTO payments (order_id, payment_method, payment_status, amount, transaction_ref) "
        "VALUES (:oid, :method, :status, :amount, :ref) RETURNING id"
    ), {
        "oid": order_id,
        "method": payment_in.get("payment_method", "cash_on_delivery"),
        "status": payment_in.get("payment_status", "pending"),
        "amount": payment_in.get("amount", 0),
        "ref": payment_in.get("transaction_reference") or payment_in.get("transaction_ref"),
    })
    payment_id = result.fetchone()[0]

    # If paid, update order status
    if payment_in.get("payment_status") == "paid":
        db.execute(_text(
            "UPDATE orders SET status = 'confirmed', updated_at = now() WHERE id = :oid"
        ), {"oid": order_id})

    db.commit()
    return {"id": payment_id, "order_id": order_id, "message": "Payment recorded"}


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
    
    result = db.execute(_text(
        "INSERT INTO shipments (order_id, tracking_number, carrier_name, shipment_status) "
        "VALUES (:oid, :tn, :carrier, :status) "
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
    db.commit()
    return {"id": result.fetchone()[0], "message": "Shipment created"}


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
        "carrier": row[3], "shipment_status": row[4],
        "shipped_at": row[5].isoformat() if row[5] else None,
        "estimated_delivery": row[6].isoformat() if row[6] else None,
        "delivered_at": row[7].isoformat() if row[7] else None,
        "created_at": row[8].isoformat() if row[8] else None,
    }


@reviews_router.post("", status_code=status.HTTP_201_CREATED)
def create_review(review_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Submit a product review."""
    from sqlalchemy import text as _text
    result = db.execute(_text(
        "INSERT INTO reviews (customer_id, variant_id, order_id, rating, title, body) "
        "VALUES (:cid, :vid, :oid, :rating, :title, :body) RETURNING id"
    ), {
        "cid": current_user.id,
        "vid": review_in.get("variant_id"),
        "oid": review_in.get("order_id"),
        "rating": review_in.get("rating"),
        "title": review_in.get("title"),
        "body": review_in.get("body"),
    })
    db.commit()
    return {"id": result.fetchone()[0], "message": "Review submitted"}


@reviews_router.get("/product/{product_id}")
def list_reviews_for_product(product_id: int, db: Session = Depends(get_db)):
    """Return all reviews for a product using raw SQL for schema compatibility."""
    try:
        from sqlalchemy import text as _text
        rows = db.execute(_text(
            "SELECT r.id, r.customer_id, p.id AS product_id, r.rating, "
            "COALESCE(r.title, '') || CASE WHEN r.body IS NOT NULL THEN ': ' || r.body ELSE '' END AS comment, "
            "r.created_at, c.email as customer_email "
            "FROM reviews r "
            "JOIN product_variants pv ON pv.id = r.variant_id "
            "JOIN products p ON p.id = pv.product_id "
            "LEFT JOIN customers c ON c.id = r.customer_id "
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
            }
            for row in rows
        ]
    except Exception:
        return []


@cart_items_router.post("", status_code=status.HTTP_201_CREATED)
def add_to_cart(cart_item_in: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add a variant to the current user's cart (raw SQL for Supabase schema)."""
    from sqlalchemy import text as _text
    variant_id = cart_item_in.get("variant_id")
    quantity = cart_item_in.get("quantity", 1)

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
        db.execute(_text(
            "UPDATE cart_items SET quantity = :qty, updated_at = now() WHERE id = :iid"
        ), {"qty": new_qty, "iid": existing[0]})
        db.commit()
        return {"id": existing[0], "variant_id": variant_id, "quantity": new_qty, "message": "Cart updated"}
    else:
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
            COALESCE(inv.current_stock - inv.reserved_stock, 0) AS available_stock
        FROM carts c
        JOIN cart_items ci ON ci.cart_id = c.id
        JOIN product_variants pv ON pv.id = ci.variant_id
        JOIN products p ON p.id = pv.product_id
        LEFT JOIN colors co ON co.id = pv.color_id
        LEFT JOIN sizes  sz ON sz.id = pv.size_id
        LEFT JOIN inventory inv ON inv.variant_id = pv.id
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
    quantity = cart_item_in.get("quantity", 1)
    # Verify ownership
    row = db.execute(_text(
        "SELECT ci.id FROM cart_items ci "
        "JOIN carts c ON c.id = ci.cart_id "
        "WHERE ci.id = :iid AND c.customer_id = :cid"
    ), {"iid": cart_item_id, "cid": current_user.id}).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
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
        "valid_until, max_uses, used_count, description "
        "FROM coupons WHERE code = :code AND is_active = true"
    ), {"code": code}).fetchone()

    if not row:
        return {"valid": False, "message": "Invalid or expired coupon code", "discount": 0}

    coupon_id, coupon_type, value, min_amt, max_discount, valid_until, max_uses, used_count, description = row

    import datetime
    if valid_until and valid_until < datetime.datetime.now(datetime.timezone.utc):
        return {"valid": False, "message": "This coupon has expired", "discount": 0}
    if min_amt and subtotal < float(min_amt):
        return {"valid": False, "message": f"Minimum order amount is {min_amt} BDT", "discount": 0}
    if max_uses and used_count >= max_uses:
        return {"valid": False, "message": "This coupon has reached its usage limit", "discount": 0}

    discount = 0.0
    if coupon_type == "percentage":
        discount = subtotal * float(value) / 100
        if max_discount:
            discount = min(discount, float(max_discount))
    else:
        discount = min(float(value), subtotal)

    return {
        "valid": True,
        "coupon_id": coupon_id,
        "discount": round(discount, 2),
        "message": description or f"Coupon applied! You save {discount:.2f} BDT",
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
        
    result = db.execute(_text("""
        INSERT INTO coupons (
            code, coupon_type, value, min_order_amount, max_discount_amount,
            max_uses, valid_until, description, is_active
        ) VALUES (
            :code, :type, :value, :min_amt, :max_disc, :max_uses, :valid, :desc, :active
        ) RETURNING id
    """), {
        "code": code,
        "type": payload.get("coupon_type", "percentage"),
        "value": payload.get("value", 0),
        "min_amt": payload.get("min_order_amount"),
        "max_disc": payload.get("max_discount_amount"),
        "max_uses": payload.get("max_uses"),
        "valid": payload.get("valid_until"),
        "desc": payload.get("description"),
        "active": payload.get("is_active", True)
    })
    db.commit()
    return {"id": result.fetchone()[0], "message": "Coupon created"}


@coupon_validate_router.put("/{coupon_id}", dependencies=[Depends(require_admin)])
def update_coupon_admin(coupon_id: int, payload: dict, db: Session = Depends(get_db)):
    from sqlalchemy import text as _text
    if "is_active" in payload:
        db.execute(_text("UPDATE coupons SET is_active = :active, updated_at = now() WHERE id = :id"), 
                   {"active": payload["is_active"], "id": coupon_id})
        db.commit()
    return {"id": coupon_id, "message": "Coupon updated"}

