-- =============================================================================
-- FashionHub — Migration: 005_views.sql
-- Purpose  : SQL Views and Materialized Views for reporting and API queries
-- Run after: 004_triggers.sql
-- =============================================================================
-- View design principles:
--   1. Views abstract complex JOIN logic from the application layer
--   2. Materialized Views pre-aggregate expensive computations
--   3. Views serve as the read layer for the API (FastAPI queries views, not raw tables)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- VIEW 1: available_products_view
-- Purpose: Products with stock > 0, including price (from variant or base),
--          brand, category, and aggregate inventory.
--          Used by the product listing API endpoint.
-- Concepts demonstrated: JOIN, COALESCE, aggregate subquery, GROUP BY
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW available_products_view AS
SELECT
    p.id                                                        AS product_id,
    p.name                                                      AS product_name,
    p.slug                                                      AS product_slug,
    p.base_price,
    p.is_featured,
    b.id                                                        AS brand_id,
    b.name                                                      AS brand_name,
    c.id                                                        AS category_id,
    c.name                                                      AS category_name,
    sc.id                                                       AS subcategory_id,
    sc.name                                                     AS subcategory_name,
    g.name                                                      AS gender,
    -- Primary image URL (scalar subquery)
    (SELECT image_url FROM product_images pi2
     WHERE pi2.product_id = p.id AND pi2.is_primary = TRUE
     LIMIT 1)                                                   AS primary_image_url,
    -- Average rating (scalar subquery using approved reviews)
    ROUND((SELECT AVG(r.rating)::NUMERIC
           FROM reviews r
           JOIN product_variants pv2 ON pv2.id = r.variant_id
           WHERE pv2.product_id = p.id AND r.is_approved = TRUE), 2) AS avg_rating,
    -- Count of approved reviews
    (SELECT COUNT(*) FROM reviews r
     JOIN product_variants pv3 ON pv3.id = r.variant_id
     WHERE pv3.product_id = p.id AND r.is_approved = TRUE)         AS review_count,
    -- Total available stock across all variants and warehouses
    COALESCE(SUM(inv.available_stock), 0)                      AS total_available_stock,
    -- Count of distinct active variants
    COUNT(DISTINCT pv.id)                                      AS variant_count
FROM products p
JOIN brands b           ON b.id  = p.brand_id
JOIN subcategories sc   ON sc.id = p.subcategory_id
JOIN categories c       ON c.id  = sc.category_id
LEFT JOIN genders g     ON g.id  = p.gender_id
LEFT JOIN product_variants pv ON pv.product_id = p.id AND pv.is_active = TRUE
LEFT JOIN inventory inv ON inv.variant_id = pv.id
WHERE p.is_active = TRUE
GROUP BY p.id, p.name, p.slug, p.base_price, p.is_featured,
         b.id, b.name, c.id, c.name, sc.id, sc.name, g.name
HAVING COALESCE(SUM(inv.available_stock), 0) > 0;

COMMENT ON VIEW available_products_view IS
'Product listing with stock > 0; includes brand, category, rating, primary image. Used by product list API.';

-- ---------------------------------------------------------------------------
-- VIEW 2: best_selling_products_view
-- Purpose: Products ranked by units sold (last 90 days).
--          Used by homepage "Best Sellers" section.
-- Concepts: JOIN, GROUP BY, ORDER BY, aggregate functions, date arithmetic
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW best_selling_products_view AS
SELECT
    p.id                                AS product_id,
    p.name                              AS product_name,
    p.slug,
    b.name                              AS brand_name,
    c.name                              AS category_name,
    SUM(oi.quantity)                    AS total_units_sold,
    SUM(oi.line_total)                  AS total_revenue,
    COUNT(DISTINCT o.id)                AS order_count,
    ROUND(AVG(oi.unit_price), 2)        AS avg_selling_price
FROM order_items oi
JOIN orders o           ON o.id  = oi.order_id
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p         ON p.id  = pv.product_id
JOIN brands b           ON b.id  = p.brand_id
JOIN subcategories sc   ON sc.id = p.subcategory_id
JOIN categories c       ON c.id  = sc.category_id
WHERE o.status NOT IN ('cancelled', 'refunded')
  AND o.order_date >= NOW() - INTERVAL '90 days'
GROUP BY p.id, p.name, p.slug, b.name, c.name
ORDER BY total_units_sold DESC;

COMMENT ON VIEW best_selling_products_view IS
'Top-selling products by units in the last 90 days. Used for homepage and analytics.';

-- ---------------------------------------------------------------------------
-- VIEW 3: customer_order_history_view
-- Purpose: Full order history per customer including payment and shipment status.
--          Used by "My Orders" page in the frontend.
-- Concepts: INNER JOIN, LEFT JOIN, COALESCE, ENUM cast
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW customer_order_history_view AS
SELECT
    o.id                            AS order_id,
    o.order_number,
    o.customer_id,
    cp.first_name || ' ' || cp.last_name AS customer_name,
    cust.email                      AS customer_email,
    o.status                        AS order_status,
    o.subtotal,
    o.discount_amount,
    o.shipping_cost,
    o.tax_amount,
    o.total_amount,
    o.order_date,
    p.payment_status,
    p.payment_method,
    p.paid_at,
    s.shipment_status,
    s.tracking_number,
    s.shipped_at,
    s.estimated_delivery,
    s.delivered_at,
    -- Coupon applied
    cou.code                        AS coupon_code,
    -- Shipping method name
    sm.name                         AS shipping_method,
    -- Count items in order
    (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) AS item_count
FROM orders o
JOIN customers cust             ON cust.id = o.customer_id
LEFT JOIN customer_profiles cp  ON cp.customer_id = cust.id
LEFT JOIN payments p            ON p.order_id = o.id
LEFT JOIN shipments s           ON s.order_id = o.id
LEFT JOIN coupons cou           ON cou.id = o.coupon_id
LEFT JOIN shipping_methods sm   ON sm.id = o.shipping_method_id;

COMMENT ON VIEW customer_order_history_view IS
'Full order details per customer with payment/shipment status. Used by My Orders page.';

-- ---------------------------------------------------------------------------
-- VIEW 4: top_rated_products_view
-- Purpose: Products sorted by average approved review rating.
--          Minimum 3 reviews to qualify (avoids single-review spikes).
-- Concepts: JOIN, GROUP BY, HAVING, scalar subquery, ROUND
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW top_rated_products_view AS
SELECT
    p.id                                    AS product_id,
    p.name                                  AS product_name,
    p.slug,
    b.name                                  AS brand_name,
    c.name                                  AS category_name,
    ROUND(AVG(r.rating)::NUMERIC, 2)        AS avg_rating,
    COUNT(r.id)                             AS review_count,
    MIN(r.rating)                           AS min_rating,
    MAX(r.rating)                           AS max_rating,
    p.base_price
FROM reviews r
JOIN product_variants pv ON pv.id = r.variant_id
JOIN products p          ON p.id  = pv.product_id
JOIN brands b            ON b.id  = p.brand_id
JOIN subcategories sc    ON sc.id = p.subcategory_id
JOIN categories c        ON c.id  = sc.category_id
WHERE r.is_approved = TRUE
  AND p.is_active   = TRUE
GROUP BY p.id, p.name, p.slug, b.name, c.name, p.base_price
HAVING COUNT(r.id) >= 3                     -- minimum 3 reviews for statistical validity
ORDER BY avg_rating DESC, review_count DESC;

COMMENT ON VIEW top_rated_products_view IS
'Products with avg approved rating (min 3 reviews). Used for Top Rated homepage section.';

-- ---------------------------------------------------------------------------
-- VIEW 5: inventory_status_view
-- Purpose: Complete inventory picture per (variant, warehouse).
--          Used by warehouse management dashboard.
-- Concepts: JOIN, CASE, generated column reference, COALESCE
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW inventory_status_view AS
SELECT
    inv.id                              AS inventory_id,
    w.name                              AS warehouse_name,
    w.city                             AS warehouse_city,
    p.id                               AS product_id,
    p.name                             AS product_name,
    pv.sku,
    pv.barcode,
    col.name                           AS color,
    sz.name                            AS size,
    mat.name                           AS material,
    inv.current_stock,
    inv.reserved_stock,
    inv.available_stock,               -- generated column
    inv.reorder_level,
    inv.last_restocked,
    -- Stock health status using CASE
    CASE
        WHEN inv.available_stock = 0          THEN 'Out of Stock'
        WHEN inv.available_stock <= inv.reorder_level THEN 'Low Stock'
        WHEN inv.available_stock <= inv.reorder_level * 2 THEN 'Running Low'
        ELSE 'In Stock'
    END                                AS stock_status,
    -- Estimated days of stock at average daily sales (30-day window)
    CASE
        WHEN COALESCE(
            (SELECT SUM(oi.quantity)::NUMERIC / 30
             FROM order_items oi
             JOIN orders o ON o.id = oi.order_id
             WHERE oi.variant_id = pv.id
               AND o.order_date >= NOW() - INTERVAL '30 days'
               AND o.status NOT IN ('cancelled', 'returned')),
            0
        ) > 0
        THEN ROUND(
            inv.available_stock /
            (SELECT SUM(oi.quantity)::NUMERIC / 30
             FROM order_items oi
             JOIN orders o ON o.id = oi.order_id
             WHERE oi.variant_id = pv.id
               AND o.order_date >= NOW() - INTERVAL '30 days'
               AND o.status NOT IN ('cancelled', 'returned')), 0
        )
        ELSE NULL
    END                                AS days_of_stock_remaining,
    COALESCE(pv.price_override, p.base_price) AS unit_price,
    (inv.current_stock * COALESCE(pv.price_override, p.base_price)) AS stock_value
FROM inventory inv
JOIN product_variants pv ON pv.id = inv.variant_id
JOIN products p          ON p.id  = pv.product_id
JOIN warehouses w        ON w.id  = inv.warehouse_id
LEFT JOIN colors col     ON col.id  = pv.color_id
LEFT JOIN sizes sz       ON sz.id   = pv.size_id
LEFT JOIN materials mat  ON mat.id  = pv.material_id;

COMMENT ON VIEW inventory_status_view IS
'Full inventory picture per (variant, warehouse) with stock health status and days-remaining estimate.';

-- ---------------------------------------------------------------------------
-- VIEW 6: low_stock_products_view
-- Purpose: Variants at or below reorder level across all warehouses.
--          Feeds reorder alert notifications.
-- Concepts: WHERE on generated column, JOIN, aggregate
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW low_stock_products_view AS
SELECT
    p.id                                AS product_id,
    p.name                              AS product_name,
    pv.sku,
    col.name                            AS color,
    sz.name                             AS size,
    w.name                              AS warehouse_name,
    inv.current_stock,
    inv.available_stock,
    inv.reorder_level,
    (inv.reorder_level - inv.available_stock) AS units_to_reorder,
    sup.name                            AS supplier_name,
    sup.contact_email                   AS supplier_email,
    sup.lead_time_days
FROM inventory inv
JOIN product_variants pv ON pv.id = inv.variant_id
JOIN products p          ON p.id  = pv.product_id
JOIN warehouses w        ON w.id  = inv.warehouse_id
JOIN suppliers sup       ON sup.id = p.supplier_id
LEFT JOIN colors col     ON col.id = pv.color_id
LEFT JOIN sizes sz       ON sz.id  = pv.size_id
WHERE inv.available_stock <= inv.reorder_level
  AND pv.is_active = TRUE
  AND p.is_active  = TRUE
ORDER BY units_to_reorder DESC;

COMMENT ON VIEW low_stock_products_view IS
'Variants at or below reorder level with supplier contact details for procurement.';

-- ---------------------------------------------------------------------------
-- VIEW 7: revenue_by_brand_view
-- Purpose: Revenue breakdown by brand for financial reporting.
-- Concepts: JOIN, GROUP BY, SUM, COUNT, ORDER BY
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW revenue_by_brand_view AS
SELECT
    b.id                                    AS brand_id,
    b.name                                  AS brand_name,
    b.country_of_origin,
    COUNT(DISTINCT o.id)                    AS order_count,
    COUNT(DISTINCT oi.id)                   AS line_item_count,
    SUM(oi.quantity)                        AS units_sold,
    SUM(oi.line_total)                      AS total_revenue,
    ROUND(AVG(oi.unit_price), 2)            AS avg_unit_price,
    ROUND(SUM(oi.line_total) /
          NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value
FROM order_items oi
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p          ON p.id  = pv.product_id
JOIN brands b            ON b.id  = p.brand_id
JOIN orders o            ON o.id  = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY b.id, b.name, b.country_of_origin
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_brand_view IS
'Revenue, unit sales, and order stats per brand. Used for brand performance reporting.';

-- ---------------------------------------------------------------------------
-- VIEW 8: revenue_by_category_view
-- Purpose: Revenue breakdown by category and subcategory.
-- Concepts: JOIN (3 levels: category→subcategory→product), GROUP BY, ROLLUP potential
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW revenue_by_category_view AS
SELECT
    c.id                                    AS category_id,
    c.name                                  AS category_name,
    sc.id                                   AS subcategory_id,
    sc.name                                 AS subcategory_name,
    COUNT(DISTINCT p.id)                    AS product_count,
    COUNT(DISTINCT o.id)                    AS order_count,
    SUM(oi.quantity)                        AS units_sold,
    SUM(oi.line_total)                      AS total_revenue,
    ROUND(AVG(oi.unit_price), 2)            AS avg_unit_price
FROM order_items oi
JOIN product_variants pv ON pv.id  = oi.variant_id
JOIN products p          ON p.id   = pv.product_id
JOIN subcategories sc    ON sc.id  = p.subcategory_id
JOIN categories c        ON c.id   = sc.category_id
JOIN orders o            ON o.id   = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY c.id, c.name, sc.id, sc.name
ORDER BY total_revenue DESC;

COMMENT ON VIEW revenue_by_category_view IS
'Revenue and sales by category and subcategory hierarchy.';

-- ---------------------------------------------------------------------------
-- VIEW 9: monthly_sales_view
-- Purpose: Month-by-month revenue and order statistics.
-- Concepts: DATE_TRUNC, EXTRACT, GROUP BY, WINDOW FUNCTION (LAG for growth rate)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW monthly_sales_view AS
WITH monthly_data AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE     AS month_start,
        TO_CHAR(o.order_date, 'YYYY-MM')            AS month_label,
        COUNT(o.id)                                 AS order_count,
        COUNT(DISTINCT o.customer_id)               AS unique_customers,
        SUM(o.total_amount)                         AS total_revenue,
        SUM(o.discount_amount)                      AS total_discounts,
        AVG(o.total_amount)                         AS avg_order_value,
        SUM(CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END)   AS delivered_orders,
        SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END)   AS cancelled_orders,
        SUM(CASE WHEN o.status = 'returned'  THEN 1 ELSE 0 END)   AS returned_orders
    FROM orders o
    GROUP BY DATE_TRUNC('month', o.order_date), TO_CHAR(o.order_date, 'YYYY-MM')
)
SELECT
    month_start,
    month_label,
    order_count,
    unique_customers,
    ROUND(total_revenue, 2)             AS total_revenue,
    ROUND(total_discounts, 2)           AS total_discounts,
    ROUND(avg_order_value, 2)           AS avg_order_value,
    delivered_orders,
    cancelled_orders,
    returned_orders,
    -- Month-over-month growth rate using LAG window function
    ROUND(
        (total_revenue - LAG(total_revenue) OVER (ORDER BY month_start)) /
        NULLIF(LAG(total_revenue) OVER (ORDER BY month_start), 0) * 100
    , 2)                                AS mom_growth_pct
FROM monthly_data
ORDER BY month_start DESC;

COMMENT ON VIEW monthly_sales_view IS
'Monthly revenue, orders, customer counts, and MoM growth rate using LAG window function.';

-- ---------------------------------------------------------------------------
-- VIEW 10: warehouse_inventory_view
-- Purpose: Inventory summary per warehouse for warehouse dashboard.
-- Concepts: GROUP BY, SUM, COUNT, CASE, aggregate with HAVING potential
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW warehouse_inventory_view AS
SELECT
    w.id                                    AS warehouse_id,
    w.name                                  AS warehouse_name,
    w.city,
    w.country,
    w.capacity,
    COUNT(DISTINCT inv.variant_id)          AS distinct_variants,
    SUM(inv.current_stock)                  AS total_current_stock,
    SUM(inv.reserved_stock)                 AS total_reserved_stock,
    SUM(inv.available_stock)                AS total_available_stock,
    COUNT(CASE WHEN inv.available_stock = 0 THEN 1 END)               AS out_of_stock_variants,
    COUNT(CASE WHEN inv.available_stock <= inv.reorder_level
               AND inv.available_stock > 0 THEN 1 END)                AS low_stock_variants,
    SUM(inv.current_stock *
        COALESCE(pv.price_override, p.base_price))                    AS total_stock_value,
    ROUND(
        SUM(inv.current_stock) * 100.0 / NULLIF(w.capacity, 0), 2
    )                                       AS capacity_utilization_pct
FROM warehouses w
LEFT JOIN inventory inv     ON inv.warehouse_id = w.id
LEFT JOIN product_variants pv ON pv.id = inv.variant_id
LEFT JOIN products p          ON p.id  = pv.product_id
WHERE w.is_active = TRUE
GROUP BY w.id, w.name, w.city, w.country, w.capacity;

COMMENT ON VIEW warehouse_inventory_view IS
'Per-warehouse inventory summary with capacity utilization and stock valuation.';

-- ---------------------------------------------------------------------------
-- VIEW 11: customer_lifetime_value_view
-- Purpose: CLV ranking of all customers. Used for VIP segmentation.
-- Concepts: LEFT JOIN, subquery, aggregate, ORDER BY, RANK window function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW customer_lifetime_value_view AS
SELECT
    cust.id                                     AS customer_id,
    cp.first_name || ' ' || cp.last_name        AS customer_name,
    cust.email,
    COUNT(DISTINCT o.id)                        AS total_orders,
    SUM(o.total_amount)                         AS lifetime_value,
    ROUND(AVG(o.total_amount), 2)               AS avg_order_value,
    MAX(o.order_date)                           AS last_order_date,
    MIN(o.order_date)                           AS first_order_date,
    EXTRACT(DAY FROM NOW() - MAX(o.order_date)) AS days_since_last_order,
    -- Customer segment using CASE
    CASE
        WHEN SUM(o.total_amount) >= 50000       THEN 'Platinum'
        WHEN SUM(o.total_amount) >= 20000       THEN 'Gold'
        WHEN SUM(o.total_amount) >= 5000        THEN 'Silver'
        ELSE 'Bronze'
    END                                         AS customer_segment,
    -- Rank by lifetime value using RANK window function
    RANK() OVER (ORDER BY SUM(o.total_amount) DESC) AS ltv_rank
FROM customers cust
LEFT JOIN customer_profiles cp  ON cp.customer_id = cust.id
LEFT JOIN orders o              ON o.customer_id  = cust.id
                                AND o.status NOT IN ('cancelled')
LEFT JOIN payments p            ON p.order_id = o.id
                                AND p.payment_status = 'paid'
GROUP BY cust.id, cp.first_name, cp.last_name, cust.email;

COMMENT ON VIEW customer_lifetime_value_view IS
'CLV per customer with segment (Platinum/Gold/Silver/Bronze) and RANK() window function.';

-- ---------------------------------------------------------------------------
-- VIEW 12: coupon_performance_view
-- Purpose: Coupon usage analytics — revenue impact, redemption rate.
-- Concepts: JOIN, GROUP BY, aggregate, NULLIF for division safety
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW coupon_performance_view AS
SELECT
    c.id                                        AS coupon_id,
    c.code,
    c.coupon_type,
    c.value,
    c.min_order_amount,
    c.max_uses,
    c.used_count,
    c.valid_from,
    c.valid_until,
    c.is_active,
    -- Redemption rate
    ROUND(c.used_count * 100.0 / NULLIF(c.max_uses, 0), 2)  AS redemption_rate_pct,
    -- Revenue generated through coupon orders
    COALESCE(SUM(o.total_amount), 0)            AS total_revenue_generated,
    -- Total discount given
    COALESCE(SUM(cu.discount_applied), 0)       AS total_discount_given,
    -- Net revenue (revenue - discount)
    COALESCE(SUM(o.total_amount), 0) -
    COALESCE(SUM(cu.discount_applied), 0)       AS net_revenue,
    COUNT(DISTINCT cu.customer_id)              AS unique_customers_used,
    ROUND(AVG(o.total_amount), 2)               AS avg_order_value_with_coupon
FROM coupons c
LEFT JOIN coupon_usages cu  ON cu.coupon_id = c.id
LEFT JOIN orders o          ON o.id = cu.order_id
                            AND o.status NOT IN ('cancelled', 'refunded')
GROUP BY c.id, c.code, c.coupon_type, c.value, c.min_order_amount,
         c.max_uses, c.used_count, c.valid_from, c.valid_until, c.is_active
ORDER BY total_revenue_generated DESC;

COMMENT ON VIEW coupon_performance_view IS
'Coupon usage analytics: redemption rate, revenue generated, net revenue, discount given.';

-- ---------------------------------------------------------------------------
-- VIEW 13: return_analysis_view
-- Purpose: Return metrics by product, reason, and time period.
--          Used by quality team to identify defective products.
-- Concepts: JOIN, GROUP BY, CASE, percentage calculation
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW return_analysis_view AS
SELECT
    p.id                                        AS product_id,
    p.name                                      AS product_name,
    b.name                                      AS brand_name,
    c.name                                      AS category_name,
    COUNT(rr.id)                                AS total_returns,
    COUNT(CASE WHEN rr.status = 'approved'  THEN 1 END) AS approved_returns,
    COUNT(CASE WHEN rr.status = 'rejected'  THEN 1 END) AS rejected_returns,
    COUNT(CASE WHEN rr.status = 'pending'   THEN 1 END) AS pending_returns,
    -- Units sold in the same period
    COALESCE((
        SELECT SUM(oi2.quantity)
        FROM order_items oi2
        JOIN product_variants pv2 ON pv2.id = oi2.variant_id
        WHERE pv2.product_id = p.id
    ), 0)                                       AS total_units_sold,
    -- Return rate percentage
    ROUND(
        COUNT(rr.id) * 100.0 /
        NULLIF((
            SELECT SUM(oi2.quantity)
            FROM order_items oi2
            JOIN product_variants pv2 ON pv2.id = oi2.variant_id
            WHERE pv2.product_id = p.id
        ), 0)
    , 2)                                        AS return_rate_pct
FROM return_requests rr
JOIN orders o           ON o.id   = rr.order_id
JOIN order_items oi     ON oi.order_id = o.id
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p         ON p.id   = pv.product_id
JOIN brands b           ON b.id   = p.brand_id
JOIN subcategories sc   ON sc.id  = p.subcategory_id
JOIN categories c       ON c.id   = sc.category_id
GROUP BY p.id, p.name, b.name, c.name
ORDER BY return_rate_pct DESC;

COMMENT ON VIEW return_analysis_view IS
'Return rate by product with approved/rejected/pending breakdown. Identifies quality issues.';

-- ---------------------------------------------------------------------------
-- VIEW 14: supplier_performance_view
-- Purpose: Supplier KPIs — product count, revenue contribution, avg lead time.
-- Concepts: LEFT JOIN, GROUP BY, aggregate, subquery, COALESCE
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW supplier_performance_view AS
SELECT
    sup.id                                      AS supplier_id,
    sup.name                                    AS supplier_name,
    sup.country,
    sup.lead_time_days,
    sup.reliability_score,
    COUNT(DISTINCT p.id)                        AS product_count,
    COUNT(DISTINCT pv.id)                       AS variant_count,
    -- Revenue from supplier's products
    COALESCE(SUM(oi.line_total), 0)             AS total_revenue,
    -- Units sold
    COALESCE(SUM(oi.quantity), 0)               AS units_sold,
    -- Active products
    COUNT(DISTINCT CASE WHEN p.is_active THEN p.id END) AS active_products,
    -- Avg price of supplier products
    ROUND(AVG(COALESCE(pv.price_override, p.base_price)), 2) AS avg_product_price
FROM suppliers sup
LEFT JOIN products p          ON p.supplier_id = sup.id
LEFT JOIN product_variants pv ON pv.product_id = p.id
LEFT JOIN order_items oi      ON oi.variant_id = pv.id
LEFT JOIN orders o            ON o.id = oi.order_id
                             AND o.status NOT IN ('cancelled', 'refunded')
GROUP BY sup.id, sup.name, sup.country, sup.lead_time_days, sup.reliability_score
ORDER BY total_revenue DESC;

COMMENT ON VIEW supplier_performance_view IS
'Supplier KPIs: product count, revenue, units sold, reliability score for procurement decisions.';

-- =============================================================================
-- MATERIALIZED VIEWS (Pre-aggregated for dashboard speed)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- MATERIALIZED VIEW 1: mat_product_sales_summary
-- Purpose: Pre-computed sales summary per product. Refreshed daily (or on demand).
--          Dashboard queries hit this MV instead of running heavy aggregations live.
-- Concepts: Materialized View, pre-aggregation, REFRESH MATERIALIZED VIEW
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mat_product_sales_summary AS
SELECT
    p.id                                    AS product_id,
    p.name                                  AS product_name,
    p.base_price,
    b.name                                  AS brand_name,
    c.name                                  AS category_name,
    COUNT(DISTINCT oi.order_id)             AS order_count,
    SUM(oi.quantity)                        AS total_units_sold,
    SUM(oi.line_total)                      AS total_revenue,
    ROUND(AVG(oi.unit_price), 2)            AS avg_selling_price,
    ROUND(AVG(
        CASE WHEN r.is_approved THEN r.rating END
    )::NUMERIC, 2)                          AS avg_rating,
    COUNT(DISTINCT r.id)                    AS review_count,
    COALESCE(SUM(inv.available_stock), 0)   AS total_available_stock,
    NOW()                                   AS last_refreshed
FROM products p
JOIN brands b            ON b.id  = p.brand_id
JOIN subcategories sc    ON sc.id = p.subcategory_id
JOIN categories c        ON c.id  = sc.category_id
LEFT JOIN product_variants pv ON pv.product_id = p.id
LEFT JOIN order_items oi      ON oi.variant_id = pv.id
LEFT JOIN orders o            ON o.id = oi.order_id
                             AND o.status NOT IN ('cancelled', 'refunded')
LEFT JOIN reviews r           ON r.variant_id = pv.id
LEFT JOIN inventory inv       ON inv.variant_id = pv.id
GROUP BY p.id, p.name, p.base_price, b.name, c.name
WITH DATA;

-- Unique index required for CONCURRENT refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_mat_product_sales_product_id
    ON mat_product_sales_summary(product_id);

COMMENT ON MATERIALIZED VIEW mat_product_sales_summary IS
'Pre-aggregated product sales summary. Run: REFRESH MATERIALIZED VIEW CONCURRENTLY mat_product_sales_summary;';

-- ---------------------------------------------------------------------------
-- MATERIALIZED VIEW 2: mat_daily_revenue
-- Purpose: Daily revenue snapshot. Refreshed once per day.
-- Concepts: Materialized View, DATE_TRUNC, pre-aggregation
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mat_daily_revenue AS
SELECT
    DATE_TRUNC('day', o.order_date)::DATE   AS revenue_date,
    COUNT(o.id)                             AS order_count,
    COUNT(DISTINCT o.customer_id)           AS unique_customers,
    SUM(o.total_amount)                     AS total_revenue,
    SUM(o.discount_amount)                  AS total_discounts,
    SUM(o.tax_amount)                       AS total_tax,
    SUM(o.shipping_cost)                    AS total_shipping_revenue,
    AVG(o.total_amount)                     AS avg_order_value,
    NOW()                                   AS last_refreshed
FROM orders o
WHERE o.status != 'cancelled'
GROUP BY DATE_TRUNC('day', o.order_date)::DATE
ORDER BY revenue_date DESC
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mat_daily_revenue_date
    ON mat_daily_revenue(revenue_date);

COMMENT ON MATERIALIZED VIEW mat_daily_revenue IS
'Daily revenue snapshot. Refresh daily with: REFRESH MATERIALIZED VIEW CONCURRENTLY mat_daily_revenue;';

-- ---------------------------------------------------------------------------
-- MATERIALIZED VIEW 3: mat_inventory_health
-- Purpose: Pre-computed inventory health snapshot per variant.
--          Avoids live aggregation on large inventory tables.
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mat_inventory_health AS
SELECT
    pv.id                                   AS variant_id,
    pv.sku,
    p.name                                  AS product_name,
    col.name                                AS color,
    sz.name                                 AS size,
    SUM(inv.current_stock)                  AS total_current_stock,
    SUM(inv.reserved_stock)                 AS total_reserved_stock,
    SUM(inv.available_stock)                AS total_available_stock,
    MIN(inv.reorder_level)                  AS reorder_level,
    CASE
        WHEN SUM(inv.available_stock) = 0            THEN 'Out of Stock'
        WHEN SUM(inv.available_stock) <= MIN(inv.reorder_level) THEN 'Low Stock'
        ELSE 'In Stock'
    END                                     AS stock_status,
    NOW()                                   AS last_refreshed
FROM product_variants pv
JOIN products p          ON p.id  = pv.product_id
LEFT JOIN colors col     ON col.id = pv.color_id
LEFT JOIN sizes sz       ON sz.id  = pv.size_id
LEFT JOIN inventory inv  ON inv.variant_id = pv.id
WHERE pv.is_active = TRUE
GROUP BY pv.id, pv.sku, p.name, col.name, sz.name
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mat_inventory_health_variant
    ON mat_inventory_health(variant_id);

COMMENT ON MATERIALIZED VIEW mat_inventory_health IS
'Per-variant inventory health snapshot across all warehouses. Refresh on inventory changes.';

-- =============================================================================
-- END OF VIEWS
-- Regular Views: 14
-- Materialized Views: 3
-- Total: 17 views
-- Run next: 006_seed.sql
-- =============================================================================
