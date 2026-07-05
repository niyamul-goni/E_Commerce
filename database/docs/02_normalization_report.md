# FashionHub — Normalization Report
## 1NF / 2NF / 3NF / BCNF Analysis for Every Table

> **Notation Used:**
> - FD = Functional Dependency: X → Y means "X determines Y"
> - PK = Primary Key
> - AK = Alternate Key (Candidate Key that wasn't chosen as PK)
> - CK = Candidate Key (any minimal superkey)

---

## Normal Form Definitions

| Form | Requirement |
|------|-------------|
| **1NF** | All attributes are atomic (no repeating groups, no multi-valued attributes) |
| **2NF** | In 1NF + no partial dependency (every non-key attribute depends on the WHOLE primary key) |
| **3NF** | In 2NF + no transitive dependency (non-key attributes depend only on the PK, not on other non-key attributes) |
| **BCNF** | For every FD X→Y, X must be a superkey. Stricter than 3NF. |

---

## MODULE: LOOKUP TABLES

### `genders`
| Attribute | Type |
|-----------|------|
| id (PK) | SMALLSERIAL |
| name (AK) | VARCHAR(20) |

**Functional Dependencies:**
- `id → name`
- `name → id` (alternate key)

**Candidate Keys:** {id}, {name}

**1NF:** ✅ All attributes atomic, no repeating groups.
**2NF:** ✅ PK is single column; partial dependency impossible.
**3NF:** ✅ No transitive dependency (only one non-key: name).
**BCNF:** ✅ Both FDs have superkeys on the left side.

---

### `colors`
| Attribute | Type |
|-----------|------|
| id (PK) | SMALLSERIAL |
| name (AK) | VARCHAR(50) |
| hex_code | CHAR(7) |

**FDs:**
- `id → {name, hex_code}`
- `name → {id, hex_code}` (name is AK)

**Candidate Keys:** {id}, {name}

**3NF/BCNF:** ✅ hex_code depends only on id (and name), never transitively. No non-key attribute determines another non-key attribute.

---

### `sizes`
| Attribute | Type |
|-----------|------|
| id (PK) | SMALLSERIAL |
| name | VARCHAR(20) |
| size_category | ENUM |
| sort_order | SMALLINT |

**FDs:**
- `id → {name, size_category, sort_order}`
- `{name, size_category} → {id, sort_order}` (composite AK)

**Candidate Keys:** {id}, {name, size_category}

**2NF/3NF/BCNF:** ✅ The composite AK shows that `name` alone does NOT determine all attributes (XS clothing ≠ XS bags), so the split is necessary.

> **Design Justification:** Without `size_category`, "XS" would appear multiple times for different categories, violating 1NF's spirit of uniqueness. The composite key properly identifies each size in context.

---

## MODULE: ADMINISTRATION

### `role_permissions`
| Attribute | Type |
|-----------|------|
| role_id (PK1, FK) | SMALLINT |
| permission_id (PK2, FK) | SMALLINT |
| granted_at | TIMESTAMPTZ |

**FD:** `{role_id, permission_id} → granted_at`

**Candidate Key:** {role_id, permission_id} (composite)

**BCNF:** ✅ The only FD has the full composite PK on the left side. Classic junction table — BCNF by definition.

> **Design Justification:** This table models a pure M:M relationship. Storing permissions as an ARRAY in the `roles` table would violate 1NF.

---

### `admins`
| Attribute | Type |
|-----------|------|
| id (PK) | BIGSERIAL |
| email (AK) | VARCHAR(255) |
| password_hash | VARCHAR |
| full_name | VARCHAR |
| role_id (FK) | SMALLINT |
| is_active | BOOLEAN |

**FDs:**
- `id → {email, password_hash, full_name, role_id, is_active}`
- `email → {id, password_hash, full_name, role_id, is_active}`

**2NF:** ✅ Single-column PK.
**3NF:** ✅ No transitive FDs — `role_id` is a foreign key (reference), not a derived attribute. The role's `name` and `description` live in the `roles` table, not here. This is exactly 3NF compliance.

> **Key 3NF decision:** If we stored `role_name` directly in admins, then `id → role_id → role_name` would be a transitive dependency, violating 3NF. By referencing `role_id` FK, the design is correct.

---

## MODULE: BRANDS & SUPPLIERS

### `brands`
**3NF Analysis:**
- `id → {name, slug, logo_url, country_of_origin, description, website_url, is_active}`
- `name → id` (AK)

**Potential transitive dependency removed:** If products contained `brand_country_of_origin VARCHAR`, then: `product.id → brand_id → country_of_origin` — transitive dependency violating 3NF. By normalizing brands into a separate table, this is eliminated.

**BCNF:** ✅ Both `id` and `name` are superkeys; no FD with non-superkey on left.

---

### `suppliers`
**3NF:**
- `id → {name, contact_email, contact_phone, address, city, country, lead_time_days, reliability_score}`
- `contact_email → id` (AK)

**Design Decision:** `lead_time_days` and `reliability_score` are attributes of the SUPPLIER as an entity, not of individual products. If stored in the product table: `product_id → supplier_id → lead_time_days` = transitive dependency. Separate table eliminates this.

---

## MODULE: PRODUCT CATEGORIES

### `subcategories`
| Attribute | Type |
|-----------|------|
| id (PK) | BIGSERIAL |
| category_id (FK) | BIGINT |
| name | VARCHAR(120) |
| slug (AK) | VARCHAR(120) |

**FDs:**
- `id → {category_id, name, slug, description, is_active}`
- `slug → id` (AK, global uniqueness)
- `{category_id, name} → id` (composite AK — name unique per category)

**2NF Verification:** Does `name` depend on only `category_id` (partial)? No — `name` needs `id` to be unique globally. The `{category_id, name}` composite is an ALTERNATE key, not the primary key. The PK is `id` alone — no partial dependencies exist.

**3NF:** ✅ `category_id` is a FK reference, not a derivable attribute. The category's attributes (description, slug) are in the `categories` table.

---

## MODULE: CUSTOMERS (Critical 3NF Separation)

### `customers` vs `customer_profiles`

**Problem with naive design:**
```
customers(id, email, password_hash, first_name, last_name, phone, date_of_birth, gender_id)
```
All non-key attributes depend on `id`. **No normalization violation technically.** However:

**Design Reasoning for Separation:**
1. `email` + `password_hash` = authentication concerns
2. `first_name`, `last_name`, `phone`, `date_of_birth` = profile/personal data
3. These are **conceptually different entities** that may evolve independently
4. Aligns with **Single Responsibility Principle** for tables
5. Enables profile updates without touching auth records (security isolation)
6. Enables Supabase Auth integration later (auth.users vs profile data)

**Functional Dependencies — customers:**
- `id → {email, password_hash, is_active, email_verified}`
- `email → id` (AK)

**Functional Dependencies — customer_profiles:**
- `customer_id → {first_name, last_name, phone, date_of_birth, gender_id, avatar_url}`
- `phone → customer_id` (AK, partial — if non-null)

**3NF:** ✅ `gender_id` is a FK reference to genders table. Without normalization: `customer_id → gender_id → gender_name` = transitive dependency.

---

### `customer_addresses`
**FDs:**
- `id → {customer_id, label, recipient_name, phone, line1, line2, city, state, postal_code, country, is_default}`

**3NF Check:** Could `city → country` be a dependency? **No** — a customer could have addresses in multiple cities and countries. City does not functionally determine country in this context (no lookup table). This is appropriate.

**Key Design:** `is_default` is a per-customer flag. A customer can have multiple addresses, only one default.

---

## MODULE: PRODUCTS (Core Normalization — 2NF Focus)

### `products` vs `product_variants` — THE CRITICAL 2NF DECISION

**Anti-pattern (what NOT to do):**
```sql
-- BAD: Stock, SKU, color, size in product table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    sku VARCHAR,          -- ← Multiple SKUs per product? Repeating group!
    color VARCHAR,        -- ← Not atomic if multiple colors
    size VARCHAR,         -- ← Not atomic if multiple sizes
    stock INTEGER         -- ← Which size's stock?
);
```

**Why this violates normalization:**
1. **1NF violation**: A product has multiple colors/sizes — storing as comma-separated list violates 1NF
2. **Repeating groups**: Creating columns `color1`, `color2`, `size1`, `size2` violates 1NF
3. **2NF violation if composite PK**: If PK were `(product_id, size)`, then `name` would depend only on `product_id` (partial dependency on non-full PK)

**Correct Design:**
```
products (id, name, brand_id, base_price, ...)  ← product-level attributes
    ↓ 1:M
product_variants (id, product_id, color_id, size_id, material_id, sku, ...)
                                   ↑ each purchasable unit is its own row
```

**2NF Proof for product_variants:**
- PK: `id` (single column, so partial dependency impossible)
- FD: `id → {product_id, color_id, size_id, material_id, sku, barcode, price_override}`
- Composite AK: `{product_id, color_id, size_id, material_id}` → uniquely identifies a variant

**BCNF for product_variants:**
The FD `sku → id` exists (sku is AK). Does `sku` determine `color_id`? Yes, because SKU uniquely identifies a variant. Both `id` and `sku` are superkeys, so BCNF holds.

---

### `product_specifications` — EAV Pattern Justification

**Problem with wide-column approach:**
```sql
-- BAD for heterogeneous products
CREATE TABLE product_specs (
    product_id INT,
    movement_type VARCHAR,    -- only for watches
    case_diameter VARCHAR,    -- only for watches
    heel_height VARCHAR,      -- only for shoes
    toe_shape VARCHAR,        -- only for shoes
    -- 50+ nullable columns...
);
```

**Why this is problematic:**
- Sparse matrix of NULLs (most columns NULL for any product)
- New spec type requires ALTER TABLE
- Violates BCNF: `product_id → movement_type` only when product is a watch

**EAV Solution:**
```
product_specifications(id, product_id, spec_key, spec_value)
```

**FD:** `{product_id, spec_key} → spec_value`
**Candidate Key:** {product_id, spec_key}
**BCNF:** ✅ The composite key is the only candidate key.

---

## MODULE: INVENTORY

### `inventory` — Generated Column

**FDs:**
- `id → {variant_id, warehouse_id, current_stock, reserved_stock, reorder_level}`
- `{variant_id, warehouse_id} → id` (composite AK)
- `id → available_stock` (but this is DERIVED: current_stock - reserved_stock)

**Generated Column Justification:**
Without the generated column, `available_stock` would be a derived attribute. If stored as a regular column, it creates a **derived data anomaly**:
- Update `current_stock` → forget to update `available_stock` → inconsistency
- The generated column eliminates this entire class of bugs at the schema level.

**3NF:** ✅ No non-key attribute determines another non-key attribute. The generated column is computed from base facts, not stored redundantly.

---

### `inventory_movements` — Immutable Ledger

**FDs:**
- `id → {inventory_id, movement_type, quantity, reference_type, reference_id, notes, created_at}`

**Design Decision:** This table is append-only (like a financial ledger). Every stock change creates a new row. This enables:
- Full audit trail
- Stock reconciliation
- Point-in-time stock reconstruction (sum of all movements = current stock)

---

## MODULE: SALES

### `orders` — 3NF with Address Normalization

**Anti-pattern (existing code's violation):**
```sql
-- OLD BAD DESIGN in schema.sql
shipping_address VARCHAR(500) NOT NULL   -- embedded string!
```

**3NF Violation in old design:**
If `shipping_address` contains city, country, postal code — these could have FDs:
`postal_code → city` (a postal code implies a city) — but mixing them into a single VARCHAR makes this unenforceable.

**New Correct Design:**
```sql
shipping_address_id BIGINT REFERENCES customer_addresses(id)
```

`customer_addresses` normalizes address components. `orders` references the address by ID. This:
1. Eliminates transitive dependency through address components
2. Enables address reuse (customer's saved addresses)
3. Allows address history without order modification

**FDs for orders:**
- `id → {order_number, customer_id, shipping_address_id, billing_address_id, shipping_method_id, coupon_id, status, subtotal, discount_amount, shipping_cost, tax_amount, total_amount}`
- `order_number → id` (AK)

**3NF Transitivity Check:**
- `id → coupon_id` but `coupon_id → {code, type, value}` — coupon details NOT stored in orders. ✅
- `id → shipping_method_id` but `shipping_method_id → {name, base_rate}` — shipping details NOT stored in orders. ✅

---

### `order_items` — Generated Column

**FD:** `id → {order_id, variant_id, quantity, unit_price, discount_amount}`
**Composite AK:** `{order_id, variant_id}`
**Generated:** `line_total = (unit_price - discount_amount) * quantity`

**Why store unit_price in order_items?**
This is a **snapshot** of the price at time of order. If `price_override` in `product_variants` changes, the historical order line items must not change. This is a deliberate denormalization for **temporal correctness** — it captures the price as it was at purchase time.

---

## MODULE: FEEDBACK

### `reviews` — Preventing 1NF Violation

**Old single-column approach (BAD):**
```sql
-- Storing multiple review images as comma-separated string
review_images TEXT   -- '{"url1","url2","url3"}'  ← 1NF violation
```

**Correct Design:**
```
reviews (id, customer_id, variant_id, rating, title, body)
    ↓ 1:M
review_images (id, review_id, image_url, sort_order)
```

Each image is its own row. This is exactly the 1NF requirement: no repeating groups, each attribute is atomic.

**Duplicate Review Prevention:**
`UNIQUE(customer_id, variant_id)` enforces the business rule that one customer can review a specific variant only once. This is a **constraint**, not a normalization issue, but both work together.

---

## Normalization Summary Table

| Table | 1NF | 2NF | 3NF | BCNF | Key Notes |
|-------|-----|-----|-----|------|-----------|
| genders | ✅ | ✅ | ✅ | ✅ | Single non-key attribute |
| colors | ✅ | ✅ | ✅ | ✅ | hex_code depends only on id |
| sizes | ✅ | ✅ | ✅ | ✅ | Composite AK (name, category) |
| materials | ✅ | ✅ | ✅ | ✅ | Simple lookup |
| seasons | ✅ | ✅ | ✅ | ✅ | Simple lookup |
| roles | ✅ | ✅ | ✅ | ✅ | Simple entity |
| permissions | ✅ | ✅ | ✅ | ✅ | Simple entity |
| role_permissions | ✅ | ✅ | ✅ | ✅ | Pure junction, composite PK |
| admins | ✅ | ✅ | ✅ | ✅ | role_id FK avoids transitive dep |
| activity_logs | ✅ | ✅ | ✅ | ✅ | Immutable audit log |
| brands | ✅ | ✅ | ✅ | ✅ | Separated from products (3NF) |
| suppliers | ✅ | ✅ | ✅ | ✅ | lead_time belongs to supplier |
| categories | ✅ | ✅ | ✅ | ✅ | Independent entity |
| subcategories | ✅ | ✅ | ✅ | ✅ | category_id FK (not denorm) |
| collections | ✅ | ✅ | ✅ | ✅ | season_id FK |
| warehouses | ✅ | ✅ | ✅ | ✅ | Independent entity |
| customers | ✅ | ✅ | ✅ | ✅ | Auth-only (3NF separation) |
| customer_profiles | ✅ | ✅ | ✅ | ✅ | 1:1 extension of customers |
| customer_addresses | ✅ | ✅ | ✅ | ✅ | Normalized from order strings |
| wishlists | ✅ | ✅ | ✅ | ✅ | 1:1 with customers |
| wishlist_items | ✅ | ✅ | ✅ | ✅ | Junction, composite AK |
| carts | ✅ | ✅ | ✅ | ✅ | 1:1 with customers |
| cart_items | ✅ | ✅ | ✅ | ✅ | Junction, variant-level |
| products | ✅ | ✅ | ✅ | ✅ | **No stock/SKU/color/size** |
| product_images | ✅ | ✅ | ✅ | ✅ | 1NF: no repeating image columns |
| product_variants | ✅ | ✅ | ✅ | ✅ | **Central 2NF fix** |
| product_specifications | ✅ | ✅ | ✅ | ✅ | EAV for flexible attributes |
| product_collections | ✅ | ✅ | ✅ | ✅ | M:M junction |
| inventory | ✅ | ✅ | ✅ | ✅ | Generated column (no derivation) |
| inventory_movements | ✅ | ✅ | ✅ | ✅ | Append-only ledger |
| shipping_methods | ✅ | ✅ | ✅ | ✅ | Separated from orders |
| coupons | ✅ | ✅ | ✅ | ✅ | code is AK |
| coupon_usages | ✅ | ✅ | ✅ | ✅ | Composite AK prevents reuse |
| orders | ✅ | ✅ | ✅ | ✅ | **Address FK (3NF fix)** |
| order_items | ✅ | ✅ | ✅ | ✅ | unit_price snapshot (temporal) |
| order_status_history | ✅ | ✅ | ✅ | ✅ | Audit log |
| payments | ✅ | ✅ | ✅ | ✅ | JSONB for gateway response |
| shipments | ✅ | ✅ | ✅ | ✅ | tracking_number AK |
| invoices | ✅ | ✅ | ✅ | ✅ | invoice_number AK |
| return_requests | ✅ | ✅ | ✅ | ✅ | approved_by FK to admin |
| refunds | ✅ | ✅ | ✅ | ✅ | 1:1 with return_requests |
| reviews | ✅ | ✅ | ✅ | ✅ | Variant-level (not product) |
| review_images | ✅ | ✅ | ✅ | ✅ | 1NF: separate from reviews |
| review_replies | ✅ | ✅ | ✅ | ✅ | 1:1 with reviews |

**All 45 tables satisfy 3NF. Most satisfy BCNF.**

---

## Key Normalization Decisions Summary

1. **customers ↔ customer_profiles** (3NF) — auth data vs profile data
2. **products ↔ product_variants** (2NF + 1NF) — no color/size/stock in products
3. **orders.shipping_address_id FK** (3NF) — not embedded address string
4. **brands/suppliers as separate tables** (3NF) — removes transitive deps from products
5. **inventory separate from product_variants** (3NF) — stock is a warehouse concern, not variant concern
6. **product_specifications as EAV** (1NF) — no sparse nullable columns
7. **review_images separate from reviews** (1NF) — no multi-valued image attributes
8. **role_permissions junction** (BCNF) — M:M without embedding arrays
9. **Generated columns** (eliminates derived data anomalies) — available_stock, line_total
10. **order_items.unit_price snapshot** (temporal normalization) — price at time of purchase
