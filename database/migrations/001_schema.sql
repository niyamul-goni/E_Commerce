-- =============================================================================
-- FashionHub — Fashion & Lifestyle E-Commerce Platform
-- Migration: 001_schema.sql
-- Purpose  : Core schema — all tables, ENUMs, constraints, generated columns
-- Author   : FashionHub DB Team
-- Standard : PostgreSQL 15+, 3NF/BCNF normalized, DBMS course project
-- =============================================================================
-- Run order: 001 → 002 → 003 → 004 → 005 → 006
-- Execute in Supabase SQL Editor (or psql) as superuser/service_role
-- =============================================================================

-- ---------------------------------------------------------------------------
-- SAFETY: Drop everything in reverse dependency order for a clean slate
-- ---------------------------------------------------------------------------
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- =============================================================================
-- SECTION 1: CUSTOM ENUM TYPES
-- Rationale: ENUMs enforce domain integrity at the type-system level,
--            making illegal state unrepresentable without CHECK constraints.
-- =============================================================================

-- Order lifecycle states (strict progression enforced by trigger)
CREATE TYPE order_status AS ENUM (
    'pending',      -- created, not yet confirmed
    'confirmed',    -- payment received
    'packed',       -- warehouse packed the order
    'shipped',      -- handed to courier
    'delivered',    -- customer received
    'cancelled',    -- cancelled before shipment
    'returned',     -- customer returned
    'refunded'      -- refund processed
);

-- Payment states
CREATE TYPE payment_status AS ENUM (
    'pending',      -- awaiting payment
    'paid',         -- successfully charged
    'failed',       -- payment declined
    'refunded'      -- money returned to customer
);

-- Shipment states
CREATE TYPE shipment_status AS ENUM (
    'pending',      -- not yet handed to courier
    'packed',       -- packed at warehouse
    'in_transit',   -- in courier network
    'delivered',    -- confirmed delivery
    'returned'      -- returned to warehouse
);

-- Inventory movement types — tracks every stock change
CREATE TYPE movement_type AS ENUM (
    'purchase',     -- stock received from supplier
    'sale',         -- stock reduced after confirmed order
    'adjustment',   -- manual correction
    'return',       -- stock restored after return
    'transfer'      -- moved between warehouses
);

-- Coupon discount types
CREATE TYPE coupon_type AS ENUM (
    'percentage',   -- e.g. 20% off
    'fixed_amount'  -- e.g. $10 off
);

-- Return request lifecycle
CREATE TYPE return_status AS ENUM (
    'pending',      -- customer submitted, awaiting review
    'approved',     -- approved, awaiting shipment back
    'rejected',     -- rejected with reason
    'completed'     -- stock restored, refund issued
);

-- Notification channel
CREATE TYPE notification_type AS ENUM (
    'order',
    'payment',
    'shipment',
    'promotion',
    'system'
);

-- Size category axis — shoes use different size charts than clothing
CREATE TYPE size_category AS ENUM (
    'clothing',     -- XS, S, M, L, XL, XXL
    'shoes',        -- EU 36–46, US 5–13
    'bags',         -- One Size, Small, Medium, Large
    'accessories'   -- One Size, adjustable
);

-- =============================================================================
-- SECTION 2: LOOKUP / REFERENCE TABLES (Normalize all repeating attributes)
-- These tables eliminate repeating groups and transitive dependencies from
-- the main entity tables, achieving 3NF.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: genders
-- Purpose: Normalize the gender attribute shared by customers, products
-- FD: id → name; name is the candidate key
-- Normal Form: BCNF (single non-key attribute, no transitive deps)
-- ---------------------------------------------------------------------------
CREATE TABLE genders (
    id          SMALLSERIAL PRIMARY KEY,
    name        VARCHAR(20) NOT NULL,
    CONSTRAINT uq_genders_name UNIQUE (name)
);
COMMENT ON TABLE genders IS 'Lookup table for gender classifications used by customers and products';

-- ---------------------------------------------------------------------------
-- TABLE: colors
-- Purpose: Normalize color attribute so ProductVariant references a color ID,
--          not a free-text string — eliminates "Red", "red", "RED" anomalies
-- FD: id → {name, hex_code}; name is an alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE colors (
    id          SMALLSERIAL PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL,
    hex_code    CHAR(7),                    -- e.g. #FF5733
    CONSTRAINT uq_colors_name     UNIQUE (name),
    CONSTRAINT chk_colors_hex     CHECK (hex_code IS NULL OR hex_code ~ '^#[0-9A-Fa-f]{6}$')
);
COMMENT ON TABLE colors IS 'Canonical color registry; hex_code enables UI color swatches';

-- ---------------------------------------------------------------------------
-- TABLE: sizes
-- Purpose: Normalize size attribute. Different product categories use
--          different sizing systems — captured by size_category.
-- FD: id → {name, size_category, sort_order}
--     (name, size_category) is a composite alternate key
-- ---------------------------------------------------------------------------
CREATE TABLE sizes (
    id              SMALLSERIAL PRIMARY KEY,
    name            VARCHAR(20)   NOT NULL,
    size_category   size_category NOT NULL,
    sort_order      SMALLINT      NOT NULL DEFAULT 0,  -- for UI ordering (XS < S < M ...)
    CONSTRAINT uq_sizes_name_category UNIQUE (name, size_category)
);
COMMENT ON TABLE sizes IS 'Size lookup keyed by category; prevents XS clothing conflating with XS bags';

-- ---------------------------------------------------------------------------
-- TABLE: materials
-- Purpose: Normalize material/fabric attribute (Cotton, Polyester, Leather…)
-- FD: id → {name, description}; name is alternate key
-- ---------------------------------------------------------------------------
CREATE TABLE materials (
    id          SMALLSERIAL PRIMARY KEY,
    name        VARCHAR(80)  NOT NULL,
    description TEXT,
    CONSTRAINT uq_materials_name UNIQUE (name)
);
COMMENT ON TABLE materials IS 'Fabric/material registry referenced by ProductVariant';

-- ---------------------------------------------------------------------------
-- TABLE: seasons
-- Purpose: Normalize season attribute for collections and products
-- FD: id → name
-- ---------------------------------------------------------------------------
CREATE TABLE seasons (
    id      SMALLSERIAL PRIMARY KEY,
    name    VARCHAR(30) NOT NULL,
    CONSTRAINT uq_seasons_name UNIQUE (name)
);
COMMENT ON TABLE seasons IS 'Season lookup: Spring/Summer/Autumn/Winter/All-Season';

-- =============================================================================
-- SECTION 3: ADMINISTRATION MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: roles
-- Purpose: Named roles for RBAC (role-based access control).
--          Separates role definition from admin users — 2NF compliance.
-- FD: id → {name, description}; name is alternate key
-- ---------------------------------------------------------------------------
CREATE TABLE roles (
    id          SMALLSERIAL PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL,
    description TEXT,
    CONSTRAINT uq_roles_name UNIQUE (name)
);
COMMENT ON TABLE roles IS 'RBAC roles: super_admin, catalog_manager, order_manager, warehouse_staff';

-- ---------------------------------------------------------------------------
-- TABLE: permissions
-- Purpose: Granular permission registry. Avoids hardcoding permissions in app.
-- FD: id → {code, description}; code is alternate key
-- ---------------------------------------------------------------------------
CREATE TABLE permissions (
    id          SMALLSERIAL PRIMARY KEY,
    code        VARCHAR(100) NOT NULL,     -- e.g. 'product:create', 'order:read'
    description TEXT,
    CONSTRAINT uq_permissions_code UNIQUE (code)
);
COMMENT ON TABLE permissions IS 'Granular permissions referenced by role_permissions join table';

-- ---------------------------------------------------------------------------
-- TABLE: role_permissions  [ASSOCIATIVE / JUNCTION TABLE]
-- Purpose: M:M relationship between roles and permissions.
--          Primary key is composite (role_id, permission_id) — classic associative entity.
-- FD: (role_id, permission_id) → {} (no non-key attributes beyond the composite PK)
-- Normal Form: BCNF — both attributes are part of the only candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE role_permissions (
    role_id         SMALLINT NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
    permission_id   SMALLINT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_role_permissions PRIMARY KEY (role_id, permission_id)
);
COMMENT ON TABLE role_permissions IS 'Junction table: M:M roles ↔ permissions';

-- ---------------------------------------------------------------------------
-- TABLE: admins
-- Purpose: Platform administrators, separate from customer accounts.
--          Links to roles for RBAC. NOT mixed with customer data (3NF).
-- FD: id → {email, password_hash, role_id, is_active, ...}
--     email is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE admins (
    id              BIGSERIAL    PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(150) NOT NULL,
    role_id         SMALLINT     NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_admins_email UNIQUE (email),
    CONSTRAINT chk_admins_email_format CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$')
);
COMMENT ON TABLE admins IS 'Admin users with RBAC via role_id; separated from customer table (3NF)';

-- ---------------------------------------------------------------------------
-- TABLE: activity_logs
-- Purpose: Immutable audit trail of all admin actions.
--          Weak entity — meaningless without admin reference.
-- FD: id → {admin_id, action, entity_type, entity_id, ip_address, created_at}
-- ---------------------------------------------------------------------------
CREATE TABLE activity_logs (
    id              BIGSERIAL    PRIMARY KEY,
    admin_id        BIGINT       REFERENCES admins(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,    -- e.g. 'UPDATE_PRODUCT', 'APPROVE_RETURN'
    entity_type     VARCHAR(50),              -- e.g. 'product', 'order'
    entity_id       BIGINT,                   -- PK of affected record
    old_value       JSONB,                    -- snapshot before change
    new_value       JSONB,                    -- snapshot after change
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE activity_logs IS 'Immutable admin audit trail; old/new values stored as JSONB';

-- =============================================================================
-- SECTION 4: BRAND & SUPPLIER MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: brands
-- Purpose: Brand is an independent entity with its own attributes.
--          Separating brand from product prevents update anomalies
--          (changing brand address requires updating every product row otherwise).
-- FD: id → {name, slug, logo_url, country_of_origin, description, is_active}
--     name and slug are alternate candidate keys
-- ---------------------------------------------------------------------------
CREATE TABLE brands (
    id                  BIGSERIAL    PRIMARY KEY,
    name                VARCHAR(150) NOT NULL,
    slug                VARCHAR(150) NOT NULL,   -- URL-friendly identifier
    logo_url            TEXT,
    country_of_origin   VARCHAR(100),
    description         TEXT,
    website_url         TEXT,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_brands_name UNIQUE (name),
    CONSTRAINT uq_brands_slug UNIQUE (slug)
);
COMMENT ON TABLE brands IS 'Fashion brands; slug used for SEO-friendly URLs';

-- ---------------------------------------------------------------------------
-- TABLE: suppliers
-- Purpose: Suppliers are independent entities that supply products to the platform.
--          Attributes like lead_time and reliability_score belong to supplier,
--          not to individual products — 3NF: no transitive dependency.
-- FD: id → {name, contact_email, contact_phone, address, lead_time_days, reliability_score, ...}
-- ---------------------------------------------------------------------------
CREATE TABLE suppliers (
    id                  BIGSERIAL    PRIMARY KEY,
    name                VARCHAR(150) NOT NULL,
    contact_person      VARCHAR(100),
    contact_email       VARCHAR(255),
    contact_phone       VARCHAR(30),
    address             TEXT,
    city                VARCHAR(100),
    country             VARCHAR(100),
    lead_time_days      SMALLINT    CHECK (lead_time_days >= 0),   -- avg delivery days
    reliability_score   NUMERIC(3,2) CHECK (reliability_score BETWEEN 0 AND 5),
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_suppliers_name          UNIQUE (name),
    CONSTRAINT uq_suppliers_contact_email UNIQUE (contact_email)
);
COMMENT ON TABLE suppliers IS 'Product suppliers; reliability_score tracks fulfillment quality';

-- =============================================================================
-- SECTION 5: PRODUCT CATEGORY MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: categories
-- Purpose: Top-level product classifications (Men, Women, Kids, Shoes, etc.)
-- FD: id → {name, slug, description, image_url, is_active}; name and slug are AKs
-- ---------------------------------------------------------------------------
CREATE TABLE categories (
    id          BIGSERIAL    PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    slug        VARCHAR(120) NOT NULL,
    description TEXT,
    image_url   TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order  SMALLINT    NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_categories_name UNIQUE (name),
    CONSTRAINT uq_categories_slug UNIQUE (slug)
);
COMMENT ON TABLE categories IS 'Top-level product categories; subcategories reference this table';

-- ---------------------------------------------------------------------------
-- TABLE: subcategories
-- Purpose: Second-level classification under a category.
--          Separated from categories to avoid self-join complexity and
--          maintain single-level hierarchy clarity for DBMS demo.
-- FD: id → {category_id, name, slug, description, is_active}
--     (category_id, name) is composite alternate key
-- Partial dependency removed: name depends on id alone, not on category_id alone.
-- ---------------------------------------------------------------------------
CREATE TABLE subcategories (
    id          BIGSERIAL    PRIMARY KEY,
    category_id BIGINT       NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name        VARCHAR(120) NOT NULL,
    slug        VARCHAR(120) NOT NULL,
    description TEXT,
    image_url   TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    sort_order  SMALLINT    NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_subcategories_slug           UNIQUE (slug),
    CONSTRAINT uq_subcategories_name_category  UNIQUE (category_id, name)
);
COMMENT ON TABLE subcategories IS 'Second-level categories; each belongs to exactly one top-level category';

-- ---------------------------------------------------------------------------
-- TABLE: collections
-- Purpose: Marketing collections (e.g., "Summer 2025 Collection", "Ramadan Edit").
--          Collections span multiple subcategories/products — an independent entity.
-- FD: id → {name, season_id, description, start_date, end_date, is_active}
-- ---------------------------------------------------------------------------
CREATE TABLE collections (
    id          BIGSERIAL    PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    slug        VARCHAR(150) NOT NULL,
    season_id   SMALLINT     REFERENCES seasons(id) ON DELETE SET NULL,
    description TEXT,
    banner_url  TEXT,
    start_date  DATE,
    end_date    DATE,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_collections_slug UNIQUE (slug),
    CONSTRAINT uq_collections_name UNIQUE (name),
    CONSTRAINT chk_collections_dates CHECK (end_date IS NULL OR end_date >= start_date)
);
COMMENT ON TABLE collections IS 'Seasonal/marketing collections; linked to seasons lookup table';

-- =============================================================================
-- SECTION 6: WAREHOUSE & INVENTORY MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: warehouses
-- Purpose: Physical warehouse locations that hold inventory.
--          Inventory quantity is per (variant, warehouse) pair — not on the product.
-- FD: id → {name, code, city, country, address, capacity, is_active}
--     code is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE warehouses (
    id          BIGSERIAL    PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    code        VARCHAR(20)  NOT NULL,    -- e.g. 'WH-DXB-01'
    address     TEXT,
    city        VARCHAR(100),
    country     VARCHAR(100),
    capacity    INTEGER      CHECK (capacity > 0),    -- max units
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_warehouses_code UNIQUE (code),
    CONSTRAINT uq_warehouses_name UNIQUE (name)
);
COMMENT ON TABLE warehouses IS 'Physical warehouse locations; inventory is tracked per warehouse';

-- =============================================================================
-- SECTION 7: CUSTOMER MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: customers
-- Purpose: Core authentication entity for customers. Stores ONLY auth data.
--          Profile data (name, DOB, gender) is in customer_profiles.
-- Normalization: Splitting auth from profile achieves 3NF — profile attributes
--          depend on customer_id, not transitively on email.
-- FD: id → {email, password_hash, is_active, created_at, updated_at}
--     email is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE customers (
    id              BIGSERIAL    PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    email_verified  BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_customers_email       UNIQUE (email),
    CONSTRAINT chk_customers_email_fmt  CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$')
);
COMMENT ON TABLE customers IS 'Auth entity: only email + password. Profile data is in customer_profiles (3NF separation)';

-- ---------------------------------------------------------------------------
-- TABLE: customer_profiles  [1:1 with customers]
-- Purpose: Separates demographic/profile data from auth credentials.
--          This is a classic 3NF normalization pattern — profile attributes
--          describe the customer, not the login credential.
-- FD: customer_id → {first_name, last_name, phone, date_of_birth, gender_id, avatar_url}
-- ---------------------------------------------------------------------------
CREATE TABLE customer_profiles (
    customer_id     BIGINT       PRIMARY KEY REFERENCES customers(id) ON DELETE CASCADE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    phone           VARCHAR(30),
    date_of_birth   DATE,
    gender_id       SMALLINT     REFERENCES genders(id) ON DELETE SET NULL,
    avatar_url      TEXT,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_customer_profiles_phone UNIQUE (phone)
);
COMMENT ON TABLE customer_profiles IS '1:1 with customers; separates profile from auth for 3NF compliance';

-- ---------------------------------------------------------------------------
-- TABLE: customer_addresses
-- Purpose: Customers may have many saved addresses (billing, shipping, home, work).
--          Normalizing addresses out of orders prevents repeating groups.
-- FD: id → {customer_id, label, recipient_name, phone, line1, line2, city, state, postal_code, country, is_default}
-- ---------------------------------------------------------------------------
CREATE TABLE customer_addresses (
    id              BIGSERIAL    PRIMARY KEY,
    customer_id     BIGINT       NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    label           VARCHAR(50)  NOT NULL DEFAULT 'Home',    -- Home, Work, Other
    recipient_name  VARCHAR(150) NOT NULL,
    phone           VARCHAR(30),
    line1           VARCHAR(255) NOT NULL,
    line2           VARCHAR(255),
    city            VARCHAR(100) NOT NULL,
    state           VARCHAR(100),
    postal_code     VARCHAR(20),
    country         VARCHAR(100) NOT NULL DEFAULT 'Bangladesh',
    is_default      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE customer_addresses IS 'Multiple saved addresses per customer; orders reference address_id (not embedded strings)';

-- ---------------------------------------------------------------------------
-- TABLE: wishlists
-- Purpose: Each customer has exactly one wishlist (1:1).
--          Separate table allows future multi-wishlist extension.
-- FD: id → customer_id; customer_id is alternate PK candidate
-- ---------------------------------------------------------------------------
CREATE TABLE wishlists (
    id          BIGSERIAL   PRIMARY KEY,
    customer_id BIGINT      NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_wishlists_customer UNIQUE (customer_id)
);
COMMENT ON TABLE wishlists IS 'One wishlist per customer; wishlist_items contains the variant-level entries';

-- ---------------------------------------------------------------------------
-- TABLE: wishlist_items  [ASSOCIATIVE TABLE]
-- Purpose: M:M between wishlists and product_variants.
--          Variant-level (not product-level) so the customer saves specific color+size.
-- FD: (wishlist_id, variant_id) → added_at
-- Normal Form: BCNF
-- ---------------------------------------------------------------------------
CREATE TABLE wishlist_items (
    id          BIGSERIAL   PRIMARY KEY,
    wishlist_id BIGINT      NOT NULL REFERENCES wishlists(id)        ON DELETE CASCADE,
    variant_id  BIGINT      NOT NULL,    -- FK added after product_variants is created
    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_wishlist_items UNIQUE (wishlist_id, variant_id)
);
COMMENT ON TABLE wishlist_items IS 'Variant-level wishlist entries; (wishlist_id, variant_id) is composite AK';

-- ---------------------------------------------------------------------------
-- TABLE: carts
-- Purpose: Active shopping cart per customer. Separate from orders.
-- FD: id → customer_id; customer_id is AK
-- ---------------------------------------------------------------------------
CREATE TABLE carts (
    id          BIGSERIAL   PRIMARY KEY,
    customer_id BIGINT      NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_carts_customer UNIQUE (customer_id)
);
COMMENT ON TABLE carts IS 'One active cart per customer; cart_items holds variant-level line items';

-- ---------------------------------------------------------------------------
-- TABLE: cart_items  [ASSOCIATIVE TABLE]
-- Purpose: Line items in a shopping cart. Variant-level for correct stock checking.
-- FD: (cart_id, variant_id) → {quantity, added_at}
-- ---------------------------------------------------------------------------
CREATE TABLE cart_items (
    id          BIGSERIAL    PRIMARY KEY,
    cart_id     BIGINT       NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    variant_id  BIGINT       NOT NULL,    -- FK added after product_variants
    quantity    SMALLINT     NOT NULL DEFAULT 1,
    added_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cart_items            UNIQUE (cart_id, variant_id),
    CONSTRAINT chk_cart_items_quantity  CHECK (quantity > 0)
);
COMMENT ON TABLE cart_items IS 'Variant-level cart line items; quantity > 0 enforced';

-- ---------------------------------------------------------------------------
-- TABLE: customer_notifications
-- Purpose: Notification log per customer. Decoupled from orders/payments
--          so the notification system can extend to promotions and system alerts.
-- FD: id → {customer_id, type, title, body, is_read, created_at}
-- ---------------------------------------------------------------------------
CREATE TABLE customer_notifications (
    id          BIGSERIAL           PRIMARY KEY,
    customer_id BIGINT              NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    type        notification_type   NOT NULL,
    title       VARCHAR(200)        NOT NULL,
    body        TEXT,
    entity_type VARCHAR(50),     -- e.g. 'order', 'shipment'
    entity_id   BIGINT,          -- PK of referenced record
    is_read     BOOLEAN          NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE customer_notifications IS 'Per-customer notification inbox; entity_type+entity_id link to source record';

-- =============================================================================
-- SECTION 8: PRODUCT MODULE
-- Key design principle: Product holds only BASE data shared across all variants.
-- Variant-specific attributes (color, size, material, SKU, price) live in
-- product_variants. This eliminates partial dependencies (2NF) and prevents
-- update anomalies.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: products  [BASE PRODUCT ENTITY]
-- Purpose: Stores attributes common to ALL variants of a product.
-- What does NOT belong here: color, size, SKU, stock, barcode, material.
-- FD: id → {name, slug, brand_id, supplier_id, subcategory_id, collection_id,
--           base_price, gender_id, description, care_instructions, is_active}
-- ---------------------------------------------------------------------------
CREATE TABLE products (
    id                  BIGSERIAL    PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    slug                VARCHAR(200) NOT NULL,
    brand_id            BIGINT       NOT NULL REFERENCES brands(id)       ON DELETE RESTRICT,
    supplier_id         BIGINT       NOT NULL REFERENCES suppliers(id)     ON DELETE RESTRICT,
    subcategory_id      BIGINT       NOT NULL REFERENCES subcategories(id) ON DELETE RESTRICT,
    collection_id       BIGINT       REFERENCES collections(id)           ON DELETE SET NULL,
    gender_id           SMALLINT     REFERENCES genders(id)               ON DELETE SET NULL,
    base_price          NUMERIC(12,2) NOT NULL,    -- MSRP; variant may override
    description         TEXT,
    care_instructions   TEXT,
    tags                TEXT[],                    -- array of search tags
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_featured         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_products_slug        UNIQUE (slug),
    CONSTRAINT chk_products_base_price CHECK (base_price > 0)
);
COMMENT ON TABLE products IS 'Base product entity; color/size/SKU/stock are in product_variants (2NF compliance)';

-- ---------------------------------------------------------------------------
-- TABLE: product_images
-- Purpose: Multiple images per product. Separating images into their own table
--          eliminates repeating groups (1NF violation if stored as columns).
-- FD: id → {product_id, image_url, alt_text, sort_order, is_primary}
-- ---------------------------------------------------------------------------
CREATE TABLE product_images (
    id          BIGSERIAL    PRIMARY KEY,
    product_id  BIGINT       NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url   TEXT         NOT NULL,
    alt_text    VARCHAR(200),
    sort_order  SMALLINT     NOT NULL DEFAULT 0,
    is_primary  BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE product_images IS 'Multiple images per product; eliminates 1NF violation of repeating image columns';

-- ---------------------------------------------------------------------------
-- TABLE: product_variants  [CENTRAL PURCHASABLE ENTITY]
-- Purpose: Each orderable SKU is a variant. A variant is a unique combination
--          of (product, color, size, material). This is the item that:
--          - has a unique SKU and barcode
--          - has stock in inventory
--          - gets added to cart and ordered
--          - gets reviewed
-- FD: id → {product_id, color_id, size_id, material_id, sku, barcode,
--            price_override, weight_grams, is_active}
--     sku and barcode are alternate candidate keys
-- Normalization: (product_id, color_id, size_id, material_id) could form a
--     composite AK — the UNIQUE constraint enforces this.
-- ---------------------------------------------------------------------------
CREATE TABLE product_variants (
    id              BIGSERIAL    PRIMARY KEY,
    product_id      BIGINT       NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    color_id        SMALLINT     REFERENCES colors(id)    ON DELETE SET NULL,
    size_id         SMALLINT     REFERENCES sizes(id)     ON DELETE SET NULL,
    material_id     SMALLINT     REFERENCES materials(id) ON DELETE SET NULL,
    sku             VARCHAR(100) NOT NULL,
    barcode         VARCHAR(100),
    price_override  NUMERIC(12,2),   -- NULL means use product.base_price
    weight_grams    INTEGER      CHECK (weight_grams > 0),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_variants_sku                      UNIQUE (sku),
    CONSTRAINT uq_variants_barcode                  UNIQUE (barcode),
    CONSTRAINT uq_variants_combination              UNIQUE (product_id, color_id, size_id, material_id),
    CONSTRAINT chk_variants_price_override          CHECK (price_override IS NULL OR price_override > 0)
);
COMMENT ON TABLE product_variants IS 'Orderable SKU units; each unique (product, color, size, material) is a variant';

-- ---------------------------------------------------------------------------
-- TABLE: product_specifications  [EAV — Entity-Attribute-Value]
-- Purpose: Flexible key-value specifications vary by product type.
--          A watch has "Movement: Quartz, Case Diameter: 42mm".
--          A shoe has "Heel Height: 5cm, Toe Shape: Round".
--          Using separate columns would cause null-heavy, un-normalized tables.
-- FD: (product_id, spec_key) → spec_value
-- Normal Form: BCNF — composite PK is the only candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE product_specifications (
    id          BIGSERIAL    PRIMARY KEY,
    product_id  BIGINT       NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    spec_key    VARCHAR(100) NOT NULL,   -- e.g. 'Movement Type', 'Strap Material'
    spec_value  TEXT         NOT NULL,   -- e.g. 'Automatic', 'Stainless Steel'
    CONSTRAINT uq_product_specs UNIQUE (product_id, spec_key)
);
COMMENT ON TABLE product_specifications IS 'EAV pattern for flexible product attributes; avoids null-heavy wide tables';

-- ---------------------------------------------------------------------------
-- TABLE: inventory
-- Purpose: Stock levels per (variant, warehouse) combination.
--          current_stock, reserved_stock are mutable; available_stock is generated.
-- FD: id → {variant_id, warehouse_id, current_stock, reserved_stock, reorder_level}
--     (variant_id, warehouse_id) is composite alternate key
-- Generated column: available_stock avoids derived data anomalies (computed from facts).
-- ---------------------------------------------------------------------------
CREATE TABLE inventory (
    id              BIGSERIAL   PRIMARY KEY,
    variant_id      BIGINT      NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    warehouse_id    BIGINT      NOT NULL REFERENCES warehouses(id)       ON DELETE RESTRICT,
    current_stock   INTEGER     NOT NULL DEFAULT 0,
    reserved_stock  INTEGER     NOT NULL DEFAULT 0,     -- held for pending orders
    reorder_level   INTEGER     NOT NULL DEFAULT 10,    -- triggers low-stock alert
    -- Generated column: eliminates derived data inconsistency (3NF principle applied to computed values)
    available_stock INTEGER GENERATED ALWAYS AS (current_stock - reserved_stock) STORED,
    last_restocked  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_inventory_variant_warehouse   UNIQUE (variant_id, warehouse_id),
    CONSTRAINT chk_inventory_current_stock      CHECK (current_stock >= 0),
    CONSTRAINT chk_inventory_reserved_stock     CHECK (reserved_stock >= 0),
    CONSTRAINT chk_inventory_reorder_level      CHECK (reorder_level >= 0),
    CONSTRAINT chk_inventory_reserved_lte_current CHECK (reserved_stock <= current_stock)
);
COMMENT ON TABLE inventory IS 'Stock per (variant, warehouse); available_stock is a generated column (current - reserved)';

-- ---------------------------------------------------------------------------
-- TABLE: inventory_movements  [AUDIT LOG — Append-only]
-- Purpose: Every change to inventory.current_stock is recorded here.
--          This enables stock reconciliation, audit, and reporting.
--          Never delete from this table — it is an immutable ledger.
-- FD: id → {inventory_id, movement_type, quantity, reference_type, reference_id, notes, created_at}
-- ---------------------------------------------------------------------------
CREATE TABLE inventory_movements (
    id              BIGSERIAL       PRIMARY KEY,
    inventory_id    BIGINT          NOT NULL REFERENCES inventory(id) ON DELETE RESTRICT,
    movement_type   movement_type   NOT NULL,
    quantity        INTEGER         NOT NULL,   -- positive = stock in, negative = stock out
    reference_type  VARCHAR(50),   -- 'order', 'return', 'supplier', 'adjustment'
    reference_id    BIGINT,        -- FK to the relevant entity
    notes           TEXT,
    created_by      BIGINT REFERENCES admins(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_movements_quantity_nonzero CHECK (quantity != 0)
);
COMMENT ON TABLE inventory_movements IS 'Immutable ledger of all stock changes; enables full audit trail';

-- =============================================================================
-- SECTION 9: SALES MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: shipping_methods
-- Purpose: Courier/shipping options with their rates. Separating this from
--          orders avoids repeating rate and ETA data across order rows.
-- FD: id → {name, carrier, base_rate, rate_per_kg, estimated_days, is_active}
-- ---------------------------------------------------------------------------
CREATE TABLE shipping_methods (
    id              BIGSERIAL    PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,    -- e.g. 'Standard Delivery', 'Express'
    carrier         VARCHAR(100),             -- e.g. 'Pathao', 'Sundarban', 'DHL'
    base_rate       NUMERIC(10,2) NOT NULL DEFAULT 0,
    rate_per_kg     NUMERIC(10,2) NOT NULL DEFAULT 0,
    estimated_days  SMALLINT     NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_shipping_methods_name UNIQUE (name),
    CONSTRAINT chk_shipping_base_rate   CHECK (base_rate >= 0),
    CONSTRAINT chk_shipping_rate_per_kg CHECK (rate_per_kg >= 0),
    CONSTRAINT chk_shipping_est_days    CHECK (estimated_days >= 0)
);
COMMENT ON TABLE shipping_methods IS 'Courier options with rates; orders reference shipping_method_id (not embedded text)';

-- ---------------------------------------------------------------------------
-- TABLE: coupons
-- Purpose: Discount coupon definitions. Separated from coupon_usages so that
--          coupon metadata (code, type, value) is defined once — not duplicated
--          in every usage record (prevents update anomalies).
-- FD: id → {code, coupon_type, value, min_order_amount, max_uses, used_count,
--            valid_from, valid_until, is_active}
--     code is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE coupons (
    id                  BIGSERIAL     PRIMARY KEY,
    code                VARCHAR(50)   NOT NULL,
    coupon_type         coupon_type   NOT NULL,
    value               NUMERIC(10,2) NOT NULL,     -- % or fixed amount
    min_order_amount    NUMERIC(12,2) NOT NULL DEFAULT 0,
    max_discount_amount NUMERIC(12,2),              -- cap for percentage coupons
    max_uses            INTEGER,                    -- NULL = unlimited
    used_count          INTEGER       NOT NULL DEFAULT 0,
    valid_from          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    valid_until         TIMESTAMPTZ,
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    description         TEXT,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_coupons_code          UNIQUE (code),
    CONSTRAINT chk_coupons_value        CHECK (value > 0),
    CONSTRAINT chk_coupons_min_order    CHECK (min_order_amount >= 0),
    CONSTRAINT chk_coupons_used_count   CHECK (used_count >= 0),
    CONSTRAINT chk_coupons_valid_dates  CHECK (valid_until IS NULL OR valid_until > valid_from),
    CONSTRAINT chk_coupons_pct_range    CHECK (coupon_type != 'percentage' OR value <= 100)
);
COMMENT ON TABLE coupons IS 'Coupon definitions; coupon_usages tracks per-customer application';

-- ---------------------------------------------------------------------------
-- TABLE: coupon_usages  [ASSOCIATIVE TABLE]
-- Purpose: Tracks which customers used which coupon on which order.
--          Prevents double-use by the UNIQUE constraint on (coupon_id, customer_id).
-- FD: id → {coupon_id, customer_id, order_id, discount_applied, used_at}
--     (coupon_id, customer_id) is composite AK (one use per customer per coupon)
-- ---------------------------------------------------------------------------
CREATE TABLE coupon_usages (
    id              BIGSERIAL    PRIMARY KEY,
    coupon_id       BIGINT       NOT NULL REFERENCES coupons(id)   ON DELETE RESTRICT,
    customer_id     BIGINT       NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_id        BIGINT,      -- FK added after orders table
    discount_applied NUMERIC(12,2) NOT NULL,
    used_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_coupon_usages_coupon_customer UNIQUE (coupon_id, customer_id),
    CONSTRAINT chk_coupon_usage_discount        CHECK (discount_applied >= 0)
);
COMMENT ON TABLE coupon_usages IS 'Coupon usage ledger; UNIQUE(coupon_id, customer_id) prevents double-use';

-- ---------------------------------------------------------------------------
-- TABLE: orders  [CORE SALES ENTITY]
-- Purpose: Represents a customer's placed order. Key normalization decisions:
--   1. shipping_address_id → FK to customer_addresses (not embedded string)
--   2. shipping_method_id  → FK to shipping_methods   (not embedded string)
--   3. coupon_id           → FK to coupons             (not embedded text)
-- FD: id → {order_number, customer_id, shipping_address_id, billing_address_id,
--           shipping_method_id, coupon_id, status, subtotal, discount_amount,
--           shipping_cost, tax_amount, total_amount, notes, order_date}
--     order_number is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE orders (
    id                      BIGSERIAL       PRIMARY KEY,
    order_number            VARCHAR(20)     NOT NULL,
    customer_id             BIGINT          NOT NULL REFERENCES customers(id)          ON DELETE RESTRICT,
    shipping_address_id     BIGINT          NOT NULL REFERENCES customer_addresses(id) ON DELETE RESTRICT,
    billing_address_id      BIGINT          REFERENCES customer_addresses(id)         ON DELETE SET NULL,
    shipping_method_id      BIGINT          REFERENCES shipping_methods(id)           ON DELETE SET NULL,
    coupon_id               BIGINT          REFERENCES coupons(id)                    ON DELETE SET NULL,
    status                  order_status    NOT NULL DEFAULT 'pending',
    subtotal                NUMERIC(12,2)   NOT NULL DEFAULT 0,
    discount_amount         NUMERIC(12,2)   NOT NULL DEFAULT 0,
    shipping_cost           NUMERIC(10,2)   NOT NULL DEFAULT 0,
    tax_amount              NUMERIC(10,2)   NOT NULL DEFAULT 0,
    total_amount            NUMERIC(12,2)   NOT NULL DEFAULT 0,
    notes                   TEXT,
    order_date              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_orders_order_number       UNIQUE (order_number),
    CONSTRAINT chk_orders_subtotal          CHECK (subtotal >= 0),
    CONSTRAINT chk_orders_discount          CHECK (discount_amount >= 0),
    CONSTRAINT chk_orders_shipping_cost     CHECK (shipping_cost >= 0),
    CONSTRAINT chk_orders_tax              CHECK (tax_amount >= 0),
    CONSTRAINT chk_orders_total            CHECK (total_amount >= 0)
);
COMMENT ON TABLE orders IS 'Core sales entity; address/shipping/coupon are FKs, not embedded strings (3NF)';

-- ---------------------------------------------------------------------------
-- TABLE: order_items  [ASSOCIATIVE TABLE — Line Items]
-- Purpose: Each line in an order for a specific product variant.
--          variant_id (not product_id) ensures correct inventory deduction.
-- FD: id → {order_id, variant_id, quantity, unit_price, discount_amount, line_total}
--     (order_id, variant_id) is composite AK
-- Generated column: line_total = (unit_price - discount_amount) * quantity
-- ---------------------------------------------------------------------------
CREATE TABLE order_items (
    id              BIGSERIAL    PRIMARY KEY,
    order_id        BIGINT       NOT NULL REFERENCES orders(id)          ON DELETE CASCADE,
    variant_id      BIGINT       NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    quantity        SMALLINT     NOT NULL,
    unit_price      NUMERIC(12,2) NOT NULL,      -- price at time of order (snapshot)
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    -- Generated column prevents calculation inconsistency
    line_total      NUMERIC(12,2) GENERATED ALWAYS AS
                    ((unit_price - discount_amount) * quantity) STORED,
    CONSTRAINT uq_order_items_order_variant UNIQUE (order_id, variant_id),
    CONSTRAINT chk_order_items_quantity     CHECK (quantity > 0),
    CONSTRAINT chk_order_items_unit_price   CHECK (unit_price > 0),
    CONSTRAINT chk_order_items_discount     CHECK (discount_amount >= 0 AND discount_amount <= unit_price)
);
COMMENT ON TABLE order_items IS 'Order line items at variant level; line_total is a generated column';

-- ---------------------------------------------------------------------------
-- TABLE: order_status_history  [AUDIT LOG]
-- Purpose: Full audit trail of every order status change.
--          Answers: "When did this order get shipped? Who changed it?"
-- FD: id → {order_id, from_status, to_status, changed_by, notes, changed_at}
-- ---------------------------------------------------------------------------
CREATE TABLE order_status_history (
    id          BIGSERIAL       PRIMARY KEY,
    order_id    BIGINT          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    from_status order_status,               -- NULL for initial creation
    to_status   order_status    NOT NULL,
    changed_by  BIGINT          REFERENCES admins(id) ON DELETE SET NULL,
    notes       TEXT,
    changed_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE order_status_history IS 'Immutable audit trail of order status transitions';

-- ---------------------------------------------------------------------------
-- TABLE: payments
-- Purpose: Payment record per order. 1:1 with orders in current design,
--          but separate table allows future multi-payment (installments).
-- FD: id → {order_id, payment_method, payment_status, amount, transaction_ref,
--           gateway_response, paid_at}
--     order_id is alternate candidate key (1:1 currently)
-- ---------------------------------------------------------------------------
CREATE TABLE payments (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    payment_method      VARCHAR(50)     NOT NULL,   -- 'bkash', 'card', 'cod', 'nagad'
    payment_status      payment_status  NOT NULL DEFAULT 'pending',
    amount              NUMERIC(12,2)   NOT NULL,
    transaction_ref     VARCHAR(150),              -- gateway transaction ID
    gateway_response    JSONB,                     -- full gateway response for audit
    paid_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_payments_order_id         UNIQUE (order_id),
    CONSTRAINT uq_payments_transaction_ref  UNIQUE (transaction_ref),
    CONSTRAINT chk_payments_amount          CHECK (amount > 0)
);
COMMENT ON TABLE payments IS 'Payment record per order; gateway_response stored as JSONB for full audit';

-- ---------------------------------------------------------------------------
-- TABLE: shipments
-- Purpose: Courier shipment record linked to an order.
-- FD: id → {order_id, shipping_method_id, tracking_number, carrier_name,
--           shipment_status, shipped_at, estimated_delivery, delivered_at}
--     tracking_number is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE shipments (
    id                  BIGSERIAL       PRIMARY KEY,
    order_id            BIGINT          NOT NULL REFERENCES orders(id)           ON DELETE CASCADE,
    shipping_method_id  BIGINT          REFERENCES shipping_methods(id)         ON DELETE SET NULL,
    tracking_number     VARCHAR(120),
    carrier_name        VARCHAR(100),
    shipment_status     shipment_status NOT NULL DEFAULT 'pending',
    shipped_at          TIMESTAMPTZ,
    estimated_delivery  DATE,
    delivered_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_shipments_order_id        UNIQUE (order_id),
    CONSTRAINT uq_shipments_tracking_number UNIQUE (tracking_number),
    CONSTRAINT chk_shipments_delivery_dates CHECK (
        delivered_at IS NULL OR shipped_at IS NULL OR delivered_at >= shipped_at
    )
);
COMMENT ON TABLE shipments IS 'Shipment record per order; tracking_number is unique alternate key';

-- ---------------------------------------------------------------------------
-- TABLE: invoices
-- Purpose: Formal invoice document generated for each order.
--          Separate from orders because invoice has its own numbering system,
--          tax calculation, and legal retention requirements.
-- FD: id → {order_id, invoice_number, subtotal, tax_amount, discount_amount,
--           total_amount, issued_at}
--     invoice_number is alternate candidate key
-- ---------------------------------------------------------------------------
CREATE TABLE invoices (
    id              BIGSERIAL    PRIMARY KEY,
    order_id        BIGINT       NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    invoice_number  VARCHAR(30)  NOT NULL,     -- auto-generated by trigger
    subtotal        NUMERIC(12,2) NOT NULL,
    tax_amount      NUMERIC(10,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_amount    NUMERIC(12,2) NOT NULL,
    notes           TEXT,
    issued_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_invoices_order_id        UNIQUE (order_id),
    CONSTRAINT uq_invoices_invoice_number  UNIQUE (invoice_number),
    CONSTRAINT chk_invoices_subtotal       CHECK (subtotal >= 0),
    CONSTRAINT chk_invoices_tax            CHECK (tax_amount >= 0),
    CONSTRAINT chk_invoices_discount       CHECK (discount_amount >= 0),
    CONSTRAINT chk_invoices_total          CHECK (total_amount >= 0)
);
COMMENT ON TABLE invoices IS 'Formal invoice per order; invoice_number auto-generated by trigger';

-- ---------------------------------------------------------------------------
-- TABLE: return_requests
-- Purpose: Customer return request for one or more items in an order.
-- FD: id → {order_id, customer_id, reason, status, approved_by, resolution_notes}
-- ---------------------------------------------------------------------------
CREATE TABLE return_requests (
    id              BIGSERIAL     PRIMARY KEY,
    order_id        BIGINT        NOT NULL REFERENCES orders(id)    ON DELETE RESTRICT,
    customer_id     BIGINT        NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    reason          TEXT          NOT NULL,
    status          return_status NOT NULL DEFAULT 'pending',
    approved_by     BIGINT        REFERENCES admins(id)            ON DELETE SET NULL,
    resolution_notes TEXT,
    requested_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE return_requests IS 'Customer return requests; approved_by references admin who processed it';

-- ---------------------------------------------------------------------------
-- TABLE: refunds
-- Purpose: Refund record generated after a return_request is approved.
--          Separate from payments to maintain distinct financial records.
-- FD: id → {return_request_id, refund_amount, refund_method, status, processed_at}
-- ---------------------------------------------------------------------------
CREATE TABLE refunds (
    id                  BIGSERIAL       PRIMARY KEY,
    return_request_id   BIGINT          NOT NULL REFERENCES return_requests(id) ON DELETE RESTRICT,
    refund_amount       NUMERIC(12,2)   NOT NULL,
    refund_method       VARCHAR(50)     NOT NULL,    -- original payment method
    status              payment_status  NOT NULL DEFAULT 'pending',
    transaction_ref     VARCHAR(150),
    processed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_refunds_return_request    UNIQUE (return_request_id),
    CONSTRAINT chk_refunds_amount           CHECK (refund_amount > 0)
);
COMMENT ON TABLE refunds IS 'Refund records; 1:1 with return_requests to maintain separate financial records';

-- =============================================================================
-- SECTION 10: FEEDBACK MODULE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: reviews
-- Purpose: Customer reviews at the variant level (specific color/size reviewed).
--          One review per (customer, variant) pair — enforced by UNIQUE constraint.
-- FD: id → {customer_id, variant_id, order_id, rating, title, body, is_approved}
--     (customer_id, variant_id) is composite alternate key
-- ---------------------------------------------------------------------------
CREATE TABLE reviews (
    id          BIGSERIAL    PRIMARY KEY,
    customer_id BIGINT       NOT NULL REFERENCES customers(id)        ON DELETE CASCADE,
    variant_id  BIGINT       NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    order_id    BIGINT       REFERENCES orders(id)                    ON DELETE SET NULL,
    rating      SMALLINT     NOT NULL,
    title       VARCHAR(200),
    body        TEXT,
    is_approved BOOLEAN      NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN      NOT NULL DEFAULT FALSE,   -- verified purchase
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reviews_customer_variant  UNIQUE (customer_id, variant_id),
    CONSTRAINT chk_reviews_rating           CHECK (rating BETWEEN 1 AND 5)
);
COMMENT ON TABLE reviews IS 'Variant-level reviews; (customer_id, variant_id) UNIQUE prevents duplicate reviews';

-- ---------------------------------------------------------------------------
-- TABLE: review_images
-- Purpose: Multiple images per review. Separate table eliminates 1NF violation.
-- FD: id → {review_id, image_url, sort_order}
-- ---------------------------------------------------------------------------
CREATE TABLE review_images (
    id          BIGSERIAL   PRIMARY KEY,
    review_id   BIGINT      NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    image_url   TEXT        NOT NULL,
    sort_order  SMALLINT    NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE review_images IS 'Customer review images; separate table prevents repeating-group 1NF violation';

-- ---------------------------------------------------------------------------
-- TABLE: review_replies
-- Purpose: Admin or seller response to a customer review.
-- FD: id → {review_id, admin_id, body, created_at}
--     review_id is alternate candidate key (one reply per review)
-- ---------------------------------------------------------------------------
CREATE TABLE review_replies (
    id          BIGSERIAL   PRIMARY KEY,
    review_id   BIGINT      NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    admin_id    BIGINT      NOT NULL REFERENCES admins(id)  ON DELETE RESTRICT,
    body        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_review_replies_review UNIQUE (review_id)   -- one reply per review
);
COMMENT ON TABLE review_replies IS 'Admin reply to customer reviews; one reply per review (UNIQUE on review_id)';

-- =============================================================================
-- SECTION 11: DEFERRED FOREIGN KEY CONSTRAINTS
-- These constraints reference tables created after the referencing table.
-- =============================================================================

-- wishlist_items.variant_id → product_variants.id
ALTER TABLE wishlist_items
    ADD CONSTRAINT fk_wishlist_items_variant
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE;

-- cart_items.variant_id → product_variants.id
ALTER TABLE cart_items
    ADD CONSTRAINT fk_cart_items_variant
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE;

-- coupon_usages.order_id → orders.id
ALTER TABLE coupon_usages
    ADD CONSTRAINT fk_coupon_usages_order
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;

-- =============================================================================
-- SECTION 12: JUNCTION TABLES FOR PRODUCT ↔ COLLECTION RELATIONSHIP
-- A product can belong to multiple collections (many-to-many).
-- Using collection_id in products would only allow one collection.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: product_collections  [M:M JUNCTION TABLE]
-- Purpose: A product can appear in multiple collections (e.g., "Summer Edit"
--          and "Beach Essentials"). This replaces the single collection_id FK.
-- FD: (product_id, collection_id) → added_at
-- Normal Form: BCNF
-- ---------------------------------------------------------------------------
CREATE TABLE product_collections (
    product_id      BIGINT      NOT NULL REFERENCES products(id)    ON DELETE CASCADE,
    collection_id   BIGINT      NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_product_collections PRIMARY KEY (product_id, collection_id)
);
COMMENT ON TABLE product_collections IS 'M:M junction: products ↔ collections (a product can be in multiple collections)';

-- Remove the single collection_id from products now that we have the junction table
-- (We keep it for simplicity of queries, and mark it as deprecated in documentation)
-- NOTE: In production, we'd drop it; for DBMS demo we keep it to show both patterns.

-- =============================================================================
-- SECTION 13: SEQUENCE OBJECTS FOR FORMATTED IDs
-- Used by triggers to generate human-readable order/invoice numbers.
-- =============================================================================

CREATE SEQUENCE IF NOT EXISTS order_number_seq   START 10001 INCREMENT 1;
CREATE SEQUENCE IF NOT EXISTS invoice_number_seq START 20001 INCREMENT 1;

-- =============================================================================
-- END OF SCHEMA
-- Table Count: 34 tables + 2 sequences + 8 ENUM types
-- Run next: 002_indexes.sql
-- =============================================================================
