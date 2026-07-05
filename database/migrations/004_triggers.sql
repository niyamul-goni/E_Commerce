-- =============================================================================
-- FashionHub — Migration: 004_triggers.sql
-- Purpose  : PostgreSQL triggers for business rule enforcement
-- Run after: 003_functions.sql
-- =============================================================================
-- Trigger philosophy:
--   Triggers enforce INVARIANTS that cannot be expressed as static constraints.
--   They run at the database layer so no application code can bypass them.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- UTILITY: Universal updated_at trigger function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;
COMMENT ON FUNCTION fn_set_updated_at() IS
'Universal trigger function: sets updated_at = NOW() on any UPDATE.';

-- Apply to every table that has updated_at
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'customers', 'customer_profiles', 'customer_addresses', 'carts',
        'cart_items', 'brands', 'suppliers', 'categories', 'subcategories',
        'collections', 'warehouses', 'products', 'product_variants',
        'shipping_methods', 'coupons', 'orders', 'payments', 'shipments',
        'invoices', 'return_requests', 'refunds', 'reviews', 'review_replies',
        'admins', 'inventory'
    ]
    LOOP
        EXECUTE FORMAT(
            'DROP TRIGGER IF EXISTS trg_%I_updated_at ON %I;
             CREATE TRIGGER trg_%I_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();',
            tbl, tbl, tbl, tbl
        );
    END LOOP;
END;
$$;

-- ---------------------------------------------------------------------------
-- TRIGGER 1: Auto-generate order_number on INSERT
-- Rationale: Business requires human-readable, sequential order numbers.
--            Generated at DB level so concurrent inserts never collide.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_generate_order_number()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
        NEW.order_number := generate_order_number();
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_generate_number
    BEFORE INSERT ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_generate_order_number();

COMMENT ON FUNCTION fn_generate_order_number() IS
'Auto-generates ORD-YYYYMMDD-NNNNN if order_number not provided on INSERT.';

-- ---------------------------------------------------------------------------
-- TRIGGER 2: Log order status changes into order_status_history
-- Rationale: Complete audit trail of order lifecycle transitions.
--            Never loses the "what was it before" context.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_log_order_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Log initial status creation
        INSERT INTO order_status_history (order_id, from_status, to_status, notes)
        VALUES (NEW.id, NULL, NEW.status, 'Order created');
    ELSIF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        -- Log every status transition
        INSERT INTO order_status_history (order_id, from_status, to_status, notes)
        VALUES (NEW.id, OLD.status, NEW.status,
                FORMAT('Status changed from %s to %s', OLD.status, NEW.status));
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_status_log
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_log_order_status_change();

COMMENT ON FUNCTION fn_log_order_status_change() IS
'Records every order status change into order_status_history (INSERT and UPDATE events).';

-- ---------------------------------------------------------------------------
-- TRIGGER 3: Deduct inventory stock when order status becomes 'confirmed'
-- Rationale: Stock should only be deducted when payment is confirmed,
--            not when order is placed (to allow cancellation without adjustment).
--            reserved_stock decreases, current_stock decreases (net change on inventory).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_deduct_inventory_on_confirm()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_item      RECORD;
    v_inv       RECORD;
BEGIN
    -- Only trigger when transitioning TO 'confirmed'
    IF NEW.status = 'confirmed' AND
       (OLD.status IS NULL OR OLD.status != 'confirmed') THEN

        FOR v_item IN
            SELECT variant_id, quantity FROM order_items WHERE order_id = NEW.id
        LOOP
            -- Find best warehouse (most available stock)
            SELECT * INTO v_inv
            FROM inventory
            WHERE variant_id = v_item.variant_id
              AND available_stock >= v_item.quantity
            ORDER BY available_stock DESC
            LIMIT 1;

            IF NOT FOUND THEN
                RAISE EXCEPTION
                    'Insufficient stock for variant_id=%. Cannot confirm order.',
                    v_item.variant_id;
            END IF;

            -- Deduct current_stock and release reserved_stock
            UPDATE inventory
            SET current_stock  = current_stock - v_item.quantity,
                reserved_stock = GREATEST(reserved_stock - v_item.quantity, 0),
                updated_at     = NOW()
            WHERE id = v_inv.id;

            -- Record movement
            INSERT INTO inventory_movements
                (inventory_id, movement_type, quantity, reference_type, reference_id, notes)
            VALUES
                (v_inv.id, 'sale', -v_item.quantity, 'order', NEW.id,
                 FORMAT('Stock deducted for confirmed order %s', NEW.order_number));
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_deduct_inventory
    AFTER UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_deduct_inventory_on_confirm();

COMMENT ON FUNCTION fn_deduct_inventory_on_confirm() IS
'Deducts inventory and logs movements when order status changes to confirmed. Raises exception if stock insufficient.';

-- ---------------------------------------------------------------------------
-- TRIGGER 4: Reserve stock when order is placed (status = 'pending')
-- Rationale: Reserves stock during checkout to prevent overselling.
--            reserved_stock is released on cancellation or deducted on confirmation.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_reserve_inventory_on_order()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_item  RECORD;
    v_inv   RECORD;
BEGIN
    -- Only on new INSERT with status 'pending'
    IF TG_OP = 'INSERT' AND NEW.status = 'pending' THEN
        FOR v_item IN
            SELECT variant_id, quantity FROM order_items WHERE order_id = NEW.id
        LOOP
            SELECT * INTO v_inv
            FROM inventory
            WHERE variant_id = v_item.variant_id
              AND available_stock >= v_item.quantity
            ORDER BY available_stock DESC
            LIMIT 1;

            IF NOT FOUND THEN
                RAISE EXCEPTION
                    'Variant % is out of stock. Cannot place order.',
                    v_item.variant_id;
            END IF;

            UPDATE inventory
            SET reserved_stock = reserved_stock + v_item.quantity,
                updated_at     = NOW()
            WHERE id = v_inv.id;
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_reserve_inventory
    AFTER INSERT ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_reserve_inventory_on_order();

COMMENT ON FUNCTION fn_reserve_inventory_on_order() IS
'Reserves inventory (increases reserved_stock) when a new pending order is created.';

-- ---------------------------------------------------------------------------
-- TRIGGER 5: Restore stock when order is cancelled
-- Rationale: On cancellation, reserved stock must be released back to available.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_restore_inventory_on_cancel()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_item  RECORD;
    v_inv   RECORD;
BEGIN
    -- Trigger on transition TO 'cancelled' FROM 'pending' or 'confirmed'
    IF NEW.status = 'cancelled' AND OLD.status IN ('pending', 'confirmed') THEN
        FOR v_item IN
            SELECT variant_id, quantity FROM order_items WHERE order_id = NEW.id
        LOOP
            -- Find the inventory record (pick first matching warehouse)
            SELECT * INTO v_inv
            FROM inventory
            WHERE variant_id = v_item.variant_id
            ORDER BY id
            LIMIT 1;

            IF FOUND THEN
                IF OLD.status = 'pending' THEN
                    -- Only reserved, not deducted — release reservation
                    UPDATE inventory
                    SET reserved_stock = GREATEST(reserved_stock - v_item.quantity, 0),
                        updated_at     = NOW()
                    WHERE id = v_inv.id;
                ELSE
                    -- Was confirmed (stock already deducted), restore current_stock
                    UPDATE inventory
                    SET current_stock = current_stock + v_item.quantity,
                        updated_at    = NOW()
                    WHERE id = v_inv.id;
                END IF;

                INSERT INTO inventory_movements
                    (inventory_id, movement_type, quantity, reference_type, reference_id, notes)
                VALUES
                    (v_inv.id, 'adjustment', v_item.quantity, 'order', NEW.id,
                     FORMAT('Stock restored on order cancellation: %s', NEW.order_number));
            END IF;
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_restore_on_cancel
    AFTER UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_restore_inventory_on_cancel();

COMMENT ON FUNCTION fn_restore_inventory_on_cancel() IS
'Restores inventory when order is cancelled; handles both pending (unreserve) and confirmed (restock) states.';

-- ---------------------------------------------------------------------------
-- TRIGGER 6: Restore stock when return is approved
-- Rationale: Returned items re-enter inventory. Movement type = 'return'.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_restore_inventory_on_return()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_item      RECORD;
    v_inv       RECORD;
BEGIN
    -- Trigger when return_request status changes to 'approved'
    IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
        -- Get all order items for the returned order
        FOR v_item IN
            SELECT oi.variant_id, oi.quantity
            FROM order_items oi
            WHERE oi.order_id = NEW.order_id
        LOOP
            SELECT * INTO v_inv
            FROM inventory
            WHERE variant_id = v_item.variant_id
            ORDER BY id LIMIT 1;

            IF FOUND THEN
                UPDATE inventory
                SET current_stock = current_stock + v_item.quantity,
                    updated_at    = NOW()
                WHERE id = v_inv.id;

                INSERT INTO inventory_movements
                    (inventory_id, movement_type, quantity, reference_type, reference_id, notes)
                VALUES
                    (v_inv.id, 'return', v_item.quantity, 'return_request', NEW.id,
                     FORMAT('Stock restored on approved return request #%s', NEW.id));
            END IF;
        END LOOP;

        -- Update parent order status to 'returned'
        UPDATE orders SET status = 'returned' WHERE id = NEW.order_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_return_restore_inventory
    AFTER UPDATE ON return_requests
    FOR EACH ROW
    EXECUTE FUNCTION fn_restore_inventory_on_return();

COMMENT ON FUNCTION fn_restore_inventory_on_return() IS
'Restores inventory and logs return movements when a return request is approved. Also updates order status.';

-- ---------------------------------------------------------------------------
-- TRIGGER 7: Prevent negative stock (hard safety guard)
-- Rationale: Belt-and-suspenders protection — even if a bug bypasses other triggers,
--            inventory can never go negative.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_prevent_negative_stock()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.current_stock < 0 THEN
        RAISE EXCEPTION
            'CONSTRAINT VIOLATION: current_stock cannot be negative. Attempted value: % for inventory_id: %',
            NEW.current_stock, NEW.id;
    END IF;
    IF NEW.reserved_stock < 0 THEN
        RAISE EXCEPTION
            'CONSTRAINT VIOLATION: reserved_stock cannot be negative. Attempted value: % for inventory_id: %',
            NEW.reserved_stock, NEW.id;
    END IF;
    IF NEW.reserved_stock > NEW.current_stock THEN
        RAISE EXCEPTION
            'CONSTRAINT VIOLATION: reserved_stock (%) cannot exceed current_stock (%) for inventory_id: %',
            NEW.reserved_stock, NEW.current_stock, NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_inventory_prevent_negative
    BEFORE INSERT OR UPDATE ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION fn_prevent_negative_stock();

COMMENT ON FUNCTION fn_prevent_negative_stock() IS
'Hard guard: raises exception if current_stock < 0, reserved_stock < 0, or reserved > current.';

-- ---------------------------------------------------------------------------
-- TRIGGER 8: Auto-generate invoice when order status = 'confirmed'
-- Rationale: Invoice is a business requirement upon payment confirmation.
--            Auto-generating ensures no order goes without an invoice.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_auto_create_invoice()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'confirmed' AND OLD.status != 'confirmed' THEN
        -- Only create if no invoice exists yet
        IF NOT EXISTS (SELECT 1 FROM invoices WHERE order_id = NEW.id) THEN
            INSERT INTO invoices
                (order_id, invoice_number, subtotal, tax_amount, discount_amount, total_amount)
            VALUES (
                NEW.id,
                generate_invoice_number(),
                NEW.subtotal,
                NEW.tax_amount,
                NEW.discount_amount,
                NEW.total_amount
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_auto_invoice
    AFTER UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_auto_create_invoice();

COMMENT ON FUNCTION fn_auto_create_invoice() IS
'Auto-creates invoice with formatted invoice number when order is confirmed.';

-- ---------------------------------------------------------------------------
-- TRIGGER 9: Increment coupon used_count when a coupon_usage is recorded
-- Rationale: used_count on coupons must stay in sync with coupon_usages rows.
--            Doing it in a trigger prevents inconsistency from direct INSERT bypasses.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_increment_coupon_usage()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE coupons
    SET used_count = used_count + 1,
        updated_at = NOW()
    WHERE id = NEW.coupon_id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_coupon_usages_increment
    AFTER INSERT ON coupon_usages
    FOR EACH ROW
    EXECUTE FUNCTION fn_increment_coupon_usage();

COMMENT ON FUNCTION fn_increment_coupon_usage() IS
'Keeps coupons.used_count synchronized with coupon_usages row count after each INSERT.';

-- ---------------------------------------------------------------------------
-- TRIGGER 10: Prevent duplicate review (belt-and-suspenders beyond UNIQUE constraint)
-- Rationale: The UNIQUE(customer_id, variant_id) constraint handles this at
--            the DB level. This trigger provides a clearer error message.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_prevent_duplicate_review()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM reviews
        WHERE customer_id = NEW.customer_id
          AND variant_id  = NEW.variant_id
          AND id != COALESCE(NEW.id, -1)
    ) THEN
        RAISE EXCEPTION
            'BUSINESS RULE VIOLATION: Customer % has already reviewed variant %. Only one review per purchase is allowed.',
            NEW.customer_id, NEW.variant_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reviews_prevent_duplicate
    BEFORE INSERT ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION fn_prevent_duplicate_review();

COMMENT ON FUNCTION fn_prevent_duplicate_review() IS
'Prevents duplicate reviews (customer, variant) with a business-friendly error message.';

-- ---------------------------------------------------------------------------
-- TRIGGER 11: Auto-create cart and wishlist on new customer registration
-- Rationale: Every customer should have exactly one cart and one wishlist.
--            Creating them automatically prevents null-pointer errors in the app.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_init_customer_cart_wishlist()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO carts     (customer_id) VALUES (NEW.id);
    INSERT INTO wishlists (customer_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_customers_init_cart_wishlist
    AFTER INSERT ON customers
    FOR EACH ROW
    EXECUTE FUNCTION fn_init_customer_cart_wishlist();

COMMENT ON FUNCTION fn_init_customer_cart_wishlist() IS
'Auto-creates one cart and one wishlist for every new customer on registration.';

-- =============================================================================
-- END OF TRIGGERS
-- Trigger count: 11 business triggers + 1 universal updated_at (applied to 25 tables)
-- Run next: 005_views.sql
-- =============================================================================
