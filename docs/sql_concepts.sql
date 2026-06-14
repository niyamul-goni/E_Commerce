-- JOINS
SELECT c.first_name, c.last_name, o.order_number
FROM customers c
INNER JOIN orders o ON o.customer_id = c.id;

SELECT c.first_name, o.order_number
FROM customers c
LEFT OUTER JOIN orders o ON o.customer_id = c.id;

SELECT o.order_number, p.transaction_reference
FROM orders o
RIGHT OUTER JOIN payments p ON p.order_id = o.id;

SELECT c.first_name, p.name
FROM customers c
FULL OUTER JOIN products p ON TRUE;

SELECT *
FROM (SELECT id AS customer_id, first_name FROM customers) c
NATURAL JOIN (SELECT customer_id, order_number FROM orders) o;

SELECT c.first_name, p.name
FROM customers c
CROSS JOIN products p
WHERE c.id = 1 AND p.id <= 2;

SELECT o.order_number, c.first_name
FROM orders o
JOIN (SELECT id AS customer_id, first_name FROM customers) c USING (customer_id);

SELECT oi.order_id, p.name, oi.quantity
FROM order_items oi
JOIN products p ON p.id = oi.product_id;

-- SUBQUERIES
SELECT name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);

SELECT first_name, last_name
FROM customers
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = customers.id AND o.status = 'pending'
);

SELECT name
FROM products
WHERE id = ANY (SELECT product_id FROM reviews WHERE rating >= 4);

SELECT name
FROM products
WHERE price > ALL (SELECT unit_price FROM order_items WHERE order_id = 1);

SELECT name
FROM products
WHERE price > SOME (SELECT unit_price FROM order_items WHERE order_id = 2);

SELECT name, price, (SELECT AVG(price) FROM products) AS avg_price
FROM products;

SELECT category_id, AVG(price) AS avg_price
FROM (SELECT * FROM products WHERE is_active = TRUE) AS active_products
GROUP BY category_id;

-- GROUP BY / HAVING / ORDER BY / AGGREGATES
SELECT category_id, COUNT(*) AS product_count, MAX(price) AS max_price, MIN(price) AS min_price, AVG(price) AS avg_price
FROM products
GROUP BY category_id
HAVING COUNT(*) >= 1
ORDER BY avg_price DESC;

SELECT customer_id, SUM(total_amount) AS total_spent
FROM orders
GROUP BY customer_id
ORDER BY total_spent DESC;

-- CTE
WITH order_totals AS (
    SELECT order_id, SUM(line_total) AS total
    FROM order_items
    GROUP BY order_id
)
SELECT o.order_number, ot.total
FROM orders o
JOIN order_totals ot ON ot.order_id = o.id;

-- STRING MANIPULATION
SELECT UPPER(first_name || ' ' || last_name) AS customer_name
FROM customers;

SELECT SUBSTRING(name FROM 1 FOR 5) AS short_name
FROM products;

-- SET OPERATIONS
SELECT email FROM customers WHERE is_admin = TRUE
UNION
SELECT contact_email FROM suppliers WHERE contact_email IS NOT NULL;

SELECT email FROM customers
INTERSECT
SELECT email FROM customers WHERE is_active = TRUE;

SELECT email FROM customers
EXCEPT
SELECT email FROM customers WHERE is_admin = TRUE;

-- UPDATES / DELETES
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id = 1;
DELETE FROM cart_items WHERE quantity <= 0;

-- VIEW EXAMPLE
CREATE OR REPLACE VIEW vw_order_summary AS
SELECT o.id, o.order_number, c.first_name || ' ' || c.last_name AS customer_name, o.total_amount, o.status
FROM orders o
JOIN customers c ON c.id = o.customer_id;
