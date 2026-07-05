-- =============================================================================
-- FashionHub — Migration: 003_functions.sql
-- Purpose  : PostgreSQL stored functions for business logic
-- Run after: 002_indexes.sql
-- =============================================================================
-- All functions use SECURITY DEFINER where they access multiple tables.
-- Language: PL/pgSQL for procedural logic, SQL for simple selectors.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- FUNCTION 1: calculate_order_total
-- Purpose: Recomputes and updates subtotal, discount, tax, and total for an
--          order from its line items. Called after order item changes.
-- Returns: NUMERIC — the final total_amount
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_order_total(p_order_id BIGINT)
RETURNS NUMERIC(12,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_subtotal          NUMERIC(12,2);
    v_discount_amount   NUMERIC(12,2);
    v_shipping_cost     NUMERIC(10,2);
    v_tax_rate          NUMERIC(5,4) := 0.05;   -- 5% VAT
    v_tax_amount        NUMERIC(10,2);
    v_total             NUMERIC(12,2);
    v_coupon_value      NUMERIC(12,2) := 0;
    v_coupon_type       coupon_type;
    v_coupon_min_order  NUMERIC(12,2);
    v_coupon_max_disc   NUMERIC(12,2);
BEGIN
    -- Step 1: Sum all line totals from order_items
    SELECT COALESCE(SUM(line_total), 0)
    INTO v_subtotal
    FROM order_items
    WHERE order_id = p_order_id;

    -- Step 2: Get shipping cost from the linked shipping method
    SELECT COALESCE(sm.base_rate, 0)
    INTO v_shipping_cost
    FROM orders o
    LEFT JOIN shipping_methods sm ON sm.id = o.shipping_method_id
    WHERE o.id = p_order_id;

    -- Step 3: Calculate coupon discount
    SELECT
        c.coupon_type,
        c.value,
        c.min_order_amount,
        c.max_discount_amount
    INTO v_coupon_type, v_coupon_value, v_coupon_min_order, v_coupon_max_disc
    FROM orders o
    JOIN coupons c ON c.id = o.coupon_id
    WHERE o.id = p_order_id AND o.coupon_id IS NOT NULL;

    v_discount_amount := 0;
    IF v_coupon_type IS NOT NULL AND v_subtotal >= v_coupon_min_order THEN
        IF v_coupon_type = 'percentage' THEN
            v_discount_amount := v_subtotal * (v_coupon_value / 100);
            -- Apply cap if set
            IF v_coupon_max_disc IS NOT NULL THEN
                v_discount_amount := LEAST(v_discount_amount, v_coupon_max_disc);
            END IF;
        ELSE
            v_discount_amount := LEAST(v_coupon_value, v_subtotal);
        END IF;
    END IF;

    -- Step 4: Tax on (subtotal - discount)
    v_tax_amount := ROUND((v_subtotal - v_discount_amount) * v_tax_rate, 2);

    -- Step 5: Final total
    v_total := v_subtotal - v_discount_amount + v_shipping_cost + v_tax_amount;
    v_total := GREATEST(v_total, 0);

    -- Step 6: Update order row
    UPDATE orders
    SET
        subtotal        = v_subtotal,
        discount_amount = v_discount_amount,
        shipping_cost   = v_shipping_cost,
        tax_amount      = v_tax_amount,
        total_amount    = v_total,
        updated_at      = NOW()
    WHERE id = p_order_id;

    RETURN v_total;
END;
$$;

COMMENT ON FUNCTION calculate_order_total(BIGINT) IS
'Recomputes and persists all order financial totals (subtotal, discount, tax, shipping, total). Call after order item changes.';

-- ---------------------------------------------------------------------------
-- FUNCTION 2: get_customer_lifetime_value
-- Purpose: Calculates total spending by a customer across all delivered orders.
-- Returns: NUMERIC — cumulative spend in default currency
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_customer_lifetime_value(p_customer_id BIGINT)
RETURNS NUMERIC(14,2)
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(SUM(o.total_amount), 0.00)
    FROM orders o
    JOIN payments p ON p.order_id = o.id
    WHERE o.customer_id = p_customer_id
      AND o.status IN ('delivered', 'returned', 'refunded')
      AND p.payment_status = 'paid';
$$;

COMMENT ON FUNCTION get_customer_lifetime_value(BIGINT) IS
'Returns total amount paid by a customer across all completed orders (delivered/returned/refunded with paid payment).';

-- ---------------------------------------------------------------------------
-- FUNCTION 3: get_available_stock
-- Purpose: Returns total available stock for a variant across ALL warehouses.
-- Returns: INTEGER — sum of available_stock across all warehouse locations
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_available_stock(p_variant_id BIGINT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(SUM(available_stock), 0)
    FROM inventory
    WHERE variant_id = p_variant_id;
$$;

COMMENT ON FUNCTION get_available_stock(BIGINT) IS
'Aggregates available_stock for a variant across all warehouses. Used for add-to-cart validation.';

-- ---------------------------------------------------------------------------
-- FUNCTION 4: get_product_average_rating
-- Purpose: Computes the average rating for a product (via its variants).
-- Returns: NUMERIC(3,2) — average rating between 1.00 and 5.00
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_product_average_rating(p_product_id BIGINT)
RETURNS NUMERIC(3,2)
LANGUAGE sql
STABLE
AS $$
    SELECT ROUND(AVG(r.rating)::NUMERIC, 2)
    FROM reviews r
    JOIN product_variants pv ON pv.id = r.variant_id
    WHERE pv.product_id = p_product_id
      AND r.is_approved = TRUE;
$$;

COMMENT ON FUNCTION get_product_average_rating(BIGINT) IS
'Computes approved review average for a product via its variants. Returns NULL if no reviews.';

-- ---------------------------------------------------------------------------
-- FUNCTION 5: get_best_selling_products
-- Purpose: Returns top N products by total units sold in a date range.
-- Returns: TABLE of (product_id, product_name, total_units_sold, total_revenue)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_best_selling_products(
    p_limit     INTEGER     DEFAULT 10,
    p_from_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    p_to_date   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    product_id      BIGINT,
    product_name    TEXT,
    brand_name      TEXT,
    total_units_sold BIGINT,
    total_revenue   NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        p.id                            AS product_id,
        p.name                          AS product_name,
        b.name                          AS brand_name,
        SUM(oi.quantity)::BIGINT        AS total_units_sold,
        SUM(oi.line_total)              AS total_revenue
    FROM order_items oi
    JOIN product_variants pv ON pv.id = oi.variant_id
    JOIN products p          ON p.id  = pv.product_id
    JOIN brands b            ON b.id  = p.brand_id
    JOIN orders o            ON o.id  = oi.order_id
    WHERE o.status NOT IN ('cancelled', 'returned', 'refunded')
      AND o.order_date BETWEEN p_from_date AND p_to_date
    GROUP BY p.id, p.name, b.name
    ORDER BY total_units_sold DESC
    LIMIT p_limit;
$$;

COMMENT ON FUNCTION get_best_selling_products(INTEGER, TIMESTAMPTZ, TIMESTAMPTZ) IS
'Returns top N products by units sold in a date range. Excludes cancelled/returned/refunded orders.';

-- ---------------------------------------------------------------------------
-- FUNCTION 6: get_monthly_revenue
-- Purpose: Returns revenue aggregated by month for a given year.
-- Returns: TABLE of (month, order_count, total_revenue, avg_order_value)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_monthly_revenue(p_year INTEGER DEFAULT EXTRACT(YEAR FROM NOW())::INTEGER)
RETURNS TABLE (
    month_number    INTEGER,
    month_name      TEXT,
    order_count     BIGINT,
    total_revenue   NUMERIC,
    avg_order_value NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        EXTRACT(MONTH FROM o.order_date)::INTEGER       AS month_number,
        TO_CHAR(o.order_date, 'Month')                  AS month_name,
        COUNT(o.id)                                     AS order_count,
        COALESCE(SUM(o.total_amount), 0)                AS total_revenue,
        COALESCE(AVG(o.total_amount), 0)                AS avg_order_value
    FROM orders o
    WHERE EXTRACT(YEAR FROM o.order_date) = p_year
      AND o.status NOT IN ('cancelled')
    GROUP BY EXTRACT(MONTH FROM o.order_date), TO_CHAR(o.order_date, 'Month')
    ORDER BY month_number;
$$;

COMMENT ON FUNCTION get_monthly_revenue(INTEGER) IS
'Monthly revenue breakdown for a given year. Excludes cancelled orders.';

-- ---------------------------------------------------------------------------
-- FUNCTION 7: calculate_stock_valuation
-- Purpose: Computes total inventory value = SUM(stock * selling_price) per warehouse.
-- Returns: TABLE of (warehouse_id, warehouse_name, total_units, total_value)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_stock_valuation()
RETURNS TABLE (
    warehouse_id    BIGINT,
    warehouse_name  TEXT,
    total_units     BIGINT,
    total_value     NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        w.id                                                AS warehouse_id,
        w.name                                              AS warehouse_name,
        SUM(inv.current_stock)::BIGINT                      AS total_units,
        SUM(inv.current_stock *
            COALESCE(pv.price_override, p.base_price))      AS total_value
    FROM inventory inv
    JOIN product_variants pv ON pv.id = inv.variant_id
    JOIN products p          ON p.id  = pv.product_id
    JOIN warehouses w        ON w.id  = inv.warehouse_id
    GROUP BY w.id, w.name
    ORDER BY total_value DESC;
$$;

COMMENT ON FUNCTION calculate_stock_valuation() IS
'Computes inventory valuation per warehouse using variant price (with base_price fallback via COALESCE).';

-- ---------------------------------------------------------------------------
-- FUNCTION 8: validate_coupon
-- Purpose: Validates a coupon code for a given customer and order amount.
--          Returns discount amount or 0 with a status message.
-- Returns: TABLE of (is_valid, discount_amount, message)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION validate_coupon(
    p_code          VARCHAR(50),
    p_customer_id   BIGINT,
    p_order_amount  NUMERIC(12,2)
)
RETURNS TABLE (
    is_valid        BOOLEAN,
    discount_amount NUMERIC(12,2),
    message         TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_coupon        RECORD;
    v_already_used  BOOLEAN;
    v_discount      NUMERIC(12,2);
BEGIN
    -- Step 1: Find the coupon
    SELECT * INTO v_coupon FROM coupons WHERE code = UPPER(TRIM(p_code));

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 0::NUMERIC(12,2), 'Coupon code not found.';
        RETURN;
    END IF;

    -- Step 2: Check active
    IF NOT v_coupon.is_active THEN
        RETURN QUERY SELECT FALSE, 0::NUMERIC(12,2), 'This coupon is no longer active.';
        RETURN;
    END IF;

    -- Step 3: Check expiry
    IF v_coupon.valid_until IS NOT NULL AND NOW() > v_coupon.valid_until THEN
        RETURN QUERY SELECT FALSE, 0::NUMERIC(12,2), 'This coupon has expired.';
        RETURN;
    END IF;

    -- Step 4: Check minimum order
    IF p_order_amount < v_coupon.min_order_amount THEN
        RETURN QUERY SELECT FALSE, 0::NUMERIC(12,2),
            FORMAT('Minimum order of %.2f required for this coupon.', v_coupon.min_order_amount);
        RETURN;
    END IF;

    -- Step 5: Check usage limit
    IF v_coupon.max_uses IS NOT NULL AND v_coupon.used_count >= v_coupon.max_uses THEN
        RETURN QUERY SELECT FALSE, 0::NUMERIC(12,2), 'This coupon has reached its usage limit.';
        RETURN;
    END IF;

    -- Step 6: Check if customer already used this coupon
    SELECT EXISTS (
        SELECT 1 FROM coupon_usages
        WHERE coupon_id = v_coupon.id AND customer_id = p_customer_id
    ) INTO v_already_used;

    IF v_already_used THEN
        RETURN QUERY SELECT FALSE, 0::NUMERIC(12,2), 'You have already used this coupon.';
        RETURN;
    END IF;

    -- Step 7: Calculate discount
    IF v_coupon.coupon_type = 'percentage' THEN
        v_discount := p_order_amount * (v_coupon.value / 100);
        IF v_coupon.max_discount_amount IS NOT NULL THEN
            v_discount := LEAST(v_discount, v_coupon.max_discount_amount);
        END IF;
    ELSE
        v_discount := LEAST(v_coupon.value, p_order_amount);
    END IF;

    RETURN QUERY SELECT TRUE, ROUND(v_discount, 2),
        FORMAT('Coupon applied! You save %.2f.', v_discount);
END;
$$;

COMMENT ON FUNCTION validate_coupon(VARCHAR, BIGINT, NUMERIC) IS
'Full coupon validation: checks existence, active, expiry, min order, usage limit, and per-customer reuse.';

-- ---------------------------------------------------------------------------
-- FUNCTION 9: calculate_shipment_eta
-- Purpose: Estimates delivery date based on order date and shipping method.
-- Returns: DATE — estimated delivery date
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_shipment_eta(p_order_id BIGINT)
RETURNS DATE
LANGUAGE sql
STABLE
AS $$
    SELECT
        (o.order_date + INTERVAL '1 day' * sm.estimated_days)::DATE
    FROM orders o
    JOIN shipping_methods sm ON sm.id = o.shipping_method_id
    WHERE o.id = p_order_id;
$$;

COMMENT ON FUNCTION calculate_shipment_eta(BIGINT) IS
'Returns estimated delivery date = order_date + shipping_method.estimated_days.';

-- ---------------------------------------------------------------------------
-- FUNCTION 10: check_return_eligibility
-- Purpose: Checks whether an order is eligible for return.
--          Rules: (1) order delivered, (2) within 7-day return window,
--                (3) no existing pending/approved return.
-- Returns: TABLE of (is_eligible, reason)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_return_eligibility(
    p_order_id      BIGINT,
    p_customer_id   BIGINT
)
RETURNS TABLE (is_eligible BOOLEAN, reason TEXT)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_order         RECORD;
    v_existing_rr   BOOLEAN;
    v_return_window INTERVAL := INTERVAL '7 days';
BEGIN
    -- Step 1: Get order
    SELECT * INTO v_order FROM orders
    WHERE id = p_order_id AND customer_id = p_customer_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Order not found or does not belong to you.';
        RETURN;
    END IF;

    -- Step 2: Must be delivered
    IF v_order.status != 'delivered' THEN
        RETURN QUERY SELECT FALSE,
            FORMAT('Order status is ''%s''. Only delivered orders can be returned.', v_order.status);
        RETURN;
    END IF;

    -- Step 3: Check return window (7 days from delivery via shipment)
    IF EXISTS (
        SELECT 1 FROM shipments s
        WHERE s.order_id = p_order_id
          AND s.delivered_at < NOW() - v_return_window
    ) THEN
        RETURN QUERY SELECT FALSE, 'Return window of 7 days has expired.';
        RETURN;
    END IF;

    -- Step 4: Check no existing active return request
    SELECT EXISTS (
        SELECT 1 FROM return_requests rr
        WHERE rr.order_id = p_order_id
          AND rr.status IN ('pending', 'approved')
    ) INTO v_existing_rr;

    IF v_existing_rr THEN
        RETURN QUERY SELECT FALSE, 'A return request for this order already exists.';
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'Order is eligible for return.';
END;
$$;

COMMENT ON FUNCTION check_return_eligibility(BIGINT, BIGINT) IS
'Validates return eligibility: delivered status, 7-day window, and no duplicate return request.';

-- ---------------------------------------------------------------------------
-- FUNCTION 11: generate_order_number (helper used by trigger)
-- Purpose: Generates a unique, formatted order number: ORD-YYYYMMDD-XXXXX
-- Returns: VARCHAR(20)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS VARCHAR(20)
LANGUAGE plpgsql
AS $$
DECLARE
    v_seq   BIGINT;
    v_date  TEXT;
BEGIN
    SELECT nextval('order_number_seq') INTO v_seq;
    v_date := TO_CHAR(NOW(), 'YYYYMMDD');
    RETURN 'ORD-' || v_date || '-' || LPAD(v_seq::TEXT, 5, '0');
END;
$$;

COMMENT ON FUNCTION generate_order_number() IS
'Generates formatted order number: ORD-YYYYMMDD-NNNNN using order_number_seq sequence.';

-- ---------------------------------------------------------------------------
-- FUNCTION 12: generate_invoice_number (helper used by trigger)
-- Purpose: Generates a unique invoice number: INV-YYYYMMDD-XXXXX
-- Returns: VARCHAR(30)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_invoice_number()
RETURNS VARCHAR(30)
LANGUAGE plpgsql
AS $$
DECLARE
    v_seq   BIGINT;
    v_date  TEXT;
BEGIN
    SELECT nextval('invoice_number_seq') INTO v_seq;
    v_date := TO_CHAR(NOW(), 'YYYYMMDD');
    RETURN 'INV-' || v_date || '-' || LPAD(v_seq::TEXT, 5, '0');
END;
$$;

COMMENT ON FUNCTION generate_invoice_number() IS
'Generates formatted invoice number: INV-YYYYMMDD-NNNNN using invoice_number_seq sequence.';

-- =============================================================================
-- END OF FUNCTIONS (12 functions)
-- Run next: 004_triggers.sql
-- =============================================================================
