-- =============================================================================
-- FashionHub — Migration: 002_indexes.sql
-- Purpose  : All performance indexes with documented rationale
-- Run after: 001_schema.sql
-- =============================================================================
-- Indexing Strategy:
--   1. All Foreign Keys  → avoid sequential scans on JOINs
--   2. Unique lookups    → SKU, barcode, email, order_number
--   3. High-frequency WHERE clauses → status filters, dates, ratings
--   4. Full-text search  → product names, brand names
--   5. Composite indexes → multi-column WHERE/JOIN patterns
-- =============================================================================

-- ---------------------------------------------------------------------------
-- CUSTOMERS & PROFILES
-- ---------------------------------------------------------------------------

-- Supports: login lookup (WHERE email = ?)  — most critical index in the system
CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email
    ON customers(email);
COMMENT ON INDEX idx_customers_email IS 'Unique; supports O(log n) login lookup and uniqueness check';

-- Supports: customer search by phone (admin panel)
CREATE INDEX IF NOT EXISTS idx_customer_profiles_phone
    ON customer_profiles(phone)
    WHERE phone IS NOT NULL;
COMMENT ON INDEX idx_customer_profiles_phone IS 'Partial index on non-null phones; admin customer lookup';

-- Supports: JOIN customers → customer_profiles
CREATE INDEX IF NOT EXISTS idx_customer_profiles_customer_id
    ON customer_profiles(customer_id);
COMMENT ON INDEX idx_customer_profiles_customer_id IS 'FK index; accelerates 1:1 JOIN to customers';

-- Supports: "get all addresses for customer" — used in checkout
CREATE INDEX IF NOT EXISTS idx_customer_addresses_customer_id
    ON customer_addresses(customer_id);
COMMENT ON INDEX idx_customer_addresses_customer_id IS 'FK index; checkout address list query';

-- Supports: "find default address for customer"
CREATE INDEX IF NOT EXISTS idx_customer_addresses_default
    ON customer_addresses(customer_id, is_default)
    WHERE is_default = TRUE;
COMMENT ON INDEX idx_customer_addresses_default IS 'Partial composite index; finds default address in O(1)';

-- ---------------------------------------------------------------------------
-- WISHLIST & CART
-- ---------------------------------------------------------------------------

-- Supports: JOIN wishlists → wishlist_items
CREATE INDEX IF NOT EXISTS idx_wishlist_items_wishlist_id
    ON wishlist_items(wishlist_id);

CREATE INDEX IF NOT EXISTS idx_wishlist_items_variant_id
    ON wishlist_items(variant_id);

-- Supports: JOIN carts → cart_items
CREATE INDEX IF NOT EXISTS idx_cart_items_cart_id
    ON cart_items(cart_id);

CREATE INDEX IF NOT EXISTS idx_cart_items_variant_id
    ON cart_items(variant_id);

-- ---------------------------------------------------------------------------
-- BRANDS & SUPPLIERS
-- ---------------------------------------------------------------------------

-- Supports: brand filter on product listing page
CREATE INDEX IF NOT EXISTS idx_brands_name
    ON brands(name);
COMMENT ON INDEX idx_brands_name IS 'Supports brand filter and brand name search';

CREATE INDEX IF NOT EXISTS idx_brands_slug
    ON brands(slug);
COMMENT ON INDEX idx_brands_slug IS 'Slug-based URL lookup for brand pages';

-- Supports: admin supplier list with search
CREATE INDEX IF NOT EXISTS idx_suppliers_name
    ON suppliers(name);

-- ---------------------------------------------------------------------------
-- CATEGORIES & SUBCATEGORIES
-- ---------------------------------------------------------------------------

-- Supports: navigation menu and URL routing
CREATE INDEX IF NOT EXISTS idx_categories_slug
    ON categories(slug);

CREATE INDEX IF NOT EXISTS idx_subcategories_slug
    ON subcategories(slug);

-- Supports: "get all subcategories for a category" — primary navigation join
CREATE INDEX IF NOT EXISTS idx_subcategories_category_id
    ON subcategories(category_id);
COMMENT ON INDEX idx_subcategories_category_id IS 'FK index; navigation menu renders subcategories per category';

-- ---------------------------------------------------------------------------
-- PRODUCTS
-- ---------------------------------------------------------------------------

-- Supports: product detail page URL routing
CREATE INDEX IF NOT EXISTS idx_products_slug
    ON products(slug);

-- Supports: full-text search on product names
CREATE INDEX IF NOT EXISTS idx_products_name_text
    ON products USING GIN(to_tsvector('english', name));
COMMENT ON INDEX idx_products_name_text IS 'GIN full-text index; enables fast product name search';

-- Supports: "products by brand" listing page
CREATE INDEX IF NOT EXISTS idx_products_brand_id
    ON products(brand_id);
COMMENT ON INDEX idx_products_brand_id IS 'FK index; brand→products JOIN on product listing';

-- Supports: "products by subcategory" — primary product listing filter
CREATE INDEX IF NOT EXISTS idx_products_subcategory_id
    ON products(subcategory_id);
COMMENT ON INDEX idx_products_subcategory_id IS 'FK index; category browsing — most frequent query pattern';

-- Supports: supplier management (which products does supplier X supply?)
CREATE INDEX IF NOT EXISTS idx_products_supplier_id
    ON products(supplier_id);

-- Supports: homepage "featured products" query
CREATE INDEX IF NOT EXISTS idx_products_featured_active
    ON products(is_featured, is_active)
    WHERE is_featured = TRUE AND is_active = TRUE;
COMMENT ON INDEX idx_products_featured_active IS 'Partial composite; homepage featured products query';

-- Supports: gender filter on product listing
CREATE INDEX IF NOT EXISTS idx_products_gender_id
    ON products(gender_id);

-- ---------------------------------------------------------------------------
-- PRODUCT VARIANTS
-- ---------------------------------------------------------------------------

-- Supports: SKU lookup (POS system, admin search, barcode scan)
CREATE UNIQUE INDEX IF NOT EXISTS idx_variants_sku
    ON product_variants(sku);
COMMENT ON INDEX idx_variants_sku IS 'Critical unique index; warehouse scanning and admin SKU lookup';

-- Supports: barcode scanner lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_variants_barcode
    ON product_variants(barcode)
    WHERE barcode IS NOT NULL;
COMMENT ON INDEX idx_variants_barcode IS 'Partial unique index; barcode scanner lookups (null barcodes excluded)';

-- Supports: "get all variants for product" — product detail page
CREATE INDEX IF NOT EXISTS idx_variants_product_id
    ON product_variants(product_id);
COMMENT ON INDEX idx_variants_product_id IS 'FK index; product detail page loads all color/size variants';

-- Supports: "all red variants" — color filter
CREATE INDEX IF NOT EXISTS idx_variants_color_id
    ON product_variants(color_id);

-- Supports: "all XL variants" — size filter
CREATE INDEX IF NOT EXISTS idx_variants_size_id
    ON product_variants(size_id);

-- Composite: "active variants for product" — most common variant query
CREATE INDEX IF NOT EXISTS idx_variants_product_active
    ON product_variants(product_id, is_active)
    WHERE is_active = TRUE;
COMMENT ON INDEX idx_variants_product_active IS 'Partial composite; only active variants for product detail';

-- ---------------------------------------------------------------------------
-- PRODUCT IMAGES & SPECIFICATIONS
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_product_images_product_id
    ON product_images(product_id);

-- Partial index: primary images (only one per product, fast lookup)
CREATE INDEX IF NOT EXISTS idx_product_images_primary
    ON product_images(product_id, is_primary)
    WHERE is_primary = TRUE;
COMMENT ON INDEX idx_product_images_primary IS 'Partial index; fast primary image lookup for product cards';

CREATE INDEX IF NOT EXISTS idx_product_specs_product_id
    ON product_specifications(product_id);

-- ---------------------------------------------------------------------------
-- INVENTORY
-- ---------------------------------------------------------------------------

-- Supports: "stock levels for variant" — product detail page availability check
CREATE INDEX IF NOT EXISTS idx_inventory_variant_id
    ON inventory(variant_id);
COMMENT ON INDEX idx_inventory_variant_id IS 'FK index; availability check before add-to-cart';

-- Supports: warehouse management dashboard
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse_id
    ON inventory(warehouse_id);

-- Supports: low-stock alerts (WHERE available_stock <= reorder_level)
CREATE INDEX IF NOT EXISTS idx_inventory_low_stock
    ON inventory(available_stock, reorder_level)
    WHERE available_stock <= reorder_level;
COMMENT ON INDEX idx_inventory_low_stock IS 'Partial index; low-stock alert dashboard query';

-- ---------------------------------------------------------------------------
-- INVENTORY MOVEMENTS
-- ---------------------------------------------------------------------------

-- Supports: "history of movements for this inventory record"
CREATE INDEX IF NOT EXISTS idx_inv_movements_inventory_id
    ON inventory_movements(inventory_id);

-- Supports: filter by movement type (e.g., all sales today)
CREATE INDEX IF NOT EXISTS idx_inv_movements_type
    ON inventory_movements(movement_type);

-- Supports: date-range movement reports
CREATE INDEX IF NOT EXISTS idx_inv_movements_created_at
    ON inventory_movements(created_at DESC);
COMMENT ON INDEX idx_inv_movements_created_at IS 'DESC index; recent movements query without full scan';

-- ---------------------------------------------------------------------------
-- ORDERS
-- ---------------------------------------------------------------------------

-- Supports: order number lookup (customer service, admin search)
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_order_number
    ON orders(order_number);
COMMENT ON INDEX idx_orders_order_number IS 'Critical unique index; order lookup by number (customer service)';

-- Supports: "all orders for customer" — my orders page
CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON orders(customer_id);
COMMENT ON INDEX idx_orders_customer_id IS 'FK index; customer orders page — high-frequency query';

-- Supports: admin order management with status filter
CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders(status);
COMMENT ON INDEX idx_orders_status IS 'Status filter on admin order management page';

-- Supports: date-range order analytics
CREATE INDEX IF NOT EXISTS idx_orders_order_date
    ON orders(order_date DESC);
COMMENT ON INDEX idx_orders_order_date IS 'DESC index; recent orders and date-range revenue reports';

-- Composite: status + date for admin dashboard pipeline
CREATE INDEX IF NOT EXISTS idx_orders_status_date
    ON orders(status, order_date DESC);
COMMENT ON INDEX idx_orders_status_date IS 'Composite; admin dashboard order pipeline by status and date';

-- Supports: coupon performance analysis (how many orders used coupon X?)
CREATE INDEX IF NOT EXISTS idx_orders_coupon_id
    ON orders(coupon_id)
    WHERE coupon_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- ORDER ITEMS
-- ---------------------------------------------------------------------------

-- Supports: "all items in order" — order detail page
CREATE INDEX IF NOT EXISTS idx_order_items_order_id
    ON order_items(order_id);

-- Supports: "all orders containing variant X" — sales analytics
CREATE INDEX IF NOT EXISTS idx_order_items_variant_id
    ON order_items(variant_id);
COMMENT ON INDEX idx_order_items_variant_id IS 'FK index; best-selling variant analysis and inventory deduction';

-- ---------------------------------------------------------------------------
-- ORDER STATUS HISTORY
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id
    ON order_status_history(order_id);

CREATE INDEX IF NOT EXISTS idx_order_status_history_changed_at
    ON order_status_history(changed_at DESC);

-- ---------------------------------------------------------------------------
-- PAYMENTS
-- ---------------------------------------------------------------------------

-- Supports: payment lookup by transaction reference (payment gateway webhook)
CREATE INDEX IF NOT EXISTS idx_payments_transaction_ref
    ON payments(transaction_ref)
    WHERE transaction_ref IS NOT NULL;
COMMENT ON INDEX idx_payments_transaction_ref IS 'Partial unique; payment gateway callback lookup';

-- Supports: failed payment monitoring
CREATE INDEX IF NOT EXISTS idx_payments_status
    ON payments(payment_status);

-- ---------------------------------------------------------------------------
-- SHIPMENTS
-- ---------------------------------------------------------------------------

-- Supports: tracking number lookup (customer tracking page)
CREATE INDEX IF NOT EXISTS idx_shipments_tracking_number
    ON shipments(tracking_number)
    WHERE tracking_number IS NOT NULL;
COMMENT ON INDEX idx_shipments_tracking_number IS 'Partial index; customer shipment tracking lookup';

-- Supports: shipment status dashboard (pending/in_transit)
CREATE INDEX IF NOT EXISTS idx_shipments_status
    ON shipments(shipment_status);
COMMENT ON INDEX idx_shipments_status IS 'Status filter; warehouse shipment processing queue';

-- ---------------------------------------------------------------------------
-- COUPONS
-- ---------------------------------------------------------------------------

-- Supports: coupon validation at checkout (WHERE code = ? AND is_active = TRUE)
CREATE INDEX IF NOT EXISTS idx_coupons_code
    ON coupons(code);
COMMENT ON INDEX idx_coupons_code IS 'Coupon code lookup at checkout — direct equality match';

-- Supports: active coupon listing
CREATE INDEX IF NOT EXISTS idx_coupons_active
    ON coupons(is_active, valid_until)
    WHERE is_active = TRUE;

-- ---------------------------------------------------------------------------
-- COUPON USAGES
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_coupon_usages_coupon_id
    ON coupon_usages(coupon_id);

CREATE INDEX IF NOT EXISTS idx_coupon_usages_customer_id
    ON coupon_usages(customer_id);

-- ---------------------------------------------------------------------------
-- REVIEWS
-- ---------------------------------------------------------------------------

-- Supports: "all reviews for product" (via variant join)
CREATE INDEX IF NOT EXISTS idx_reviews_variant_id
    ON reviews(variant_id);

-- Supports: "all reviews by customer" — my reviews page
CREATE INDEX IF NOT EXISTS idx_reviews_customer_id
    ON reviews(customer_id);

-- Supports: rating filter and average rating calculation
CREATE INDEX IF NOT EXISTS idx_reviews_rating
    ON reviews(rating);
COMMENT ON INDEX idx_reviews_rating IS 'Rating index; average rating aggregation and filter by stars';

-- Supports: pending review moderation queue
CREATE INDEX IF NOT EXISTS idx_reviews_approved
    ON reviews(is_approved)
    WHERE is_approved = FALSE;
COMMENT ON INDEX idx_reviews_approved IS 'Partial index; admin moderation queue for unapproved reviews';

-- ---------------------------------------------------------------------------
-- ACTIVITY LOGS
-- ---------------------------------------------------------------------------

-- Supports: admin action history
CREATE INDEX IF NOT EXISTS idx_activity_logs_admin_id
    ON activity_logs(admin_id);

-- Supports: "all actions on entity X" (e.g., what happened to order #12345)
CREATE INDEX IF NOT EXISTS idx_activity_logs_entity
    ON activity_logs(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at
    ON activity_logs(created_at DESC);

-- ---------------------------------------------------------------------------
-- RETURN REQUESTS
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_return_requests_order_id
    ON return_requests(order_id);

CREATE INDEX IF NOT EXISTS idx_return_requests_customer_id
    ON return_requests(customer_id);

CREATE INDEX IF NOT EXISTS idx_return_requests_status
    ON return_requests(status);

-- =============================================================================
-- END OF INDEXES (57 indexes total)
-- Run next: 003_functions.sql
-- =============================================================================
