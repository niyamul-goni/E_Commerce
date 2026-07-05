-- =============================================================================
-- FashionHub — docs/04_sql_query_library.sql
-- Purpose  : 100+ categorized SQL queries demonstrating DBMS concepts
-- Database : PostgreSQL (Supabase)
-- =============================================================================
-- Query Categories:
--   BASIC       (Q001–Q020) — Simple SELECT, WHERE, ORDER BY, LIMIT
--   INTERMEDIATE(Q021–Q045) — JOINs, GROUP BY, HAVING, Subqueries
--   ADVANCED    (Q046–Q070) — Window Functions, CTEs, Complex Subqueries
--   EXPERT      (Q071–Q085) — Recursive CTEs, Correlated Subqueries, Set Ops
--   ANALYTICAL  (Q086–Q100) — Business Analytics, Complex Aggregations
--   DML         (Q101–Q110) — INSERT, UPDATE, DELETE, UPSERT, Transactions
-- =============================================================================

-- ============================================================================
-- BASIC QUERIES (Q001–Q020)
-- ============================================================================

-- Q001: Simple SELECT with column aliases
-- Concept: Basic SELECT, column aliasing
-- Tables: products, brands
-- Complexity: Basic
SELECT
    p.name                              AS product_name,
    p.base_price                        AS price_bdt,
    p.is_featured                       AS featured
FROM products p
ORDER BY p.base_price DESC
LIMIT 10;

-- Q002: Filter with WHERE and multiple conditions
-- Concept: WHERE clause with AND, comparison operators
-- Tables: products
SELECT name, base_price, is_active
FROM products
WHERE base_price BETWEEN 1000 AND 5000
  AND is_active = TRUE
ORDER BY base_price;

-- Q003: String functions — UPPER, LOWER, CONCAT, TRIM
-- Concept: String manipulation functions
-- Tables: customer_profiles
SELECT
    customer_id,
    UPPER(first_name)                           AS first_name_upper,
    LOWER(last_name)                            AS last_name_lower,
    CONCAT(TRIM(first_name), ' ', TRIM(last_name)) AS full_name,
    SUBSTRING(phone, 1, 8) || 'XXXX'           AS masked_phone
FROM customer_profiles
LIMIT 20;

-- Q004: DISTINCT values
-- Concept: DISTINCT keyword
-- Tables: orders
SELECT DISTINCT status FROM orders ORDER BY status;

-- Q005: IN operator
-- Concept: IN predicate for multiple value matching
-- Tables: orders
SELECT id, order_number, status, total_amount
FROM orders
WHERE status IN ('shipped', 'delivered', 'returned')
ORDER BY total_amount DESC
LIMIT 20;

-- Q006: NOT IN operator
-- Concept: NOT IN predicate
-- Tables: orders
SELECT id, order_number, status
FROM orders
WHERE status NOT IN ('cancelled', 'refunded')
ORDER BY order_date DESC
LIMIT 20;

-- Q007: LIKE pattern matching
-- Concept: LIKE operator for pattern matching
-- Tables: products
SELECT name, slug
FROM products
WHERE name LIKE '%Nike%'
   OR name LIKE '%Adidas%'
ORDER BY name;

-- Q008: NULL handling with COALESCE and NULLIF
-- Concept: NULL-safe functions
-- Tables: product_variants, products
SELECT
    pv.sku,
    COALESCE(pv.price_override, p.base_price)           AS effective_price,
    NULLIF(pv.price_override, p.base_price)             AS premium_surcharge,
    COALESCE(col.name, 'No Color Specified')            AS color
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
LEFT JOIN colors col ON col.id = pv.color_id
LIMIT 20;

-- Q009: Aggregate functions — COUNT, SUM, AVG, MIN, MAX
-- Concept: Aggregate functions without GROUP BY
-- Tables: orders
SELECT
    COUNT(*)                    AS total_orders,
    SUM(total_amount)           AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    MIN(total_amount)           AS min_order,
    MAX(total_amount)           AS max_order
FROM orders
WHERE status NOT IN ('cancelled');

-- Q010: ORDER BY with multiple columns and direction
-- Concept: Multi-column ORDER BY
-- Tables: products, brands
SELECT
    p.name,
    b.name AS brand,
    p.base_price
FROM products p
JOIN brands b ON b.id = p.brand_id
ORDER BY b.name ASC, p.base_price DESC;

-- Q011: LIMIT with OFFSET (pagination)
-- Concept: LIMIT / OFFSET pagination
-- Tables: products
-- Purpose: Page 3 of products, 10 per page
SELECT id, name, base_price
FROM products
WHERE is_active = TRUE
ORDER BY created_at DESC
LIMIT 10 OFFSET 20;    -- page 3 = OFFSET (3-1)*10 = 20

-- Q012: BETWEEN date range
-- Concept: Date range filter with BETWEEN
-- Tables: orders
SELECT order_number, total_amount, order_date
FROM orders
WHERE order_date BETWEEN NOW() - INTERVAL '30 days' AND NOW()
ORDER BY order_date DESC;

-- Q013: CASE expression
-- Concept: CASE for conditional labeling
-- Tables: inventory
SELECT
    variant_id,
    current_stock,
    available_stock,
    reorder_level,
    CASE
        WHEN available_stock = 0              THEN 'Out of Stock'
        WHEN available_stock <= reorder_level THEN 'Low Stock'
        WHEN available_stock <= reorder_level * 2 THEN 'Running Low'
        ELSE 'In Stock'
    END AS stock_status
FROM inventory
ORDER BY available_stock;

-- Q014: COUNT with filter (conditional aggregation)
-- Concept: COUNT with FILTER clause
-- Tables: orders
SELECT
    COUNT(*) FILTER (WHERE status = 'pending')    AS pending,
    COUNT(*) FILTER (WHERE status = 'confirmed')  AS confirmed,
    COUNT(*) FILTER (WHERE status = 'delivered')  AS delivered,
    COUNT(*) FILTER (WHERE status = 'cancelled')  AS cancelled
FROM orders;

-- Q015: Working with arrays — ANY operator
-- Concept: ANY with array
-- Tables: products
SELECT name, tags
FROM products
WHERE 'featured'::TEXT = ANY(tags)
   OR tags && ARRAY['new-arrival', 'bestseller'];

-- Q016: Subquery in SELECT (scalar subquery)
-- Concept: Scalar subquery in SELECT clause
-- Tables: customers, orders
SELECT
    c.email,
    (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS order_count,
    (SELECT COALESCE(SUM(o.total_amount), 0)
     FROM orders o WHERE o.customer_id = c.id
       AND o.status = 'delivered')                              AS lifetime_spend
FROM customers c
ORDER BY lifetime_spend DESC
LIMIT 10;

-- Q017: STRING_AGG — aggregate strings
-- Concept: STRING_AGG for concatenation
-- Tables: products, colors (via variants)
SELECT
    p.name AS product_name,
    STRING_AGG(DISTINCT col.name, ', ' ORDER BY col.name) AS available_colors,
    STRING_AGG(DISTINCT sz.name,  ', ' ORDER BY sz.name)  AS available_sizes,
    COUNT(DISTINCT pv.id)                                  AS total_variants
FROM products p
JOIN product_variants pv ON pv.product_id = p.id AND pv.is_active = TRUE
LEFT JOIN colors col      ON col.id = pv.color_id
LEFT JOIN sizes sz        ON sz.id  = pv.size_id
GROUP BY p.id, p.name
ORDER BY total_variants DESC
LIMIT 10;

-- Q018: DEFAULT and NOT NULL constraint verification
-- Concept: Show defaults via system catalog
-- Tables: information_schema
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'orders'
  AND table_schema = 'public'
ORDER BY ordinal_position;

-- Q019: REPLACE and text manipulation
-- Concept: REPLACE, SUBSTRING, UPPER, LOWER string functions
-- Tables: brands
SELECT
    name,
    REPLACE(slug, '-', ' ')         AS slug_readable,
    UPPER(SUBSTRING(name, 1, 3))    AS code,
    LENGTH(name)                     AS name_length
FROM brands
ORDER BY name;

-- Q020: EXTRACT date parts
-- Concept: EXTRACT and TO_CHAR date functions
-- Tables: orders
SELECT
    order_number,
    EXTRACT(YEAR  FROM order_date) AS year,
    EXTRACT(MONTH FROM order_date) AS month,
    EXTRACT(DAY   FROM order_date) AS day,
    TO_CHAR(order_date, 'Day, DD Month YYYY') AS formatted_date
FROM orders
ORDER BY order_date DESC
LIMIT 10;

-- ============================================================================
-- INTERMEDIATE QUERIES (Q021–Q045)
-- ============================================================================

-- Q021: INNER JOIN — products with brands and categories
-- Concept: INNER JOIN, multi-table JOIN
-- Tables: products, brands, subcategories, categories
SELECT
    p.name          AS product,
    b.name          AS brand,
    sc.name         AS subcategory,
    c.name          AS category,
    p.base_price
FROM products p
INNER JOIN brands b       ON b.id  = p.brand_id
INNER JOIN subcategories sc ON sc.id = p.subcategory_id
INNER JOIN categories c   ON c.id  = sc.category_id
ORDER BY c.name, b.name, p.name;

-- Q022: LEFT JOIN — customers with their orders (including customers with no orders)
-- Concept: LEFT JOIN to include non-matching rows
-- Tables: customers, customer_profiles, orders
SELECT
    cp.first_name || ' ' || cp.last_name    AS customer_name,
    c.email,
    COUNT(o.id)                             AS order_count,
    COALESCE(SUM(o.total_amount), 0)        AS total_spent
FROM customers c
LEFT JOIN customer_profiles cp ON cp.customer_id = c.id
LEFT JOIN orders o             ON o.customer_id  = c.id
                               AND o.status NOT IN ('cancelled')
GROUP BY c.id, cp.first_name, cp.last_name, c.email
ORDER BY total_spent DESC;

-- Q023: RIGHT JOIN — all brands even those with no products
-- Concept: RIGHT JOIN
-- Tables: products, brands
SELECT
    b.name              AS brand_name,
    COUNT(p.id)         AS product_count,
    b.country_of_origin
FROM products p
RIGHT JOIN brands b ON b.id = p.brand_id
GROUP BY b.id, b.name, b.country_of_origin
ORDER BY product_count DESC;

-- Q024: FULL OUTER JOIN — customers and admins (all persons)
-- Concept: FULL OUTER JOIN combining two user types
-- Tables: customers, customer_profiles, admins
SELECT
    COALESCE(cp.first_name || ' ' || cp.last_name, adm.full_name) AS person_name,
    COALESCE(c.email, adm.email)    AS email,
    CASE
        WHEN c.id IS NOT NULL AND adm.id IS NOT NULL THEN 'Both'
        WHEN c.id IS NOT NULL   THEN 'Customer'
        ELSE 'Admin'
    END                             AS person_type
FROM customers c
FULL OUTER JOIN customer_profiles cp ON cp.customer_id = c.id
FULL OUTER JOIN admins adm           ON adm.email = c.email
ORDER BY person_type;

-- Q025: JOIN USING — when column name is the same
-- Concept: JOIN USING syntax shorthand
-- Tables: customer_profiles (customer_id matches customers.id)
SELECT cp.first_name, cp.last_name, c.email, c.is_active
FROM customer_profiles cp
JOIN customers c USING (customer_id)     -- implicit: cp.customer_id = c.id
WHERE c.is_active = TRUE
LIMIT 20;

-- Q026: SELF JOIN — find customers from the same city
-- Concept: SELF JOIN on same table
-- Tables: customer_addresses
SELECT
    ca1.recipient_name  AS customer1,
    ca2.recipient_name  AS customer2,
    ca1.city
FROM customer_addresses ca1
JOIN customer_addresses ca2
    ON ca1.city = ca2.city
    AND ca1.customer_id < ca2.customer_id   -- avoid duplicates and self-match
ORDER BY ca1.city
LIMIT 20;

-- Q027: CROSS JOIN — all possible color-size combinations for a product
-- Concept: CROSS JOIN (Cartesian product)
-- Tables: colors, sizes
SELECT
    col.name    AS color,
    sz.name     AS size,
    col.name || '-' || sz.name AS variant_name
FROM colors col
CROSS JOIN sizes sz
WHERE sz.size_category = 'clothing'
ORDER BY col.name, sz.sort_order;

-- Q028: NATURAL JOIN — joining on matching column names
-- Concept: NATURAL JOIN (implicit column matching)
-- Note: Demonstrates concept; use explicit JOINs in production
SELECT customer_id, first_name, last_name
FROM customer_profiles
NATURAL JOIN (
    SELECT customer_id, is_active
    FROM customers
    WHERE is_active = TRUE
) active_customers
LIMIT 20;

-- Q029: GROUP BY with HAVING — brands with revenue > threshold
-- Concept: GROUP BY + HAVING for filtering aggregated results
-- Tables: orders, order_items, product_variants, products, brands
SELECT
    b.name      AS brand,
    COUNT(DISTINCT o.id)    AS orders,
    SUM(oi.line_total)      AS revenue
FROM brands b
JOIN products p     ON p.brand_id = b.id
JOIN product_variants pv ON pv.product_id = p.id
JOIN order_items oi ON oi.variant_id = pv.id
JOIN orders o       ON o.id = oi.order_id AND o.status != 'cancelled'
GROUP BY b.id, b.name
HAVING SUM(oi.line_total) > 10000
ORDER BY revenue DESC;

-- Q030: EXISTS — customers who have placed at least one delivered order
-- Concept: EXISTS correlated subquery
-- Tables: customers, orders
SELECT cp.first_name, cp.last_name, c.email
FROM customers c
JOIN customer_profiles cp ON cp.customer_id = c.id
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.id
      AND o.status = 'delivered'
);

-- Q031: NOT EXISTS — customers who have NEVER placed an order
-- Concept: NOT EXISTS
-- Tables: customers, orders
SELECT cp.first_name, cp.last_name, c.email, c.created_at
FROM customers c
JOIN customer_profiles cp ON cp.customer_id = c.id
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
)
ORDER BY c.created_at DESC;

-- Q032: ANY — products priced above ANY competitor in same subcategory
-- Concept: ANY operator with subquery
-- Tables: products, subcategories
SELECT p.name, p.base_price, sc.name AS subcategory
FROM products p
JOIN subcategories sc ON sc.id = p.subcategory_id
WHERE p.base_price > ANY (
    SELECT p2.base_price
    FROM products p2
    WHERE p2.subcategory_id = p.subcategory_id
      AND p2.id != p.id
      AND p2.base_price < 2000
)
ORDER BY p.base_price;

-- Q033: ALL — products priced above ALL products in Kids category
-- Concept: ALL operator
-- Tables: products, subcategories, categories
SELECT name, base_price
FROM products
WHERE base_price > ALL (
    SELECT p2.base_price
    FROM products p2
    JOIN subcategories sc ON sc.id = p2.subcategory_id
    JOIN categories c     ON c.id  = sc.category_id
    WHERE c.slug = 'kids'
)
ORDER BY base_price;

-- Q034: Subquery in FROM clause (derived table)
-- Concept: Subquery as a derived table in FROM
-- Tables: orders, order_items
SELECT
    order_category.status,
    order_category.order_count,
    order_category.total_revenue,
    ROUND(order_category.total_revenue / order_category.order_count, 2) AS avg_value
FROM (
    SELECT
        o.status,
        COUNT(o.id)             AS order_count,
        SUM(o.total_amount)     AS total_revenue
    FROM orders o
    GROUP BY o.status
) AS order_category
ORDER BY total_revenue DESC;

-- Q035: Subquery in WHERE clause
-- Concept: Subquery in WHERE for filtering
-- Tables: orders, customers
SELECT order_number, total_amount, status
FROM orders
WHERE customer_id IN (
    SELECT customer_id
    FROM customer_profiles
    WHERE city = 'Dhaka'
)
ORDER BY total_amount DESC
LIMIT 20;

-- Q036: Correlated subquery — for each product, its variants count
-- Concept: Correlated subquery (references outer query table)
-- Tables: products, product_variants
SELECT
    p.name,
    p.base_price,
    (SELECT COUNT(*) FROM product_variants pv WHERE pv.product_id = p.id)   AS variant_count,
    (SELECT COUNT(*) FROM product_variants pv WHERE pv.product_id = p.id
                           AND pv.is_active = TRUE)                           AS active_variants
FROM products p
ORDER BY variant_count DESC
LIMIT 15;

-- Q037: UNION — combine customer and admin emails into one list
-- Concept: UNION (removes duplicates)
-- Tables: customers, admins
SELECT email, 'customer' AS user_type FROM customers
UNION
SELECT email, 'admin'    AS user_type FROM admins
ORDER BY email;

-- Q038: UNION ALL — combine all inventory movements with preserving duplicates
-- Concept: UNION ALL (keeps all rows including duplicates)
-- Tables: inventory_movements
SELECT inventory_id, quantity, movement_type::TEXT, created_at FROM inventory_movements WHERE movement_type = 'sale'
UNION ALL
SELECT inventory_id, quantity, movement_type::TEXT, created_at FROM inventory_movements WHERE movement_type = 'return'
ORDER BY created_at DESC
LIMIT 20;

-- Q039: INTERSECT — customers who have both placed orders AND written reviews
-- Concept: INTERSECT set operation
-- Tables: orders, reviews
SELECT customer_id FROM orders
INTERSECT
SELECT customer_id FROM reviews
ORDER BY customer_id;

-- Q040: EXCEPT — customers who placed orders but have NOT written any review
-- Concept: EXCEPT set operation
-- Tables: orders, reviews
SELECT DISTINCT customer_id FROM orders
EXCEPT
SELECT DISTINCT customer_id FROM reviews
ORDER BY customer_id;

-- Q041: GROUP BY multiple columns
-- Concept: Multi-column GROUP BY
-- Tables: orders, order_items, product_variants, products, categories
SELECT
    c.name          AS category,
    EXTRACT(MONTH FROM o.order_date) AS month,
    COUNT(DISTINCT o.id) AS orders,
    SUM(oi.line_total)   AS revenue
FROM orders o
JOIN order_items oi  ON oi.order_id = o.id
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p      ON p.id = pv.product_id
JOIN subcategories sc ON sc.id = p.subcategory_id
JOIN categories c    ON c.id  = sc.category_id
WHERE o.status NOT IN ('cancelled')
GROUP BY c.name, EXTRACT(MONTH FROM o.order_date)
ORDER BY c.name, month;

-- Q042: JOIN ON with additional conditions
-- Concept: JOIN ON with compound conditions (not just FK equality)
-- Tables: inventory, product_variants
SELECT
    pv.sku,
    inv.current_stock,
    inv.available_stock,
    w.name AS warehouse
FROM inventory inv
JOIN product_variants pv
    ON pv.id = inv.variant_id
    AND pv.is_active = TRUE             -- additional JOIN condition
    AND inv.available_stock > 0         -- only show stocked variants
JOIN warehouses w ON w.id = inv.warehouse_id
ORDER BY inv.available_stock DESC
LIMIT 20;

-- Q043: UNIQUE constraint demonstration
-- Concept: UNIQUE constraint prevents duplicate entries
-- Tables: reviews (UNIQUE customer_id, variant_id)
-- Demonstrate: attempt duplicate (shows constraint enforcement)
-- This query shows existing unique combinations:
SELECT customer_id, variant_id, COUNT(*) AS review_count
FROM reviews
GROUP BY customer_id, variant_id
HAVING COUNT(*) > 1;   -- should return empty (UNIQUE constraint enforced)

-- Q044: Date arithmetic
-- Concept: Date arithmetic, INTERVAL, AGE
-- Tables: orders, shipments
SELECT
    o.order_number,
    o.order_date::DATE              AS ordered_on,
    s.shipped_at::DATE              AS shipped_on,
    s.delivered_at::DATE            AS delivered_on,
    s.shipped_at - o.order_date     AS time_to_ship,
    s.delivered_at - s.shipped_at   AS transit_time,
    s.delivered_at - o.order_date   AS total_fulfillment_time
FROM orders o
JOIN shipments s ON s.order_id = o.id
WHERE s.delivered_at IS NOT NULL
ORDER BY total_fulfillment_time DESC
LIMIT 20;

-- Q045: HAVING vs WHERE distinction
-- Concept: HAVING filters groups, WHERE filters rows before grouping
-- Tables: customers, orders
-- Find customers with more than 3 orders AND total spend > 10000
SELECT
    c.email,
    cp.first_name || ' ' || cp.last_name AS name,
    COUNT(o.id)                          AS order_count,
    SUM(o.total_amount)                  AS total_spend
FROM customers c
JOIN customer_profiles cp ON cp.customer_id = c.id
JOIN orders o             ON o.customer_id  = c.id
WHERE o.status != 'cancelled'           -- WHERE filters individual orders
GROUP BY c.id, c.email, cp.first_name, cp.last_name
HAVING COUNT(o.id) > 3                  -- HAVING filters customer groups
   AND SUM(o.total_amount) > 10000
ORDER BY total_spend DESC;

-- ============================================================================
-- ADVANCED QUERIES (Q046–Q070)
-- ============================================================================

-- Q046: CTE (Common Table Expression) — basic WITH clause
-- Concept: CTE for readability and reuse
-- Tables: orders, order_items, products
WITH monthly_revenue AS (
    SELECT
        TO_CHAR(order_date, 'YYYY-MM') AS month,
        SUM(total_amount)              AS revenue
    FROM orders
    WHERE status NOT IN ('cancelled', 'refunded')
    GROUP BY TO_CHAR(order_date, 'YYYY-MM')
)
SELECT
    month,
    revenue,
    SUM(revenue) OVER (ORDER BY month) AS cumulative_revenue
FROM monthly_revenue
ORDER BY month;

-- Q047: Window Function — ROW_NUMBER
-- Concept: ROW_NUMBER() to assign sequential rank within a partition
-- Tables: products, brands
SELECT
    b.name AS brand,
    p.name AS product,
    p.base_price,
    ROW_NUMBER() OVER (
        PARTITION BY b.id
        ORDER BY p.base_price DESC
    ) AS price_rank_within_brand
FROM products p
JOIN brands b ON b.id = p.brand_id
ORDER BY b.name, price_rank_within_brand;

-- Q048: Window Function — RANK and DENSE_RANK
-- Concept: RANK vs DENSE_RANK (RANK skips numbers on ties, DENSE_RANK doesn't)
-- Tables: reviews, product_variants, products
SELECT
    p.name AS product,
    ROUND(AVG(r.rating)::NUMERIC, 2)    AS avg_rating,
    RANK()       OVER (ORDER BY AVG(r.rating) DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (ORDER BY AVG(r.rating) DESC) AS dense_rank_no_gaps
FROM reviews r
JOIN product_variants pv ON pv.id = r.variant_id
JOIN products p          ON p.id  = pv.product_id
WHERE r.is_approved = TRUE
GROUP BY p.id, p.name
HAVING COUNT(r.id) >= 2
ORDER BY avg_rating DESC;

-- Q049: Window Function — LAG and LEAD
-- Concept: LAG/LEAD to compare current row with previous/next row
-- Tables: orders (using monthly aggregation)
WITH daily_orders AS (
    SELECT
        order_date::DATE            AS day,
        COUNT(*)                    AS order_count,
        SUM(total_amount)           AS daily_revenue
    FROM orders
    GROUP BY order_date::DATE
)
SELECT
    day,
    order_count,
    daily_revenue,
    LAG(daily_revenue)  OVER (ORDER BY day) AS prev_day_revenue,
    LEAD(daily_revenue) OVER (ORDER BY day) AS next_day_revenue,
    daily_revenue - LAG(daily_revenue) OVER (ORDER BY day) AS revenue_change
FROM daily_orders
ORDER BY day DESC
LIMIT 30;

-- Q050: Window Function — SUM as running total
-- Concept: SUM() OVER with ORDER BY creates running/cumulative total
-- Tables: orders
SELECT
    order_number,
    order_date::DATE,
    total_amount,
    SUM(total_amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total_revenue
FROM orders
WHERE status NOT IN ('cancelled')
ORDER BY order_date
LIMIT 30;

-- Q051: Window Function — COUNT with PARTITION BY
-- Concept: COUNT() OVER PARTITION BY to count within groups
-- Tables: order_items, orders, products, categories
SELECT
    c.name          AS category,
    p.name          AS product,
    oi.quantity,
    COUNT(oi.id) OVER (PARTITION BY c.id)           AS category_total_items,
    COUNT(oi.id) OVER (PARTITION BY p.id)           AS product_total_items,
    COUNT(oi.id) OVER ()                            AS grand_total_items
FROM order_items oi
JOIN product_variants pv ON pv.id  = oi.variant_id
JOIN products p          ON p.id   = pv.product_id
JOIN subcategories sc    ON sc.id  = p.subcategory_id
JOIN categories c        ON c.id   = sc.category_id
JOIN orders o            ON o.id   = oi.order_id
WHERE o.status NOT IN ('cancelled')
LIMIT 30;

-- Q052: Window Function — NTILE for quartile analysis
-- Concept: NTILE() to divide rows into N groups
-- Tables: customers (by lifetime value)
WITH customer_spend AS (
    SELECT
        c.id,
        c.email,
        COALESCE(SUM(o.total_amount), 0) AS lifetime_value
    FROM customers c
    LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'delivered'
    GROUP BY c.id, c.email
)
SELECT
    email,
    lifetime_value,
    NTILE(4) OVER (ORDER BY lifetime_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY lifetime_value DESC)
        WHEN 1 THEN 'Top 25% (Platinum)'
        WHEN 2 THEN 'Top 50% (Gold)'
        WHEN 3 THEN 'Top 75% (Silver)'
        ELSE        'Bottom 25% (Bronze)'
    END AS segment
FROM customer_spend
ORDER BY lifetime_value DESC;

-- Q053: Multiple CTEs chained
-- Concept: Multiple WITH clauses, CTE referencing CTE
WITH brand_revenue AS (
    SELECT
        b.id AS brand_id, b.name AS brand_name,
        SUM(oi.line_total) AS revenue
    FROM brands b
    JOIN products p ON p.brand_id = b.id
    JOIN product_variants pv ON pv.product_id = p.id
    JOIN order_items oi ON oi.variant_id = pv.id
    JOIN orders o ON o.id = oi.order_id AND o.status != 'cancelled'
    GROUP BY b.id, b.name
),
ranked_brands AS (
    SELECT
        brand_id, brand_name, revenue,
        RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM brand_revenue
)
SELECT brand_name, revenue, revenue_rank
FROM ranked_brands
WHERE revenue_rank <= 10
ORDER BY revenue_rank;

-- Q054: EXISTS with correlated subquery — products with low stock
-- Concept: Complex EXISTS with correlated subquery
-- Tables: products, product_variants, inventory
SELECT p.name, p.base_price
FROM products p
WHERE EXISTS (
    SELECT 1
    FROM product_variants pv
    JOIN inventory inv ON inv.variant_id = pv.id
    WHERE pv.product_id = p.id
      AND inv.available_stock <= inv.reorder_level
      AND inv.available_stock > 0       -- low stock, not zero
);

-- Q055: WINDOW function — FIRST_VALUE and LAST_VALUE
-- Concept: FIRST_VALUE / LAST_VALUE window functions
-- Tables: order_items, orders, products
SELECT
    p.name                          AS product,
    oi.unit_price,
    o.order_date::DATE,
    FIRST_VALUE(oi.unit_price) OVER (
        PARTITION BY p.id
        ORDER BY o.order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS earliest_price,
    LAST_VALUE(oi.unit_price) OVER (
        PARTITION BY p.id
        ORDER BY o.order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS latest_price
FROM order_items oi
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p          ON p.id  = pv.product_id
JOIN orders o            ON o.id  = oi.order_id
ORDER BY p.name, o.order_date
LIMIT 30;

-- Q056: Window Function — PERCENT_RANK
-- Concept: PERCENT_RANK() for relative standing
-- Tables: products
SELECT
    name,
    base_price,
    ROUND(PERCENT_RANK() OVER (ORDER BY base_price) * 100, 2) AS price_percentile
FROM products
WHERE is_active = TRUE
ORDER BY base_price DESC;

-- Q057: Subquery in SELECT with aggregation
-- Concept: Aggregate scalar subquery in SELECT
-- Tables: products, product_variants, order_items
SELECT
    p.name,
    p.base_price,
    (SELECT ROUND(AVG(r.rating)::NUMERIC, 2)
     FROM reviews r
     JOIN product_variants pv ON pv.id = r.variant_id
     WHERE pv.product_id = p.id AND r.is_approved = TRUE) AS avg_rating,
    (SELECT COUNT(DISTINCT oi.order_id)
     FROM order_items oi
     JOIN product_variants pv ON pv.id = oi.variant_id
     WHERE pv.product_id = p.id) AS times_ordered
FROM products p
ORDER BY times_ordered DESC NULLS LAST
LIMIT 15;

-- Q058: CASE with aggregation
-- Concept: CASE inside aggregate functions (conditional aggregation)
-- Tables: orders
SELECT
    TO_CHAR(order_date, 'YYYY-MM')  AS month,
    COUNT(*) FILTER (WHERE status = 'delivered')  AS delivered,
    COUNT(*) FILTER (WHERE status = 'cancelled')  AS cancelled,
    COUNT(*) FILTER (WHERE status = 'returned')   AS returned,
    SUM(CASE WHEN status = 'delivered' THEN total_amount ELSE 0 END) AS delivered_revenue,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'cancelled') * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS cancellation_rate_pct
FROM orders
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY month DESC;

-- Q059: Complex multi-table JOIN for order detail
-- Concept: Complex 8-table JOIN representing an order detail page
SELECT
    o.order_number,
    cp.first_name || ' ' || cp.last_name   AS customer,
    ca.line1 || ', ' || ca.city            AS shipping_address,
    p.name                                  AS product,
    col.name                               AS color,
    sz.name                                AS size,
    pv.sku,
    oi.quantity,
    oi.unit_price,
    oi.line_total,
    sm.name                                AS shipping_method,
    py.payment_status,
    py.payment_method,
    s.tracking_number,
    s.shipment_status
FROM orders o
JOIN customers cust          ON cust.id = o.customer_id
JOIN customer_profiles cp    ON cp.customer_id = cust.id
JOIN customer_addresses ca   ON ca.id = o.shipping_address_id
JOIN order_items oi          ON oi.order_id = o.id
JOIN product_variants pv     ON pv.id = oi.variant_id
JOIN products p              ON p.id  = pv.product_id
LEFT JOIN colors col         ON col.id = pv.color_id
LEFT JOIN sizes sz           ON sz.id  = pv.size_id
LEFT JOIN shipping_methods sm ON sm.id = o.shipping_method_id
LEFT JOIN payments py        ON py.order_id = o.id
LEFT JOIN shipments s        ON s.order_id  = o.id
ORDER BY o.order_date DESC
LIMIT 20;

-- Q060: CTE + Window Function — Top product per category
-- Concept: CTE + RANK() to find top product per category
WITH product_sales AS (
    SELECT
        c.id AS category_id,
        c.name AS category,
        p.id AS product_id,
        p.name AS product,
        SUM(oi.quantity) AS units_sold,
        RANK() OVER (
            PARTITION BY c.id
            ORDER BY SUM(oi.quantity) DESC
        ) AS rank_in_category
    FROM order_items oi
    JOIN product_variants pv ON pv.id = oi.variant_id
    JOIN products p ON p.id = pv.product_id
    JOIN subcategories sc ON sc.id = p.subcategory_id
    JOIN categories c ON c.id = sc.category_id
    JOIN orders o ON o.id = oi.order_id AND o.status != 'cancelled'
    GROUP BY c.id, c.name, p.id, p.name
)
SELECT category, product, units_sold, rank_in_category
FROM product_sales
WHERE rank_in_category = 1
ORDER BY units_sold DESC;

-- Q061: JSONB operations — gateway response in payments
-- Concept: JSONB querying with -> and ->>
-- Tables: payments
SELECT
    id,
    payment_method,
    payment_status,
    gateway_response->>'transaction_id'     AS txn_id,
    gateway_response->>'gateway'            AS gateway,
    (gateway_response->>'amount')::NUMERIC  AS gateway_amount
FROM payments
WHERE gateway_response IS NOT NULL
LIMIT 10;

-- Q062: GENERATE_SERIES for date dimension
-- Concept: GENERATE_SERIES for generating date ranges
SELECT
    d::DATE AS date,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS revenue
FROM GENERATE_SERIES(
    NOW() - INTERVAL '30 days',
    NOW(),
    '1 day'::INTERVAL
) AS d
LEFT JOIN orders o ON o.order_date::DATE = d::DATE
                  AND o.status NOT IN ('cancelled')
GROUP BY d::DATE
ORDER BY d::DATE;

-- Q063: ARRAY aggregation
-- Concept: ARRAY_AGG function
-- Tables: orders, order_items, products
SELECT
    o.order_number,
    ARRAY_AGG(DISTINCT p.name ORDER BY p.name) AS products_ordered
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p ON p.id = pv.product_id
GROUP BY o.id, o.order_number
ORDER BY o.order_number
LIMIT 10;

-- Q064: FILTER clause with window function
-- Concept: FILTER with COUNT window function
-- Tables: reviews
SELECT
    variant_id,
    COUNT(*) FILTER (WHERE rating = 5)  AS five_star,
    COUNT(*) FILTER (WHERE rating = 4)  AS four_star,
    COUNT(*) FILTER (WHERE rating = 3)  AS three_star,
    COUNT(*) FILTER (WHERE rating <= 2) AS negative,
    ROUND(AVG(rating)::NUMERIC, 2)      AS avg_rating
FROM reviews
WHERE is_approved = TRUE
GROUP BY variant_id
ORDER BY avg_rating DESC
LIMIT 20;

-- Q065: Advanced GROUP BY ROLLUP
-- Concept: ROLLUP for hierarchical totals
-- Tables: orders, order_items, products, brands, categories
SELECT
    COALESCE(b.name, 'ALL BRANDS')  AS brand,
    COALESCE(c.name, 'ALL CATEGORIES') AS category,
    SUM(oi.line_total)              AS revenue
FROM order_items oi
JOIN product_variants pv ON pv.id = oi.variant_id
JOIN products p ON p.id = pv.product_id
JOIN brands b ON b.id = p.brand_id
JOIN subcategories sc ON sc.id = p.subcategory_id
JOIN categories c ON c.id = sc.category_id
JOIN orders o ON o.id = oi.order_id AND o.status != 'cancelled'
GROUP BY ROLLUP (b.name, c.name)
ORDER BY brand NULLS LAST, category NULLS LAST;

-- ============================================================================
-- EXPERT QUERIES (Q071–Q085)
-- ============================================================================

-- Q071: Recursive CTE — category hierarchy tree
-- Concept: Recursive CTE for hierarchical data traversal
-- Tables: categories, subcategories
WITH RECURSIVE category_tree AS (
    -- Base case: top-level categories
    SELECT
        id,
        name,
        slug,
        0 AS level,
        name::TEXT AS path
    FROM categories
    WHERE is_active = TRUE

    UNION ALL

    -- Recursive case: subcategories
    SELECT
        sc.id,
        sc.name,
        sc.slug,
        ct.level + 1,
        ct.path || ' > ' || sc.name
    FROM subcategories sc
    JOIN category_tree ct ON ct.id = sc.category_id
)
SELECT
    REPEAT('  ', level) || name   AS indented_name,
    level,
    path
FROM category_tree
ORDER BY path;

-- Q072: Recursive CTE — order status transition chain
-- Concept: Recursive CTE tracing order lifecycle
-- Tables: order_status_history
WITH RECURSIVE status_chain AS (
    -- Base: initial status (INSERT trigger creates this)
    SELECT
        order_id,
        to_status::TEXT AS status_path,
        changed_at,
        1 AS step
    FROM order_status_history
    WHERE from_status IS NULL   -- initial status

    UNION ALL

    -- Recursive: next status transitions
    SELECT
        osh.order_id,
        sc.status_path || ' → ' || osh.to_status::TEXT,
        osh.changed_at,
        sc.step + 1
    FROM order_status_history osh
    JOIN status_chain sc
        ON sc.order_id = osh.order_id
        AND osh.changed_at > sc.changed_at
    WHERE sc.step < 10  -- prevent infinite loops
)
SELECT DISTINCT ON (order_id)
    order_id,
    status_path AS full_status_journey,
    step AS total_transitions
FROM status_chain
ORDER BY order_id, step DESC;

-- Q073: Correlated subquery with EXISTS for reviews
-- Concept: Correlated EXISTS subquery referencing outer alias
-- Tables: products, product_variants, reviews
SELECT
    p.name,
    p.base_price
FROM products p
WHERE EXISTS (
    SELECT 1
    FROM product_variants pv
    JOIN reviews r ON r.variant_id = pv.id
    WHERE pv.product_id = p.id        -- correlation
      AND r.rating = 5
      AND r.is_approved = TRUE
)
ORDER BY p.base_price DESC;

-- Q074: EXCEPT with complex subquery
-- Concept: EXCEPT with multi-column subquery
-- Tables: products, product_variants, order_items
-- Products that have variants but have NEVER been ordered
SELECT p.id, p.name, p.base_price
FROM products p
WHERE p.id IN (SELECT DISTINCT product_id FROM product_variants)
EXCEPT
SELECT p.id, p.name, p.base_price
FROM products p
JOIN product_variants pv ON pv.product_id = p.id
JOIN order_items oi ON oi.variant_id = pv.id
ORDER BY name;

-- Q075: Correlated update subquery (UPDATE with subquery)
-- Concept: UPDATE using correlated subquery
-- Tables: coupons, coupon_usages
-- Recalculate used_count from actual coupon_usages data
UPDATE coupons c
SET used_count = (
    SELECT COUNT(*) FROM coupon_usages cu WHERE cu.coupon_id = c.id
)
WHERE EXISTS (SELECT 1 FROM coupon_usages cu WHERE cu.coupon_id = c.id);

-- Q076: Multi-row INSERT with SELECT
-- Concept: INSERT ... SELECT from another table
-- Tables: customer_notifications, customers, orders
INSERT INTO customer_notifications (customer_id, type, title, body, entity_type, entity_id)
SELECT
    o.customer_id,
    'shipment'::notification_type,
    'Your order ' || o.order_number || ' has been shipped!',
    'Track your shipment with tracking number: ' || s.tracking_number,
    'order',
    o.id
FROM orders o
JOIN shipments s ON s.order_id = o.id
WHERE o.status = 'shipped'
  AND s.shipped_at >= NOW() - INTERVAL '1 hour'
  AND NOT EXISTS (
    SELECT 1 FROM customer_notifications cn
    WHERE cn.customer_id = o.customer_id
      AND cn.entity_id = o.id
      AND cn.type = 'shipment'
  );

-- Q077: UPSERT (INSERT ... ON CONFLICT DO UPDATE)
-- Concept: UPSERT — insert if new, update if exists
-- Tables: inventory
INSERT INTO inventory (variant_id, warehouse_id, current_stock, reserved_stock, reorder_level)
VALUES (1, 1, 100, 5, 10)
ON CONFLICT (variant_id, warehouse_id)
DO UPDATE SET
    current_stock  = EXCLUDED.current_stock,
    reserved_stock = EXCLUDED.reserved_stock,
    last_restocked = NOW(),
    updated_at     = NOW();

-- Q078: DELETE with subquery
-- Concept: DELETE with subquery condition
-- Tables: customer_notifications
DELETE FROM customer_notifications
WHERE is_read = TRUE
  AND created_at < NOW() - INTERVAL '90 days'
  AND customer_id IN (
    SELECT id FROM customers WHERE is_active = TRUE
  );

-- Q079: Transaction with SAVEPOINT
-- Concept: ACID transactions with SAVEPOINT for partial rollback
BEGIN;
    SAVEPOINT before_order_update;

    UPDATE orders
    SET status = 'confirmed'
    WHERE order_number = 'ORD-20250101-10001';

    -- If payment verification fails, rollback just the order update
    -- ROLLBACK TO SAVEPOINT before_order_update;

    SAVEPOINT before_payment_update;

    UPDATE payments
    SET payment_status = 'paid', paid_at = NOW()
    WHERE order_id = (
        SELECT id FROM orders WHERE order_number = 'ORD-20250101-10001'
    );

COMMIT;

-- Q080: Complex JOIN with CASE for analytics
-- Concept: Multi-table JOIN with CASE for cohort analysis
-- Tables: customers, orders
SELECT
    CASE
        WHEN c.created_at >= NOW() - INTERVAL '30 days'  THEN 'New (< 30d)'
        WHEN c.created_at >= NOW() - INTERVAL '90 days'  THEN 'Recent (30-90d)'
        WHEN c.created_at >= NOW() - INTERVAL '365 days' THEN 'Regular (90d-1yr)'
        ELSE 'Loyal (> 1yr)'
    END AS customer_cohort,
    COUNT(DISTINCT c.id)           AS customer_count,
    COUNT(o.id)                    AS total_orders,
    ROUND(AVG(o.total_amount), 2)  AS avg_order_value,
    SUM(o.total_amount)            AS total_revenue
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.status NOT IN ('cancelled')
GROUP BY customer_cohort
ORDER BY customer_count DESC;

-- Q081: Pivot-like query using conditional aggregation
-- Concept: Pivot table using CASE + GROUP BY
-- Tables: orders (payment method distribution by month)
SELECT
    TO_CHAR(o.order_date, 'YYYY-MM') AS month,
    COUNT(*) FILTER (WHERE p.payment_method = 'bkash')  AS bkash_orders,
    COUNT(*) FILTER (WHERE p.payment_method = 'nagad')  AS nagad_orders,
    COUNT(*) FILTER (WHERE p.payment_method = 'card')   AS card_orders,
    COUNT(*) FILTER (WHERE p.payment_method = 'cod')    AS cod_orders,
    COUNT(*)                                             AS total_orders
FROM orders o
JOIN payments p ON p.order_id = o.id
GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
ORDER BY month DESC;

-- Q082: Subquery with HAVING and DISTINCT
-- Concept: DISTINCT inside aggregate subquery
-- Tables: products, order_items
SELECT p.name
FROM products p
WHERE (
    SELECT COUNT(DISTINCT oi.order_id)
    FROM order_items oi
    JOIN product_variants pv ON pv.id = oi.variant_id
    WHERE pv.product_id = p.id
) > (
    SELECT AVG(order_count)
    FROM (
        SELECT COUNT(DISTINCT oi2.order_id) AS order_count
        FROM order_items oi2
        JOIN product_variants pv2 ON pv2.id = oi2.variant_id
        GROUP BY pv2.product_id
    ) sub
);

-- Q083: Window frame specification — moving average
-- Concept: ROWS BETWEEN for moving average calculation
-- Tables: orders (daily revenue)
WITH daily AS (
    SELECT
        order_date::DATE AS day,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status NOT IN ('cancelled')
    GROUP BY order_date::DATE
)
SELECT
    day,
    revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2) AS seven_day_moving_avg
FROM daily
ORDER BY day DESC
LIMIT 30;

-- Q084: Full-text search using GIN index
-- Concept: Full-text search with tsvector/tsquery
-- Tables: products
SELECT
    name,
    base_price,
    ts_rank(to_tsvector('english', name), to_tsquery('english', 'running & shoe')) AS relevance
FROM products
WHERE to_tsvector('english', name) @@ to_tsquery('english', 'running | sport | athletic')
ORDER BY relevance DESC;

-- Q085: Lateral join
-- Concept: LATERAL join for correlated derived tables
-- Tables: customers, orders (latest order per customer)
SELECT
    c.email,
    cp.first_name,
    latest_order.order_number,
    latest_order.total_amount,
    latest_order.status
FROM customers c
JOIN customer_profiles cp ON cp.customer_id = c.id
JOIN LATERAL (
    SELECT order_number, total_amount, status
    FROM orders o
    WHERE o.customer_id = c.id
    ORDER BY o.order_date DESC
    LIMIT 1
) AS latest_order ON TRUE
ORDER BY latest_order.total_amount DESC
LIMIT 20;

-- ============================================================================
-- ANALYTICAL QUERIES (Q086–Q100)
-- ============================================================================

-- Q086: RFM Analysis (Recency, Frequency, Monetary)
-- Concept: Advanced CTE + window functions for customer segmentation
WITH rfm_base AS (
    SELECT
        c.id AS customer_id,
        c.email,
        MAX(o.order_date)                           AS last_order_date,
        COUNT(DISTINCT o.id)                        AS frequency,
        SUM(o.total_amount)                         AS monetary
    FROM customers c
    JOIN orders o ON o.customer_id = c.id AND o.status NOT IN ('cancelled')
    GROUP BY c.id, c.email
),
rfm_scores AS (
    SELECT
        customer_id, email, monetary, frequency,
        EXTRACT(DAY FROM NOW() - last_order_date)   AS recency_days,
        NTILE(5) OVER (ORDER BY last_order_date DESC)   AS r_score,
        NTILE(5) OVER (ORDER BY frequency)              AS f_score,
        NTILE(5) OVER (ORDER BY monetary)               AS m_score
    FROM rfm_base
)
SELECT
    email,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score)   AS total_rfm_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champion'
        WHEN r_score >= 4 AND f_score >= 3                  THEN 'Loyal Customer'
        WHEN r_score >= 4 AND f_score < 2                   THEN 'New Customer'
        WHEN r_score >= 3 AND m_score >= 4                  THEN 'Potential Loyalist'
        WHEN r_score < 2 AND m_score >= 4                   THEN 'At Risk - High Value'
        WHEN r_score < 2 AND m_score < 2                    THEN 'Lost Customer'
        ELSE 'Regular'
    END AS rfm_segment
FROM rfm_scores
ORDER BY total_rfm_score DESC;

-- Q087: Market Basket Analysis (co-purchased products)
-- Concept: SELF JOIN on order_items to find product pairs
-- Tables: order_items, product_variants, products
SELECT
    p1.name AS product_a,
    p2.name AS product_b,
    COUNT(*) AS times_bought_together
FROM order_items oi1
JOIN order_items oi2
    ON oi1.order_id = oi2.order_id
    AND oi1.id < oi2.id               -- avoid duplicate pairs
JOIN product_variants pv1 ON pv1.id = oi1.variant_id
JOIN product_variants pv2 ON pv2.id = oi2.variant_id
JOIN products p1 ON p1.id = pv1.product_id
JOIN products p2 ON p2.id = pv2.product_id
WHERE p1.id != p2.id
GROUP BY p1.id, p1.name, p2.id, p2.name
HAVING COUNT(*) >= 2
ORDER BY times_bought_together DESC
LIMIT 20;

-- Q088: Inventory Aging Report
-- Concept: Complex CTE + date arithmetic for stock aging
-- Tables: inventory, inventory_movements, product_variants
WITH last_sold AS (
    SELECT
        oi.variant_id,
        MAX(o.order_date) AS last_sold_date
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    WHERE o.status NOT IN ('cancelled')
    GROUP BY oi.variant_id
)
SELECT
    pv.sku,
    p.name AS product,
    col.name AS color,
    sz.name AS size,
    SUM(inv.current_stock)          AS total_stock,
    COALESCE(ls.last_sold_date, inv.last_restocked) AS last_activity_date,
    EXTRACT(DAY FROM NOW() - COALESCE(ls.last_sold_date, inv.last_restocked)) AS days_since_activity,
    CASE
        WHEN EXTRACT(DAY FROM NOW() - COALESCE(ls.last_sold_date, inv.last_restocked)) < 30  THEN 'Active'
        WHEN EXTRACT(DAY FROM NOW() - COALESCE(ls.last_sold_date, inv.last_restocked)) < 90  THEN 'Slow-Moving'
        WHEN EXTRACT(DAY FROM NOW() - COALESCE(ls.last_sold_date, inv.last_restocked)) < 180 THEN 'Aging'
        ELSE 'Dead Stock'
    END AS stock_health,
    SUM(inv.current_stock * COALESCE(pv.price_override, p.base_price)) AS stock_value_at_risk
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
LEFT JOIN colors col ON col.id = pv.color_id
LEFT JOIN sizes sz   ON sz.id  = pv.size_id
JOIN inventory inv   ON inv.variant_id = pv.id
LEFT JOIN last_sold ls ON ls.variant_id = pv.id
WHERE inv.current_stock > 0
GROUP BY pv.id, pv.sku, p.name, col.name, sz.name, ls.last_sold_date,
         inv.last_restocked, pv.price_override, p.base_price
ORDER BY days_since_activity DESC NULLS LAST;

-- Q089: Cohort Retention Analysis
-- Concept: Complex CTE + self join for retention
WITH first_order AS (
    SELECT customer_id, MIN(DATE_TRUNC('month', order_date)) AS cohort_month
    FROM orders WHERE status != 'cancelled'
    GROUP BY customer_id
),
orders_by_month AS (
    SELECT DISTINCT
        o.customer_id,
        DATE_TRUNC('month', o.order_date) AS order_month
    FROM orders o
    WHERE o.status != 'cancelled'
)
SELECT
    TO_CHAR(fo.cohort_month, 'YYYY-MM') AS cohort,
    COUNT(DISTINCT fo.customer_id) AS cohort_size,
    COUNT(DISTINCT CASE WHEN om.order_month = fo.cohort_month THEN fo.customer_id END) AS month_0,
    COUNT(DISTINCT CASE WHEN om.order_month = fo.cohort_month + INTERVAL '1 month' THEN fo.customer_id END) AS month_1,
    COUNT(DISTINCT CASE WHEN om.order_month = fo.cohort_month + INTERVAL '2 months' THEN fo.customer_id END) AS month_2,
    COUNT(DISTINCT CASE WHEN om.order_month = fo.cohort_month + INTERVAL '3 months' THEN fo.customer_id END) AS month_3
FROM first_order fo
JOIN orders_by_month om ON om.customer_id = fo.customer_id
GROUP BY fo.cohort_month
ORDER BY fo.cohort_month;

-- Q090: Revenue Attribution by Coupon Type
-- Concept: GROUP BY CUBE for multi-dimensional analysis
SELECT
    COALESCE(cou.coupon_type::TEXT, 'No Coupon') AS coupon_type,
    COALESCE(TO_CHAR(o.order_date, 'YYYY-MM'), 'All Months') AS month,
    COUNT(DISTINCT o.id)            AS orders,
    SUM(o.total_amount)             AS revenue,
    SUM(o.discount_amount)          AS discounts,
    ROUND(AVG(o.total_amount), 2)   AS avg_order_value
FROM orders o
LEFT JOIN coupons cou ON cou.id = o.coupon_id
WHERE o.status NOT IN ('cancelled')
GROUP BY CUBE (cou.coupon_type, TO_CHAR(o.order_date, 'YYYY-MM'))
ORDER BY coupon_type NULLS LAST, month NULLS LAST;

-- Q091: Return Rate by Reason Analysis
-- Concept: CTE + string aggregation for return reason analysis
SELECT
    rr.reason,
    COUNT(*) AS return_count,
    COUNT(CASE WHEN rr.status = 'approved' THEN 1 END) AS approved,
    COUNT(CASE WHEN rr.status = 'rejected' THEN 1 END) AS rejected,
    ROUND(
        COUNT(CASE WHEN rr.status = 'approved' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS approval_rate_pct
FROM return_requests rr
GROUP BY rr.reason
ORDER BY return_count DESC;

-- Q092: Inventory Reorder Planning
-- Concept: Complex calculation for reorder quantities
SELECT
    pv.sku,
    p.name,
    sup.name AS supplier,
    sup.lead_time_days,
    SUM(inv.current_stock)      AS current_stock,
    SUM(inv.available_stock)    AS available_stock,
    -- Average daily sales (last 30 days)
    COALESCE((
        SELECT SUM(oi.quantity)::NUMERIC / 30
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        WHERE oi.variant_id = pv.id
          AND o.order_date >= NOW() - INTERVAL '30 days'
          AND o.status NOT IN ('cancelled')
    ), 0) AS avg_daily_sales,
    -- Recommended reorder quantity (30-day buffer)
    GREATEST(0, ROUND(
        (COALESCE((
            SELECT SUM(oi.quantity)::NUMERIC / 30
            FROM order_items oi JOIN orders o ON o.id = oi.order_id
            WHERE oi.variant_id = pv.id
              AND o.order_date >= NOW() - INTERVAL '30 days'
              AND o.status NOT IN ('cancelled')
        ), 0) * (sup.lead_time_days + 30)) - SUM(inv.current_stock)
    , 0))   AS recommended_order_qty
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
JOIN suppliers sup ON sup.id = p.supplier_id
JOIN inventory inv ON inv.variant_id = pv.id
GROUP BY pv.id, pv.sku, p.name, sup.name, sup.lead_time_days
HAVING SUM(inv.available_stock) <= MIN(inv.reorder_level)
ORDER BY recommended_order_qty DESC;

-- Q093: Price Sensitivity Analysis
-- Concept: Correlation between price and sales volume
SELECT
    CASE
        WHEN p.base_price < 1000  THEN '< 1,000'
        WHEN p.base_price < 3000  THEN '1,000–3,000'
        WHEN p.base_price < 7000  THEN '3,000–7,000'
        WHEN p.base_price < 15000 THEN '7,000–15,000'
        ELSE '> 15,000'
    END AS price_range,
    COUNT(DISTINCT p.id)        AS product_count,
    SUM(oi.quantity)            AS units_sold,
    ROUND(AVG(oi.quantity), 2)  AS avg_units_per_order,
    SUM(oi.line_total)          AS total_revenue,
    ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT p.id), 0), 2) AS revenue_per_product
FROM products p
JOIN product_variants pv ON pv.product_id = p.id
JOIN order_items oi ON oi.variant_id = pv.id
JOIN orders o ON o.id = oi.order_id AND o.status NOT IN ('cancelled')
GROUP BY price_range
ORDER BY MIN(p.base_price);

-- Q094: Customer Journey — first to repeat purchase
-- Concept: Window LAG for customer purchase intervals
WITH customer_orders AS (
    SELECT
        customer_id,
        order_date,
        total_amount,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS order_num,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
    FROM orders
    WHERE status NOT IN ('cancelled')
)
SELECT
    order_num AS nth_order,
    COUNT(DISTINCT customer_id) AS customers_at_this_order,
    ROUND(AVG(EXTRACT(DAY FROM order_date - prev_order_date)), 1) AS avg_days_between_orders,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM customer_orders
WHERE prev_order_date IS NOT NULL
GROUP BY order_num
ORDER BY order_num
LIMIT 10;

-- Q095: Supplier vs Customer Price Margin (hypothetical)
-- Concept: Multiple CTEs, complex joins, calculated margin
WITH supplier_avg_cost AS (
    -- Average cost estimate based on supplier reliability
    SELECT
        p.id AS product_id,
        p.base_price * (1 - (sup.reliability_score / 20)) AS estimated_cost
    FROM products p
    JOIN suppliers sup ON sup.id = p.supplier_id
),
product_revenue AS (
    SELECT
        pv.product_id,
        SUM(oi.line_total) AS revenue,
        SUM(oi.quantity) AS units_sold
    FROM order_items oi
    JOIN product_variants pv ON pv.id = oi.variant_id
    JOIN orders o ON o.id = oi.order_id AND o.status NOT IN ('cancelled')
    GROUP BY pv.product_id
)
SELECT
    p.name,
    p.base_price,
    ROUND(sc.estimated_cost, 2) AS est_unit_cost,
    ROUND(p.base_price - sc.estimated_cost, 2) AS est_gross_margin,
    ROUND((p.base_price - sc.estimated_cost) / NULLIF(p.base_price, 0) * 100, 2) AS margin_pct,
    COALESCE(pr.units_sold, 0) AS units_sold,
    COALESCE(pr.revenue, 0) AS total_revenue
FROM products p
JOIN supplier_avg_cost sc ON sc.product_id = p.id
LEFT JOIN product_revenue pr ON pr.product_id = p.id
ORDER BY margin_pct DESC
LIMIT 20;

-- Q096: View usage demonstration — querying available_products_view
-- Concept: Querying a VIEW as if it were a table
SELECT product_name, brand_name, category_name, avg_rating, total_available_stock
FROM available_products_view
WHERE avg_rating >= 4.0
ORDER BY avg_rating DESC, total_available_stock DESC
LIMIT 10;

-- Q097: Querying materialized view
-- Concept: MATERIALIZED VIEW as pre-computed result set
SELECT product_name, brand_name, total_units_sold, total_revenue, avg_rating
FROM mat_product_sales_summary
ORDER BY total_revenue DESC
LIMIT 10;

-- Q098: Complex analytical function call
-- Concept: Calling stored functions in SELECT
SELECT
    c.email,
    get_customer_lifetime_value(c.id) AS lifetime_value,
    get_customer_lifetime_value(c.id) / NULLIF(
        EXTRACT(DAY FROM NOW() - c.created_at)::NUMERIC / 30,
        0
    ) AS monthly_avg_spend
FROM customers c
WHERE get_customer_lifetime_value(c.id) > 0
ORDER BY lifetime_value DESC
LIMIT 20;

-- Q099: Stock valuation function call
-- Concept: Table-returning function
SELECT * FROM calculate_stock_valuation()
ORDER BY total_value DESC;

-- Q100: Full business intelligence query — executive dashboard KPIs
-- Concept: CTE + multiple aggregates for executive dashboard
WITH kpis AS (
    SELECT
        COUNT(DISTINCT c.id)                                AS total_customers,
        COUNT(DISTINCT CASE WHEN o.id IS NOT NULL THEN c.id END) AS paying_customers,
        COUNT(DISTINCT o.id) FILTER (WHERE o.status != 'cancelled') AS total_orders,
        SUM(o.total_amount) FILTER (WHERE o.status != 'cancelled') AS total_revenue,
        AVG(o.total_amount) FILTER (WHERE o.status != 'cancelled') AS avg_order_value,
        COUNT(DISTINCT o.id) FILTER (WHERE o.order_date >= NOW() - INTERVAL '30 days'
                                    AND o.status != 'cancelled')  AS orders_last_30d,
        SUM(o.total_amount) FILTER (WHERE o.order_date >= NOW() - INTERVAL '30 days'
                                    AND o.status != 'cancelled')  AS revenue_last_30d,
        COUNT(DISTINCT p.id) FILTER (WHERE p.is_active = TRUE)    AS active_products,
        COUNT(DISTINCT CASE WHEN inv.available_stock = 0 THEN inv.variant_id END) AS oos_variants,
        COUNT(DISTINCT rr.id) FILTER (WHERE rr.status = 'pending') AS pending_returns
    FROM customers c
    LEFT JOIN orders o   ON o.customer_id = c.id
    CROSS JOIN (SELECT COUNT(*) AS cnt FROM products WHERE is_active = TRUE) AS p(id)
    LEFT JOIN inventory inv ON TRUE
    LEFT JOIN return_requests rr ON TRUE
)
SELECT
    total_customers,
    paying_customers,
    ROUND(paying_customers * 100.0 / NULLIF(total_customers, 0), 2) AS conversion_rate_pct,
    total_orders,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(avg_order_value, 2) AS avg_order_value,
    orders_last_30d,
    ROUND(revenue_last_30d, 2) AS revenue_last_30d,
    active_products,
    oos_variants,
    pending_returns
FROM kpis;

-- ============================================================================
-- DML QUERIES (Q101–Q110)
-- ============================================================================

-- Q101: INSERT single row
INSERT INTO colors (name, hex_code) VALUES ('Rose Gold', '#B76E79');

-- Q102: INSERT multiple rows
INSERT INTO sizes (name, size_category, sort_order) VALUES
    ('EU 46', 'shoes', 11),
    ('EU 47', 'shoes', 12);

-- Q103: INSERT ... SELECT
INSERT INTO customer_notifications (customer_id, type, title, entity_type, entity_id)
SELECT customer_id, 'promotion', 'Summer Sale: Up to 30% Off!', 'promotion', NULL
FROM customers WHERE is_active = TRUE AND email_verified = TRUE;

-- Q104: UPDATE single column
UPDATE products SET is_featured = TRUE WHERE base_price > 10000 AND is_active = TRUE;

-- Q105: UPDATE with JOIN (PostgreSQL FROM clause)
UPDATE inventory inv
SET reorder_level = 20
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
JOIN brands b   ON b.id = p.brand_id
WHERE inv.variant_id = pv.id
  AND b.name = 'Nike'
  AND inv.reorder_level < 20;

-- Q106: UPDATE with subquery
UPDATE orders
SET status = 'confirmed'
WHERE status = 'pending'
  AND id IN (
    SELECT order_id FROM payments WHERE payment_status = 'paid'
  );

-- Q107: DELETE with condition
DELETE FROM cart_items
WHERE updated_at < NOW() - INTERVAL '30 days';

-- Q108: DELETE with subquery
DELETE FROM customer_notifications
WHERE customer_id IN (
    SELECT id FROM customers WHERE is_active = FALSE
);

-- Q109: UPSERT — ON CONFLICT DO UPDATE
INSERT INTO inventory (variant_id, warehouse_id, current_stock, reorder_level)
VALUES (1, 2, 50, 15)
ON CONFLICT (variant_id, warehouse_id)
DO UPDATE SET
    current_stock  = inventory.current_stock + EXCLUDED.current_stock,
    last_restocked = NOW(),
    updated_at     = NOW();

-- Q110: Full Transaction — place order atomically
BEGIN;

    -- Step 1: Create order
    INSERT INTO orders (customer_id, shipping_address_id, shipping_method_id, status)
    VALUES (1, 1, 1, 'pending')
    RETURNING id;   -- capture order_id

    -- Step 2: Add items (using captured id in real application)
    -- INSERT INTO order_items ... VALUES (...);

    -- Step 3: Calculate totals
    -- PERFORM calculate_order_total(v_order_id);

    -- Step 4: Record payment
    -- INSERT INTO payments ... VALUES (...);

    -- If any step fails, ROLLBACK reverts everything (ACID atomicity)
ROLLBACK;   -- rolling back demo transaction; use COMMIT in production

-- =============================================================================
-- END OF SQL QUERY LIBRARY (110 queries)
-- =============================================================================
