# FashionHub — Entity-Relationship Diagram

## Complete ER Diagram (Mermaid)

```mermaid
erDiagram
    %% =========================================================
    %% LOOKUP / REFERENCE ENTITIES
    %% =========================================================
    GENDERS {
        smallserial id PK
        varchar(20) name UK
    }
    COLORS {
        smallserial id PK
        varchar(50) name UK
        char(7) hex_code
    }
    SIZES {
        smallserial id PK
        varchar(20) name
        size_category size_category
        smallint sort_order
    }
    MATERIALS {
        smallserial id PK
        varchar(80) name UK
        text description
    }
    SEASONS {
        smallserial id PK
        varchar(30) name UK
    }

    %% =========================================================
    %% ADMINISTRATION
    %% =========================================================
    ROLES {
        smallserial id PK
        varchar(50) name UK
        text description
    }
    PERMISSIONS {
        smallserial id PK
        varchar(100) code UK
        text description
    }
    ROLE_PERMISSIONS {
        smallint role_id FK
        smallint permission_id FK
        timestamptz granted_at
    }
    ADMINS {
        bigserial id PK
        varchar(255) email UK
        varchar(255) password_hash
        varchar(150) full_name
        smallint role_id FK
        boolean is_active
        timestamptz last_login_at
    }
    ACTIVITY_LOGS {
        bigserial id PK
        bigint admin_id FK
        varchar(100) action
        varchar(50) entity_type
        bigint entity_id
        jsonb old_value
        jsonb new_value
        inet ip_address
    }

    %% =========================================================
    %% BRANDS & SUPPLIERS
    %% =========================================================
    BRANDS {
        bigserial id PK
        varchar(150) name UK
        varchar(150) slug UK
        text logo_url
        varchar(100) country_of_origin
        boolean is_active
    }
    SUPPLIERS {
        bigserial id PK
        varchar(150) name UK
        varchar(255) contact_email UK
        varchar(30) contact_phone
        text address
        varchar(100) city
        varchar(100) country
        smallint lead_time_days
        numeric reliability_score
    }

    %% =========================================================
    %% CATEGORIES
    %% =========================================================
    CATEGORIES {
        bigserial id PK
        varchar(120) name UK
        varchar(120) slug UK
        text description
        boolean is_active
    }
    SUBCATEGORIES {
        bigserial id PK
        bigint category_id FK
        varchar(120) name
        varchar(120) slug UK
        boolean is_active
    }
    COLLECTIONS {
        bigserial id PK
        varchar(150) name UK
        varchar(150) slug UK
        smallint season_id FK
        date start_date
        date end_date
    }

    %% =========================================================
    %% WAREHOUSES
    %% =========================================================
    WAREHOUSES {
        bigserial id PK
        varchar(150) name UK
        varchar(20) code UK
        text address
        varchar(100) city
        integer capacity
    }

    %% =========================================================
    %% CUSTOMERS
    %% =========================================================
    CUSTOMERS {
        bigserial id PK
        varchar(255) email UK
        varchar(255) password_hash
        boolean is_active
        boolean email_verified
    }
    CUSTOMER_PROFILES {
        bigint customer_id PK_FK
        varchar(100) first_name
        varchar(100) last_name
        varchar(30) phone UK
        date date_of_birth
        smallint gender_id FK
        text avatar_url
    }
    CUSTOMER_ADDRESSES {
        bigserial id PK
        bigint customer_id FK
        varchar(50) label
        varchar(150) recipient_name
        varchar(255) line1
        varchar(100) city
        varchar(100) country
        boolean is_default
    }
    WISHLISTS {
        bigserial id PK
        bigint customer_id FK_UK
    }
    WISHLIST_ITEMS {
        bigserial id PK
        bigint wishlist_id FK
        bigint variant_id FK
        timestamptz added_at
    }
    CARTS {
        bigserial id PK
        bigint customer_id FK_UK
    }
    CART_ITEMS {
        bigserial id PK
        bigint cart_id FK
        bigint variant_id FK
        smallint quantity
    }
    CUSTOMER_NOTIFICATIONS {
        bigserial id PK
        bigint customer_id FK
        notification_type type
        varchar(200) title
        boolean is_read
    }

    %% =========================================================
    %% PRODUCTS
    %% =========================================================
    PRODUCTS {
        bigserial id PK
        varchar(200) name
        varchar(200) slug UK
        bigint brand_id FK
        bigint supplier_id FK
        bigint subcategory_id FK
        bigint collection_id FK
        smallint gender_id FK
        numeric base_price
        boolean is_active
    }
    PRODUCT_IMAGES {
        bigserial id PK
        bigint product_id FK
        text image_url
        smallint sort_order
        boolean is_primary
    }
    PRODUCT_VARIANTS {
        bigserial id PK
        bigint product_id FK
        smallint color_id FK
        smallint size_id FK
        smallint material_id FK
        varchar(100) sku UK
        varchar(100) barcode UK
        numeric price_override
        boolean is_active
    }
    PRODUCT_SPECIFICATIONS {
        bigserial id PK
        bigint product_id FK
        varchar(100) spec_key
        text spec_value
    }
    PRODUCT_COLLECTIONS {
        bigint product_id FK
        bigint collection_id FK
        timestamptz added_at
    }

    %% =========================================================
    %% INVENTORY
    %% =========================================================
    INVENTORY {
        bigserial id PK
        bigint variant_id FK
        bigint warehouse_id FK
        integer current_stock
        integer reserved_stock
        integer available_stock "GENERATED"
        integer reorder_level
    }
    INVENTORY_MOVEMENTS {
        bigserial id PK
        bigint inventory_id FK
        movement_type movement_type
        integer quantity
        varchar(50) reference_type
        bigint reference_id
        bigint created_by FK
    }

    %% =========================================================
    %% SALES
    %% =========================================================
    SHIPPING_METHODS {
        bigserial id PK
        varchar(100) name UK
        varchar(100) carrier
        numeric base_rate
        smallint estimated_days
    }
    COUPONS {
        bigserial id PK
        varchar(50) code UK
        coupon_type coupon_type
        numeric value
        integer used_count
        timestamptz valid_until
    }
    COUPON_USAGES {
        bigserial id PK
        bigint coupon_id FK
        bigint customer_id FK
        bigint order_id FK
        numeric discount_applied
    }
    ORDERS {
        bigserial id PK
        varchar(20) order_number UK
        bigint customer_id FK
        bigint shipping_address_id FK
        bigint billing_address_id FK
        bigint shipping_method_id FK
        bigint coupon_id FK
        order_status status
        numeric subtotal
        numeric total_amount
    }
    ORDER_ITEMS {
        bigserial id PK
        bigint order_id FK
        bigint variant_id FK
        smallint quantity
        numeric unit_price
        numeric line_total "GENERATED"
    }
    ORDER_STATUS_HISTORY {
        bigserial id PK
        bigint order_id FK
        order_status from_status
        order_status to_status
        bigint changed_by FK
    }
    PAYMENTS {
        bigserial id PK
        bigint order_id FK_UK
        varchar(50) payment_method
        payment_status payment_status
        numeric amount
        varchar(150) transaction_ref UK
    }
    SHIPMENTS {
        bigserial id PK
        bigint order_id FK_UK
        bigint shipping_method_id FK
        varchar(120) tracking_number UK
        shipment_status shipment_status
        timestamptz shipped_at
        timestamptz delivered_at
    }
    INVOICES {
        bigserial id PK
        bigint order_id FK_UK
        varchar(30) invoice_number UK
        numeric subtotal
        numeric total_amount
    }
    RETURN_REQUESTS {
        bigserial id PK
        bigint order_id FK
        bigint customer_id FK
        text reason
        return_status status
        bigint approved_by FK
    }
    REFUNDS {
        bigserial id PK
        bigint return_request_id FK_UK
        numeric refund_amount
        varchar(50) refund_method
        payment_status status
    }

    %% =========================================================
    %% FEEDBACK
    %% =========================================================
    REVIEWS {
        bigserial id PK
        bigint customer_id FK
        bigint variant_id FK
        bigint order_id FK
        smallint rating
        varchar(200) title
        boolean is_approved
    }
    REVIEW_IMAGES {
        bigserial id PK
        bigint review_id FK
        text image_url
    }
    REVIEW_REPLIES {
        bigserial id PK
        bigint review_id FK_UK
        bigint admin_id FK
        text body
    }

    %% =========================================================
    %% RELATIONSHIPS
    %% =========================================================

    %% Lookup relationships
    GENDERS         ||--o{ CUSTOMER_PROFILES : "gender_id"
    GENDERS         ||--o{ PRODUCTS          : "gender_id"
    COLORS          ||--o{ PRODUCT_VARIANTS  : "color_id"
    SIZES           ||--o{ PRODUCT_VARIANTS  : "size_id"
    MATERIALS       ||--o{ PRODUCT_VARIANTS  : "material_id"
    SEASONS         ||--o{ COLLECTIONS       : "season_id"

    %% Admin
    ROLES           ||--o{ ADMINS            : "has role"
    ROLES           ||--o{ ROLE_PERMISSIONS  : "grants"
    PERMISSIONS     ||--o{ ROLE_PERMISSIONS  : "granted via"
    ADMINS          ||--o{ ACTIVITY_LOGS     : "logged by"
    ADMINS          ||--o{ INVENTORY_MOVEMENTS : "created by"
    ADMINS          ||--o{ ORDER_STATUS_HISTORY : "changed by"
    ADMINS          ||--o{ RETURN_REQUESTS   : "approved by"
    ADMINS          ||--|| REVIEW_REPLIES    : "replies"

    %% Catalog
    BRANDS          ||--o{ PRODUCTS          : "manufactures"
    SUPPLIERS       ||--o{ PRODUCTS          : "supplies"
    CATEGORIES      ||--o{ SUBCATEGORIES     : "contains"
    SUBCATEGORIES   ||--o{ PRODUCTS          : "classifies"
    COLLECTIONS     ||--o{ PRODUCTS          : "features"
    PRODUCTS        ||--o{ PRODUCT_IMAGES    : "has images"
    PRODUCTS        ||--o{ PRODUCT_VARIANTS  : "has variants"
    PRODUCTS        ||--o{ PRODUCT_SPECIFICATIONS : "specifies"
    PRODUCTS        ||--o{ PRODUCT_COLLECTIONS : "in collections"
    COLLECTIONS     ||--o{ PRODUCT_COLLECTIONS : "contains"

    %% Inventory
    PRODUCT_VARIANTS ||--o{ INVENTORY        : "stocked at"
    WAREHOUSES      ||--o{ INVENTORY         : "holds"
    INVENTORY       ||--o{ INVENTORY_MOVEMENTS : "movement"

    %% Customers
    CUSTOMERS       ||--|| CUSTOMER_PROFILES  : "has profile"
    CUSTOMERS       ||--o{ CUSTOMER_ADDRESSES : "has addresses"
    CUSTOMERS       ||--|| WISHLISTS          : "has wishlist"
    CUSTOMERS       ||--|| CARTS              : "has cart"
    CUSTOMERS       ||--o{ CUSTOMER_NOTIFICATIONS : "notified"
    WISHLISTS       ||--o{ WISHLIST_ITEMS     : "contains"
    PRODUCT_VARIANTS ||--o{ WISHLIST_ITEMS   : "wishlisted as"
    CARTS           ||--o{ CART_ITEMS         : "contains"
    PRODUCT_VARIANTS ||--o{ CART_ITEMS        : "in cart as"

    %% Orders
    CUSTOMERS       ||--o{ ORDERS            : "places"
    CUSTOMER_ADDRESSES ||--o{ ORDERS         : "shipped to"
    SHIPPING_METHODS   ||--o{ ORDERS         : "uses"
    COUPONS         ||--o{ ORDERS            : "applied to"
    ORDERS          ||--o{ ORDER_ITEMS       : "contains"
    PRODUCT_VARIANTS   ||--o{ ORDER_ITEMS    : "ordered as"
    ORDERS          ||--o{ ORDER_STATUS_HISTORY : "tracks"
    ORDERS          ||--|| PAYMENTS          : "paid via"
    ORDERS          ||--|| SHIPMENTS         : "shipped via"
    ORDERS          ||--|| INVOICES          : "invoiced as"
    ORDERS          ||--o{ RETURN_REQUESTS   : "returned by"
    RETURN_REQUESTS ||--|| REFUNDS           : "refunded as"
    SHIPPING_METHODS   ||--o{ SHIPMENTS      : "uses"
    COUPONS         ||--o{ COUPON_USAGES     : "used in"
    CUSTOMERS       ||--o{ COUPON_USAGES     : "uses coupon"

    %% Feedback
    CUSTOMERS       ||--o{ REVIEWS           : "writes"
    PRODUCT_VARIANTS ||--o{ REVIEWS          : "reviewed as"
    ORDERS          ||--o{ REVIEWS           : "verified from"
    REVIEWS         ||--o{ REVIEW_IMAGES     : "includes"
    REVIEWS         ||--|| REVIEW_REPLIES    : "replied to"
    CUSTOMERS       ||--o{ RETURN_REQUESTS   : "requests"
```

---

## Table Summary (34 Tables)

| # | Table | Module | Type | PK Type |
|---|-------|--------|------|---------|
| 1 | `genders` | Lookup | Reference | SMALLSERIAL |
| 2 | `colors` | Lookup | Reference | SMALLSERIAL |
| 3 | `sizes` | Lookup | Reference | SMALLSERIAL |
| 4 | `materials` | Lookup | Reference | SMALLSERIAL |
| 5 | `seasons` | Lookup | Reference | SMALLSERIAL |
| 6 | `roles` | Admin | Reference | SMALLSERIAL |
| 7 | `permissions` | Admin | Reference | SMALLSERIAL |
| 8 | `role_permissions` | Admin | **Junction (M:M)** | Composite (role_id, permission_id) |
| 9 | `admins` | Admin | Entity | BIGSERIAL |
| 10 | `activity_logs` | Admin | **Audit Log** | BIGSERIAL |
| 11 | `brands` | Product | Entity | BIGSERIAL |
| 12 | `suppliers` | Product | Entity | BIGSERIAL |
| 13 | `categories` | Product | Entity | BIGSERIAL |
| 14 | `subcategories` | Product | Entity | BIGSERIAL |
| 15 | `collections` | Product | Entity | BIGSERIAL |
| 16 | `warehouses` | Inventory | Entity | BIGSERIAL |
| 17 | `customers` | Customer | **Auth Entity** | BIGSERIAL |
| 18 | `customer_profiles` | Customer | **1:1 Extension** | FK (customer_id) |
| 19 | `customer_addresses` | Customer | Entity | BIGSERIAL |
| 20 | `wishlists` | Customer | Entity | BIGSERIAL |
| 21 | `wishlist_items` | Customer | Junction | BIGSERIAL |
| 22 | `carts` | Customer | Entity | BIGSERIAL |
| 23 | `cart_items` | Customer | Junction | BIGSERIAL |
| 24 | `customer_notifications` | Customer | Log | BIGSERIAL |
| 25 | `products` | Product | **Base Entity** | BIGSERIAL |
| 26 | `product_images` | Product | Weak | BIGSERIAL |
| 27 | `product_variants` | Product | **Core SKU Entity** | BIGSERIAL |
| 28 | `product_specifications` | Product | EAV | BIGSERIAL |
| 29 | `product_collections` | Product | **Junction (M:M)** | Composite |
| 30 | `inventory` | Inventory | Entity | BIGSERIAL |
| 31 | `inventory_movements` | Inventory | **Audit Ledger** | BIGSERIAL |
| 32 | `shipping_methods` | Sales | Reference | BIGSERIAL |
| 33 | `coupons` | Sales | Entity | BIGSERIAL |
| 34 | `coupon_usages` | Sales | Junction | BIGSERIAL |
| 35 | `orders` | Sales | **Core Sales Entity** | BIGSERIAL |
| 36 | `order_items` | Sales | Junction | BIGSERIAL |
| 37 | `order_status_history` | Sales | **Audit Log** | BIGSERIAL |
| 38 | `payments` | Sales | Entity | BIGSERIAL |
| 39 | `shipments` | Sales | Entity | BIGSERIAL |
| 40 | `invoices` | Sales | Entity | BIGSERIAL |
| 41 | `return_requests` | Sales | Entity | BIGSERIAL |
| 42 | `refunds` | Sales | Entity | BIGSERIAL |
| 43 | `reviews` | Feedback | Entity | BIGSERIAL |
| 44 | `review_images` | Feedback | Weak | BIGSERIAL |
| 45 | `review_replies` | Feedback | Entity | BIGSERIAL |

---

## Key Design Patterns Highlighted

### 1. Auth ↔ Profile Separation (3NF)
```
customers (id, email, password_hash)
    ↓ 1:1
customer_profiles (customer_id, first_name, last_name, phone, gender_id)
```

### 2. Product ↔ Variant ↔ Inventory (2NF + Proper Normalization)
```
products (base attributes, no stock/SKU/color/size)
    ↓ 1:M
product_variants (SKU, barcode, color_id FK, size_id FK, material_id FK)
    ↓ 1:M
inventory (variant_id FK, warehouse_id FK, current_stock, reserved_stock)
    → available_stock GENERATED ALWAYS AS (current_stock - reserved_stock) STORED
```

### 3. Order Address Normalization (3NF)
```
orders.shipping_address_id → customer_addresses(id)
    Not: orders.shipping_address VARCHAR(500) [embedded string — 3NF violation]
```

### 4. Composite Primary Keys on Junction Tables
```
role_permissions    → PRIMARY KEY (role_id, permission_id)
product_collections → PRIMARY KEY (product_id, collection_id)
```

### 5. Generated Columns (Eliminates Derived Data Anomalies)
```
inventory.available_stock   GENERATED ALWAYS AS (current_stock - reserved_stock) STORED
order_items.line_total      GENERATED ALWAYS AS ((unit_price - discount_amount) * quantity) STORED
```
