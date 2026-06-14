BEGIN;

INSERT INTO customers (id, first_name, last_name, email, phone, password_hash, is_active, is_admin) VALUES
(1, 'Aarav', 'Sharma', 'aarav@example.com', '9000000001', '$2b$12$abcdefghijklmnopqrstuv0123456789abcdefghijklmno', TRUE, FALSE),
(2, 'Meera', 'Iyer', 'meera@example.com', '9000000002', '$2b$12$abcdefghijklmnopqrstuv0123456789abcdefghijklmno', TRUE, FALSE),
(3, 'Admin', 'User', 'admin@example.com', '9000000003', '$2b$12$abcdefghijklmnopqrstuv0123456789abcdefghijklmno', TRUE, TRUE);

INSERT INTO categories (id, name, description, is_active) VALUES
(1, 'Electronics', 'Devices, accessories, and gadgets', TRUE),
(2, 'Fashion', 'Clothing and lifestyle products', TRUE),
(3, 'Home & Kitchen', 'Household and kitchen essentials', TRUE);

INSERT INTO suppliers (id, name, contact_email, contact_phone, address, is_active) VALUES
(1, 'Nova Supply Co.', 'sales@novasupply.com', '9111111111', '12 Industrial Park, Mumbai', TRUE),
(2, 'Prime Traders', 'contact@primetraders.com', '9222222222', '44 Market Road, Bengaluru', TRUE),
(3, 'Urban Source Ltd.', 'hello@urbansource.com', '9333333333', '88 Commerce Street, Delhi', TRUE);

INSERT INTO products (id, name, sku, description, price, stock_quantity, is_active, category_id, supplier_id) VALUES
(1, 'Wireless Headphones', 'ELEC-1001', 'Noise cancelling over-ear headphones', 6999.00, 45, TRUE, 1, 1),
(2, 'Smart Watch', 'ELEC-1002', 'Fitness tracking smart watch', 8999.00, 30, TRUE, 1, 1),
(3, 'Cotton T-Shirt', 'FASH-2001', 'Premium unisex t-shirt', 799.00, 120, TRUE, 2, 2),
(4, 'Denim Jeans', 'FASH-2002', 'Slim fit blue jeans', 1799.00, 80, TRUE, 2, 2),
(5, 'Non-stick Pan', 'HOME-3001', '28cm cookware pan', 1299.00, 60, TRUE, 3, 3),
(6, 'Stainless Steel Bottle', 'HOME-3002', 'Insulated water bottle', 999.00, 150, TRUE, 3, 3);

INSERT INTO orders (id, order_number, customer_id, status, total_amount, shipping_address, billing_address, order_date) VALUES
(1, 'ORD-202606090001', 1, 'delivered', 14797.00, '12 Lake View, Pune', '12 Lake View, Pune', NOW() - INTERVAL '10 days'),
(2, 'ORD-202606090002', 2, 'paid', 2598.00, '44 Green Park, Chennai', '44 Green Park, Chennai', NOW() - INTERVAL '5 days'),
(3, 'ORD-202606090003', 1, 'pending', 6999.00, '12 Lake View, Pune', '12 Lake View, Pune', NOW() - INTERVAL '1 day');

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, line_total) VALUES
(1, 1, 1, 1, 6999.00, 6999.00),
(2, 1, 2, 1, 8999.00, 8999.00),
(3, 2, 5, 2, 1299.00, 2598.00),
(4, 3, 1, 1, 6999.00, 6999.00);

INSERT INTO payments (id, order_id, amount, payment_method, payment_status, transaction_reference, paid_at) VALUES
(1, 1, 14797.00, 'card', 'completed', 'TXN-AAA-001', NOW() - INTERVAL '9 days'),
(2, 2, 2598.00, 'upi', 'completed', 'TXN-BBB-002', NOW() - INTERVAL '4 days'),
(3, 3, 6999.00, 'card', 'pending', NULL, NULL);

INSERT INTO shipments (id, order_id, carrier, tracking_number, shipment_status, shipped_at, delivered_at) VALUES
(1, 1, 'Blue Dart', 'TRK111111', 'delivered', NOW() - INTERVAL '8 days', NOW() - INTERVAL '4 days'),
(2, 2, 'Delhivery', 'TRK222222', 'in_transit', NOW() - INTERVAL '2 days', NULL),
(3, 3, NULL, NULL, 'pending', NULL, NULL);

INSERT INTO reviews (id, customer_id, product_id, rating, comment) VALUES
(1, 1, 1, 5, 'Excellent sound quality and battery life.'),
(2, 1, 2, 4, 'Useful features, decent battery.'),
(3, 2, 5, 5, 'Great cookware for daily use.'),
(4, 2, 6, 3, 'Good bottle but slightly heavy.');

INSERT INTO cart_items (id, customer_id, product_id, quantity) VALUES
(1, 1, 4, 1),
(2, 1, 6, 2),
(3, 2, 3, 3),
(4, 2, 1, 1);

SELECT setval(pg_get_serial_sequence('customers', 'id'), (SELECT MAX(id) FROM customers));
SELECT setval(pg_get_serial_sequence('categories', 'id'), (SELECT MAX(id) FROM categories));
SELECT setval(pg_get_serial_sequence('suppliers', 'id'), (SELECT MAX(id) FROM suppliers));
SELECT setval(pg_get_serial_sequence('products', 'id'), (SELECT MAX(id) FROM products));
SELECT setval(pg_get_serial_sequence('orders', 'id'), (SELECT MAX(id) FROM orders));
SELECT setval(pg_get_serial_sequence('order_items', 'id'), (SELECT MAX(id) FROM order_items));
SELECT setval(pg_get_serial_sequence('payments', 'id'), (SELECT MAX(id) FROM payments));
SELECT setval(pg_get_serial_sequence('shipments', 'id'), (SELECT MAX(id) FROM shipments));
SELECT setval(pg_get_serial_sequence('reviews', 'id'), (SELECT MAX(id) FROM reviews));
SELECT setval(pg_get_serial_sequence('cart_items', 'id'), (SELECT MAX(id) FROM cart_items));

COMMIT;
