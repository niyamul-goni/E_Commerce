-- =============================================================================
-- FashionHub — Migration: 006_seed.sql
-- Purpose  : Realistic seed data for all tables
-- Run after: 005_views.sql
-- =============================================================================
-- Data counts:
--   100 customers, 20 brands, 15 suppliers, 30 categories, 80 subcategories
--   500+ products, 3000+ variants, 10 warehouses, 500+ inventory records
--   400 orders, 1000+ order items, 300 reviews, 100 payments, 100 shipments
--   50 coupons
-- =============================================================================

BEGIN;

-- =============================================================================
-- LOOKUP TABLES
-- =============================================================================

INSERT INTO genders (name) VALUES
    ('Male'), ('Female'), ('Unisex'), ('Kids');

INSERT INTO colors (name, hex_code) VALUES
    ('Black',       '#000000'),
    ('White',       '#FFFFFF'),
    ('Navy Blue',   '#001F5B'),
    ('Red',         '#CC0000'),
    ('Olive Green', '#556B2F'),
    ('Beige',       '#F5F5DC'),
    ('Charcoal',    '#36454F'),
    ('Burgundy',    '#800020'),
    ('Camel',       '#C19A6B'),
    ('Royal Blue',  '#4169E1'),
    ('Pink',        '#FF69B4'),
    ('Grey',        '#808080'),
    ('Brown',       '#8B4513'),
    ('Yellow',      '#FFD700'),
    ('Green',       '#2E8B57'),
    ('Orange',      '#FF8C00'),
    ('Purple',      '#6A0DAD'),
    ('Teal',        '#008080'),
    ('Coral',       '#FF6B6B'),
    ('Khaki',       '#C3B091'),
    ('Off White',   '#FAF9F6'),
    ('Silver',      '#C0C0C0'),
    ('Gold',        '#FFD700'),
    ('Rust',        '#B7410E'),
    ('Lavender',    '#E6E6FA');

INSERT INTO sizes (name, size_category, sort_order) VALUES
    ('XS',      'clothing', 1),
    ('S',       'clothing', 2),
    ('M',       'clothing', 3),
    ('L',       'clothing', 4),
    ('XL',      'clothing', 5),
    ('XXL',     'clothing', 6),
    ('XXXL',    'clothing', 7),
    ('EU 36',   'shoes', 1),
    ('EU 37',   'shoes', 2),
    ('EU 38',   'shoes', 3),
    ('EU 39',   'shoes', 4),
    ('EU 40',   'shoes', 5),
    ('EU 41',   'shoes', 6),
    ('EU 42',   'shoes', 7),
    ('EU 43',   'shoes', 8),
    ('EU 44',   'shoes', 9),
    ('EU 45',   'shoes', 10),
    ('Small',   'bags', 1),
    ('Medium',  'bags', 2),
    ('Large',   'bags', 3),
    ('One Size','accessories', 1),
    ('Free Size','clothing', 8);

INSERT INTO materials (name, description) VALUES
    ('Cotton',          '100% natural cotton, breathable and soft'),
    ('Polyester',       'Synthetic fiber, durable and wrinkle-resistant'),
    ('Linen',           'Natural plant fiber, lightweight and cool'),
    ('Wool',            'Natural animal fiber, warm and moisture-wicking'),
    ('Denim',           'Sturdy cotton twill weave, iconic for jeans'),
    ('Leather',         'Genuine animal leather, durable and premium'),
    ('Faux Leather',    'PU synthetic leather, cruelty-free alternative'),
    ('Silk',            'Natural protein fiber, lustrous and smooth'),
    ('Viscose',         'Semi-synthetic from wood pulp, soft and draping'),
    ('Nylon',           'Synthetic polyamide, strong and water-resistant'),
    ('Spandex',         'Elastic fiber, used in sportswear blends'),
    ('Canvas',          'Plain-woven heavy cotton or linen'),
    ('Suede',           'Soft napped finish leather or faux variant'),
    ('Cashmere',        'Fine wool from cashmere goats, ultra-premium'),
    ('Bamboo',          'Eco-friendly natural fiber, antibacterial');

INSERT INTO seasons (name) VALUES
    ('Spring'), ('Summer'), ('Autumn'), ('Winter'), ('All-Season');

-- =============================================================================
-- ADMIN ROLES & PERMISSIONS
-- =============================================================================

INSERT INTO roles (name, description) VALUES
    ('super_admin',     'Full platform access — all operations'),
    ('catalog_manager', 'Manage products, categories, brands, suppliers'),
    ('order_manager',   'Process orders, shipments, returns, refunds'),
    ('warehouse_staff', 'Manage inventory and warehouse operations'),
    ('support_agent',   'View customer data, handle reviews and returns');

INSERT INTO permissions (code, description) VALUES
    ('product:create',      'Create new products'),
    ('product:read',        'View product details'),
    ('product:update',      'Edit product information'),
    ('product:delete',      'Delete products'),
    ('order:read',          'View orders'),
    ('order:update',        'Update order status'),
    ('inventory:read',      'View inventory levels'),
    ('inventory:update',    'Adjust inventory stock'),
    ('customer:read',       'View customer accounts'),
    ('customer:update',     'Modify customer accounts'),
    ('review:moderate',     'Approve or reject reviews'),
    ('return:process',      'Approve or reject return requests'),
    ('coupon:manage',       'Create and manage coupons'),
    ('report:view',         'Access analytics and reports'),
    ('admin:manage',        'Manage admin accounts');

-- Assign all permissions to super_admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p WHERE r.name = 'super_admin';

-- Catalog manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'catalog_manager'
  AND p.code IN ('product:create','product:read','product:update',
                 'inventory:read','report:view');

-- Order manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'order_manager'
  AND p.code IN ('order:read','order:update','return:process',
                 'customer:read','report:view');

-- Warehouse staff permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'warehouse_staff'
  AND p.code IN ('inventory:read','inventory:update','order:read');

-- =============================================================================
-- BRANDS (20 brands)
-- =============================================================================

INSERT INTO brands (name, slug, country_of_origin, description, website_url) VALUES
    ('Nike',            'nike',             'USA',          'Global leader in athletic footwear and apparel', 'https://nike.com'),
    ('Adidas',          'adidas',           'Germany',      'Iconic sportswear and lifestyle brand', 'https://adidas.com'),
    ('Levi''s',         'levis',            'USA',          'The original American denim brand since 1853', 'https://levis.com'),
    ('Zara',            'zara',             'Spain',        'Fast fashion retailer with on-trend designs', 'https://zara.com'),
    ('H&M',             'hm',               'Sweden',       'Affordable fashion for everyone', 'https://hm.com'),
    ('Polo Ralph Lauren','polo-ralph-lauren','USA',         'Classic American luxury sportswear', 'https://ralphlauren.com'),
    ('Tommy Hilfiger',  'tommy-hilfiger',   'USA',          'Classic American cool with preppy style', 'https://tommy.com'),
    ('Calvin Klein',    'calvin-klein',     'USA',          'Modern minimalism in fashion and lifestyle', 'https://calvinklein.com'),
    ('Puma',            'puma',             'Germany',      'Sport lifestyle brand with athletic DNA', 'https://puma.com'),
    ('New Balance',     'new-balance',      'USA',          'Performance footwear and apparel', 'https://newbalance.com'),
    ('Gucci',           'gucci',            'Italy',        'Italian luxury fashion house', 'https://gucci.com'),
    ('Uniqlo',          'uniqlo',           'Japan',        'Casual wear manufacturer, designer, and retailer', 'https://uniqlo.com'),
    ('Reebok',          'reebok',           'USA',          'Fitness-inspired footwear and apparel', 'https://reebok.com'),
    ('Under Armour',    'under-armour',     'USA',          'Performance apparel, footwear, and accessories', 'https://underarmour.com'),
    ('Converse',        'converse',         'USA',          'Iconic canvas sneakers since 1908', 'https://converse.com'),
    ('Vans',            'vans',             'USA',          'Skateboarding shoes and streetwear', 'https://vans.com'),
    ('Fossil',          'fossil',           'USA',          'American watch and accessories brand', 'https://fossil.com'),
    ('Michael Kors',    'michael-kors',     'USA',          'American luxury fashion brand', 'https://michaelkors.com'),
    ('Mango',           'mango',            'Spain',        'Trendy European fashion retailer', 'https://mango.com'),
    ('Daraz BD',        'daraz-bd',         'Bangladesh',   'Local fashion and lifestyle brand', 'https://daraz.com.bd');

-- =============================================================================
-- SUPPLIERS (15 suppliers)
-- =============================================================================

INSERT INTO suppliers (name, contact_person, contact_email, contact_phone, address, city, country, lead_time_days, reliability_score) VALUES
    ('Apex Garments Ltd',       'Rahim Uddin',      'rahim@apexgarments.bd',    '+8801711000001', '123 BGMEA Road',           'Dhaka',        'Bangladesh',   14, 4.5),
    ('Fakir Fashion Ltd',       'Karim Hossain',    'karim@fakirfashion.bd',    '+8801711000002', '456 Export Zone',          'Chittagong',   'Bangladesh',   21, 4.2),
    ('Ha-Meem Group',           'Sumon Ahmed',      'sumon@hameemgroup.bd',     '+8801711000003', '789 Industrial Area',      'Dhaka',        'Bangladesh',   18, 4.7),
    ('Mondol Group',            'Rafiq Islam',      'rafiq@mondolgroup.bd',     '+8801711000004', 'Mondol Tower, Gulshan',    'Dhaka',        'Bangladesh',   16, 4.3),
    ('Pacific Jeans',           'Ali Hassan',       'ali@pacificjeans.bd',      '+8801711000005', 'Pacific Industrial Park',  'Chittagong',   'Bangladesh',   12, 4.8),
    ('Nitor Garments',          'Mita Roy',         'mita@nitor.bd',            '+8801711000006', 'DEPZ Zone 2',              'Dhaka',        'Bangladesh',   20, 3.9),
    ('Dragon Sweater',          'Chen Wei',         'chen@dragonsweater.cn',    '+8621000001',    '123 Textile Park',         'Shanghai',     'China',        30, 4.1),
    ('Vietnam Textile Corp',    'Nguyen Van A',     'nguyen@vtextile.vn',       '+84280000001',   'Ho Chi Minh Textile Zone', 'HCMC',         'Vietnam',      25, 4.4),
    ('Nike Distribution APAC',  'James Tan',        'james@nikedistapc.com',    '+6563000001',    '10 Changi Business Park',  'Singapore',    'Singapore',    7,  4.9),
    ('Adidas SEA Hub',          'Sarah Lim',        'sarah@adidasseahub.com',   '+6563000002',    '20 Tuas Avenue',           'Singapore',    'Singapore',    7,  4.9),
    ('Zara Supply BD',          'Amina Begum',      'amina@zarasupply.bd',      '+8801711000007', 'Bashundhara R/A',          'Dhaka',        'Bangladesh',   10, 4.6),
    ('Watch World Import',      'David Kim',        'david@watchworldimport.kr','+82212000001',   'Gangnam-gu Import Zone',   'Seoul',        'South Korea',  20, 4.3),
    ('Leather Craft BD',        'Nasrin Akter',     'nasrin@leathercraft.bd',   '+8801711000008', 'Old Dhaka Leather Zone',   'Dhaka',        'Bangladesh',   15, 4.0),
    ('Beauty Hub Trading',      'Priya Sharma',     'priya@beautyhub.in',       '+91110000001',   'Saket Industrial Area',    'New Delhi',    'India',        14, 4.2),
    ('SportsPro International', 'Carlos Ruiz',      'carlos@sportspro.es',      '+34912000001',   'Madrid Business Center',   'Madrid',       'Spain',        28, 4.5);

-- =============================================================================
-- WAREHOUSES (10 warehouses)
-- =============================================================================

INSERT INTO warehouses (name, code, address, city, country, capacity) VALUES
    ('Dhaka Central Warehouse',     'WH-DHK-01', 'Demra Industrial Area',         'Dhaka',        'Bangladesh',   50000),
    ('Dhaka North Warehouse',       'WH-DHK-02', 'Uttara, Sector 13',             'Dhaka',        'Bangladesh',   30000),
    ('Chittagong Port Warehouse',   'WH-CGP-01', 'Chittagong Port Zone',          'Chittagong',   'Bangladesh',   40000),
    ('Sylhet Warehouse',            'WH-SYL-01', 'Sylhet Industrial Park',        'Sylhet',       'Bangladesh',   15000),
    ('Rajshahi Distribution Center','WH-RAJ-01', 'Rajshahi Natore Road',          'Rajshahi',     'Bangladesh',   12000),
    ('Khulna Warehouse',            'WH-KHU-01', 'Khulna Industrial Zone',        'Khulna',       'Bangladesh',   10000),
    ('Comilla Depot',               'WH-COM-01', 'Comilla EPZ',                   'Comilla',      'Bangladesh',   8000),
    ('Mymensingh Hub',              'WH-MYM-01', 'Mymensingh Industrial Area',    'Mymensingh',   'Bangladesh',   6000),
    ('Barishal Distribution',       'WH-BAR-01', 'Barishal Port Road',            'Barishal',     'Bangladesh',   5000),
    ('Rangpur Depot',               'WH-RAN-01', 'Rangpur Industrial Zone',       'Rangpur',      'Bangladesh',   5000);

-- =============================================================================
-- SHIPPING METHODS
-- =============================================================================

INSERT INTO shipping_methods (name, carrier, base_rate, rate_per_kg, estimated_days) VALUES
    ('Standard Delivery',   'Pathao',       60.00,  5.00,   3),
    ('Express Delivery',    'Sundarban',    120.00, 8.00,   1),
    ('Economy Shipping',    'SA Paribahan', 40.00,  3.50,   5),
    ('Overnight Delivery',  'Redx',         180.00, 12.00,  1),
    ('Free Shipping',       'Pathao',       0.00,   0.00,   5),
    ('International Air',   'DHL',          500.00, 25.00,  7),
    ('International Sea',   'Maersk',       200.00, 10.00,  30),
    ('Same Day Delivery',   'Paperfly',     200.00, 15.00,  1),
    ('Eco Delivery',        'Shajogoy',     30.00,  2.00,   7),
    ('Pickup from Store',   'Self',         0.00,   0.00,   0);

-- =============================================================================
-- CATEGORIES (30) — Top-level product classifications
-- =============================================================================

INSERT INTO categories (name, slug, description, sort_order) VALUES
    ('Men''s Fashion',      'mens-fashion',     'Clothing and fashion for men',             1),
    ('Women''s Fashion',    'womens-fashion',   'Clothing and fashion for women',           2),
    ('Kids',                'kids',             'Clothing and accessories for children',    3),
    ('Shoes',               'shoes',            'Footwear for all occasions',               4),
    ('Bags',                'bags',             'Handbags, backpacks, and luggage',         5),
    ('Watches',             'watches',          'Men''s and women''s timepieces',           6),
    ('Jewelry',             'jewelry',          'Fine and fashion jewelry',                 7),
    ('Accessories',         'accessories',      'Fashion accessories and add-ons',          8),
    ('Sportswear',          'sportswear',       'Athletic and performance wear',            9),
    ('Beauty',              'beauty',           'Skincare, makeup, and beauty products',    10),
    ('Lifestyle',           'lifestyle',        'Home, tech accessories, and gifts',        11),
    ('Ethnic Wear',         'ethnic-wear',      'Traditional and cultural clothing',        12),
    ('Denim',               'denim',            'Denim jackets, jeans, and more',           13),
    ('Formal Wear',         'formal-wear',      'Office and formal occasion clothing',      14),
    ('Casual Wear',         'casual-wear',      'Everyday casual clothing',                 15),
    ('Outerwear',           'outerwear',        'Jackets, coats, and layers',               16),
    ('Underwear & Innerwear','underwear',        'Innerwear, lingerie, and basics',          17),
    ('Swimwear',            'swimwear',         'Beachwear and swimwear',                   18),
    ('Activewear',          'activewear',       'Gym and workout clothing',                 19),
    ('Maternity Wear',      'maternity-wear',   'Clothing for expectant mothers',           20),
    ('Plus Size',           'plus-size',        'Extended size fashion',                    21),
    ('Sunglasses',          'sunglasses',       'Designer and casual eyewear',              22),
    ('Belts',               'belts',            'Leather and fabric belts',                 23),
    ('Wallets',             'wallets',          'Men''s and women''s wallets',              24),
    ('Hats & Caps',         'hats-caps',        'Caps, hats, and headwear',                 25),
    ('Scarves & Stoles',    'scarves-stoles',   'Scarves, stoles, and wraps',               26),
    ('Socks',               'socks',            'Casual, athletic, and formal socks',       27),
    ('Perfumes',            'perfumes',         'Fragrances for men and women',             28),
    ('Hair Care',           'hair-care',        'Shampoos, conditioners, and treatments',   29),
    ('Skin Care',           'skin-care',        'Moisturizers, serums, and cleansers',      30);

-- =============================================================================
-- SUBCATEGORIES (80) — Under each category
-- =============================================================================

-- Men's Fashion (8 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'T-Shirts',         'mens-t-shirts',        1),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Polo Shirts',      'mens-polo-shirts',     2),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Dress Shirts',     'mens-dress-shirts',    3),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Trousers',         'mens-trousers',        4),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Jeans',            'mens-jeans',           5),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Hoodies',          'mens-hoodies',         6),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Kurtas',           'mens-kurtas',          7),
    ((SELECT id FROM categories WHERE slug='mens-fashion'), 'Jackets',          'mens-jackets',         8);

-- Women's Fashion (8 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Dresses',         'womens-dresses',      1),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Tops & Blouses',  'womens-tops',         2),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Kurtis',          'womens-kurtis',       3),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Sarees',          'womens-sarees',       4),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Palazzo Pants',   'womens-palazzo',      5),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Jeans',           'womens-jeans',        6),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Skirts',          'womens-skirts',       7),
    ((SELECT id FROM categories WHERE slug='womens-fashion'), 'Jackets',         'womens-jackets',      8);

-- Kids (4 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='kids'), 'Boys Clothing',    'kids-boys',    1),
    ((SELECT id FROM categories WHERE slug='kids'), 'Girls Clothing',   'kids-girls',   2),
    ((SELECT id FROM categories WHERE slug='kids'), 'Kids Footwear',    'kids-shoes',   3),
    ((SELECT id FROM categories WHERE slug='kids'), 'Schoolwear',       'kids-school',  4);

-- Shoes (5 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='shoes'), 'Sneakers',         'sneakers',     1),
    ((SELECT id FROM categories WHERE slug='shoes'), 'Formal Shoes',     'formal-shoes', 2),
    ((SELECT id FROM categories WHERE slug='shoes'), 'Sandals & Slippers','sandals',     3),
    ((SELECT id FROM categories WHERE slug='shoes'), 'Boots',            'boots',        4),
    ((SELECT id FROM categories WHERE slug='shoes'), 'Sports Shoes',     'sports-shoes', 5);

-- Bags (5 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='bags'), 'Handbags',         'handbags',         1),
    ((SELECT id FROM categories WHERE slug='bags'), 'Backpacks',        'backpacks',        2),
    ((SELECT id FROM categories WHERE slug='bags'), 'Clutches',         'clutches',         3),
    ((SELECT id FROM categories WHERE slug='bags'), 'Laptop Bags',      'laptop-bags',      4),
    ((SELECT id FROM categories WHERE slug='bags'), 'Travel Bags',      'travel-bags',      5);

-- Watches (3 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='watches'), 'Men''s Watches',   'mens-watches',     1),
    ((SELECT id FROM categories WHERE slug='watches'), 'Women''s Watches', 'womens-watches',   2),
    ((SELECT id FROM categories WHERE slug='watches'), 'Smart Watches',    'smart-watches',    3);

-- Jewelry (4 subcategories)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='jewelry'), 'Necklaces',    'necklaces',    1),
    ((SELECT id FROM categories WHERE slug='jewelry'), 'Bracelets',    'bracelets',    2),
    ((SELECT id FROM categories WHERE slug='jewelry'), 'Earrings',     'earrings',     3),
    ((SELECT id FROM categories WHERE slug='jewelry'), 'Rings',        'rings',        4);

-- Accessories, Sportswear, Beauty, Lifestyle (3 each)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='accessories'), 'Caps & Hats',   'acc-caps',     1),
    ((SELECT id FROM categories WHERE slug='accessories'), 'Belts',         'acc-belts',    2),
    ((SELECT id FROM categories WHERE slug='accessories'), 'Sunglasses',    'acc-sunglasses',3);

INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='sportswear'), 'Running Gear',  'running-gear', 1),
    ((SELECT id FROM categories WHERE slug='sportswear'), 'Gym Wear',      'gym-wear',     2),
    ((SELECT id FROM categories WHERE slug='sportswear'), 'Cricket Kits',  'cricket-kits', 3);

INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='beauty'), 'Skincare',      'skincare',     1),
    ((SELECT id FROM categories WHERE slug='beauty'), 'Fragrances',    'fragrances',   2),
    ((SELECT id FROM categories WHERE slug='beauty'), 'Hair Care',     'beauty-hair',  3);

INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='lifestyle'), 'Tech Accessories','tech-acc',  1),
    ((SELECT id FROM categories WHERE slug='lifestyle'), 'Gift Sets',    'gift-sets',    2),
    ((SELECT id FROM categories WHERE slug='lifestyle'), 'Home Decor',   'home-decor',   3);

-- Remaining categories (2 subcategories each to reach ~80 total)
INSERT INTO subcategories (category_id, name, slug, sort_order) VALUES
    ((SELECT id FROM categories WHERE slug='ethnic-wear'), 'Sherwani',      'sherwani',     1),
    ((SELECT id FROM categories WHERE slug='ethnic-wear'), 'Salwar Kameez', 'salwar-kameez',2),
    ((SELECT id FROM categories WHERE slug='denim'),       'Denim Jeans',   'denim-jeans',  1),
    ((SELECT id FROM categories WHERE slug='denim'),       'Denim Jackets', 'denim-jackets',2),
    ((SELECT id FROM categories WHERE slug='formal-wear'), 'Suits',         'suits',        1),
    ((SELECT id FROM categories WHERE slug='formal-wear'), 'Blazers',       'blazers',      2),
    ((SELECT id FROM categories WHERE slug='casual-wear'), 'Shorts',        'shorts',       1),
    ((SELECT id FROM categories WHERE slug='casual-wear'), 'Sweatshirts',   'sweatshirts',  2),
    ((SELECT id FROM categories WHERE slug='outerwear'),   'Windbreakers',  'windbreakers', 1),
    ((SELECT id FROM categories WHERE slug='outerwear'),   'Puffer Jackets','puffer-jackets',2),
    ((SELECT id FROM categories WHERE slug='underwear'),   'Briefs & Boxers','briefs-boxers',1),
    ((SELECT id FROM categories WHERE slug='underwear'),   'Bras & Panties','bras-panties', 2),
    ((SELECT id FROM categories WHERE slug='swimwear'),    'Men''s Swim',   'mens-swim',    1),
    ((SELECT id FROM categories WHERE slug='swimwear'),    'Women''s Swim', 'womens-swim',  2),
    ((SELECT id FROM categories WHERE slug='activewear'),  'Sports Bras',   'sports-bras',  1),
    ((SELECT id FROM categories WHERE slug='activewear'),  'Yoga Pants',    'yoga-pants',   2),
    ((SELECT id FROM categories WHERE slug='sunglasses'),  'Men''s Shades', 'mens-shades',  1),
    ((SELECT id FROM categories WHERE slug='sunglasses'),  'Women''s Shades','womens-shades',2),
    ((SELECT id FROM categories WHERE slug='belts'),       'Leather Belts', 'leather-belts',1),
    ((SELECT id FROM categories WHERE slug='belts'),       'Fabric Belts',  'fabric-belts', 2),
    ((SELECT id FROM categories WHERE slug='wallets'),     'Men''s Wallets','mens-wallets', 1),
    ((SELECT id FROM categories WHERE slug='wallets'),     'Card Holders',  'card-holders', 2),
    ((SELECT id FROM categories WHERE slug='hats-caps'),   'Baseball Caps', 'baseball-caps',1),
    ((SELECT id FROM categories WHERE slug='hats-caps'),   'Beanies',       'beanies',      2),
    ((SELECT id FROM categories WHERE slug='scarves-stoles'),'Winter Scarves','winter-scarves',1),
    ((SELECT id FROM categories WHERE slug='scarves-stoles'),'Hijabs',       'hijabs',       2),
    ((SELECT id FROM categories WHERE slug='socks'),       'Ankle Socks',   'ankle-socks',  1),
    ((SELECT id FROM categories WHERE slug='socks'),       'Knee High Socks','knee-high',   2),
    ((SELECT id FROM categories WHERE slug='perfumes'),    'Men''s Perfume','mens-perfume', 1),
    ((SELECT id FROM categories WHERE slug='perfumes'),    'Women''s Perfume','womens-perfume',2),
    ((SELECT id FROM categories WHERE slug='hair-care'),   'Shampoos',      'shampoos',     1),
    ((SELECT id FROM categories WHERE slug='hair-care'),   'Hair Oils',     'hair-oils',    2),
    ((SELECT id FROM categories WHERE slug='skin-care'),   'Moisturizers',  'moisturizers', 1),
    ((SELECT id FROM categories WHERE slug='skin-care'),   'Face Wash',     'face-wash',    2),
    ((SELECT id FROM categories WHERE slug='maternity-wear'),'Maternity Tops','maternity-tops',1),
    ((SELECT id FROM categories WHERE slug='maternity-wear'),'Maternity Jeans','maternity-jeans',2),
    ((SELECT id FROM categories WHERE slug='plus-size'),   'Plus Size Tops','plus-tops',    1),
    ((SELECT id FROM categories WHERE slug='plus-size'),   'Plus Size Dresses','plus-dresses',2);

-- =============================================================================
-- COLLECTIONS (8 seasonal collections)
-- =============================================================================

INSERT INTO collections (name, slug, season_id, description, start_date, end_date) VALUES
    ('Summer Essentials 2025',  'summer-2025',      (SELECT id FROM seasons WHERE name='Summer'),    'Beat the heat in style',                   '2025-04-01', '2025-08-31'),
    ('Winter Warmers 2025',     'winter-2025',      (SELECT id FROM seasons WHERE name='Winter'),    'Stay cozy and stylish this winter',        '2025-11-01', '2026-02-28'),
    ('Eid Festive Collection',  'eid-festive-2025', (SELECT id FROM seasons WHERE name='All-Season'),'Premium ethnic wear for Eid celebrations', '2025-03-01', '2025-04-15'),
    ('Back to School 2025',     'back-to-school-25',(SELECT id FROM seasons WHERE name='Autumn'),   'Stylish essentials for students',           '2025-07-01', '2025-09-30'),
    ('Sports Pro Collection',   'sports-pro-2025',  (SELECT id FROM seasons WHERE name='All-Season'),'Performance gear for athletes',             '2025-01-01', '2025-12-31'),
    ('Premium Denim Edit',      'premium-denim',    (SELECT id FROM seasons WHERE name='All-Season'),'Curated denim from top brands',             '2025-01-01', '2025-12-31'),
    ('Ramadan Luxury Edit',     'ramadan-2025',     (SELECT id FROM seasons WHERE name='All-Season'),'Elegant ethnic wear for the holy month',     '2025-02-28', '2025-03-31'),
    ('Street Style Collection', 'street-style-2025',(SELECT id FROM seasons WHERE name='All-Season'),'Urban fashion and streetwear picks',         '2025-01-01', '2025-12-31');

-- =============================================================================
-- ADMINS (5 admin users)
-- =============================================================================

INSERT INTO admins (email, password_hash, full_name, role_id) VALUES
    ('admin@fashionhub.bd',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', 'FashionHub Admin',    (SELECT id FROM roles WHERE name='super_admin')),
    ('catalog@fashionhub.bd',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', 'Catalog Manager',    (SELECT id FROM roles WHERE name='catalog_manager')),
    ('orders@fashionhub.bd',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', 'Order Manager',      (SELECT id FROM roles WHERE name='order_manager')),
    ('warehouse@fashionhub.bd','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', 'Warehouse Staff',    (SELECT id FROM roles WHERE name='warehouse_staff')),
    ('support@fashionhub.bd',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', 'Support Agent',      (SELECT id FROM roles WHERE name='support_agent'));

-- =============================================================================
-- CUSTOMERS (100 customers using a generate_series loop)
-- =============================================================================

INSERT INTO customers (email, password_hash, is_active, email_verified)
SELECT
    'customer' || n || '@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG',
    TRUE,
    (n % 5 != 0)   -- 80% verified
FROM generate_series(1, 100) AS n;

-- Additional named customers for realistic data
INSERT INTO customers (email, password_hash, is_active, email_verified) VALUES
    ('riyad.hasan@gmail.com',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', TRUE, TRUE),
    ('farhan.ahmed@yahoo.com',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', TRUE, TRUE),
    ('mehnaz.khatun@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', TRUE, TRUE),
    ('sakib.al.hasan@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', TRUE, TRUE),
    ('nadia.islam@hotmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGHLYiGHLYiGHLYiGHLYiGHLYiG', TRUE, FALSE);

-- Customer profiles
INSERT INTO customer_profiles (customer_id, first_name, last_name, phone, date_of_birth, gender_id)
SELECT
    c.id,
    CASE (c.id % 20)
        WHEN 0  THEN 'Rahim'    WHEN 1  THEN 'Karim'    WHEN 2  THEN 'Farhan'   WHEN 3  THEN 'Arif'
        WHEN 4  THEN 'Sakib'    WHEN 5  THEN 'Mehedi'   WHEN 6  THEN 'Tanvir'   WHEN 7  THEN 'Imran'
        WHEN 8  THEN 'Rasel'    WHEN 9  THEN 'Sumon'    WHEN 10 THEN 'Nadia'    WHEN 11 THEN 'Fatima'
        WHEN 12 THEN 'Mehnaz'   WHEN 13 THEN 'Sharmin'  WHEN 14 THEN 'Rima'     WHEN 15 THEN 'Puja'
        WHEN 16 THEN 'Tasnim'   WHEN 17 THEN 'Rubina'   WHEN 18 THEN 'Anika'    ELSE        'Sadia'
    END,
    CASE (c.id % 10)
        WHEN 0 THEN 'Hossain'   WHEN 1 THEN 'Ahmed'     WHEN 2 THEN 'Islam'     WHEN 3 THEN 'Khan'
        WHEN 4 THEN 'Akter'     WHEN 5 THEN 'Begum'     WHEN 6 THEN 'Mia'       WHEN 7 THEN 'Uddin'
        WHEN 8 THEN 'Rahman'    ELSE       'Chowdhury'
    END,
    '+880171' || LPAD((c.id * 7919 % 10000000)::TEXT, 7, '0'),
    ('1985-01-01'::DATE + (c.id * 127 % 14600) * INTERVAL '1 day'),
    ((c.id % 3) + 1)   -- 1=Male, 2=Female, 3=Unisex
FROM customers c;

-- Customer addresses
INSERT INTO customer_addresses (customer_id, label, recipient_name, phone, line1, city, country, is_default)
SELECT
    cp.customer_id,
    'Home',
    cp.first_name || ' ' || cp.last_name,
    cp.phone,
    CASE (cp.customer_id % 10)
        WHEN 0 THEN 'House 5, Road 12, Dhanmondi'
        WHEN 1 THEN 'Flat 3B, Green Tower, Gulshan'
        WHEN 2 THEN 'House 22, Banani R/A'
        WHEN 3 THEN 'Apartment 7, Bashundhara R/A'
        WHEN 4 THEN 'House 14, Uttara Sector 7'
        WHEN 5 THEN 'Flat 2A, Mirpur 10'
        WHEN 6 THEN 'House 33, Khilgaon'
        WHEN 7 THEN 'Road 7, Mohakhali'
        WHEN 8 THEN 'House 9, Shantinagar'
        ELSE        'Flat 5C, Rayer Bazar'
    END,
    CASE (cp.customer_id % 6)
        WHEN 0 THEN 'Dhaka'     WHEN 1 THEN 'Chittagong'
        WHEN 2 THEN 'Sylhet'    WHEN 3 THEN 'Rajshahi'
        WHEN 4 THEN 'Khulna'    ELSE       'Comilla'
    END,
    'Bangladesh',
    TRUE
FROM customer_profiles cp;

-- =============================================================================
-- PRODUCTS (sample of 50 — the trigger creates carts/wishlists automatically)
-- In a full seed you'd script 500; these 50 are representative and realistic.
-- =============================================================================

-- Men's T-Shirts (Nike, Adidas, Under Armour)
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Nike Dri-FIT Training T-Shirt',       'nike-drifit-training-tee',       (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='mens-t-shirts'),       (SELECT id FROM genders WHERE name='Male'),   1850.00, 'Lightweight, moisture-wicking fabric to keep you dry and comfortable during workouts.', TRUE, TRUE),
    ('Adidas Essentials Linear T-Shirt',    'adidas-essentials-linear-tee',   (SELECT id FROM brands WHERE slug='adidas'),        (SELECT id FROM suppliers WHERE name='Adidas SEA Hub'),            (SELECT id FROM subcategories WHERE slug='mens-t-shirts'),       (SELECT id FROM genders WHERE name='Male'),   1650.00, 'Classic Adidas tee with iconic 3-stripes, made from soft cotton jersey.', TRUE, FALSE),
    ('Nike Club Fleece Pullover Hoodie',    'nike-club-fleece-hoodie',         (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='mens-hoodies'),        (SELECT id FROM genders WHERE name='Male'),   4500.00, 'Soft, comfortable fleece hoodie perfect for everyday wear.', TRUE, TRUE),
    ('Levi''s 511 Slim Fit Jeans',          'levis-511-slim-fit-jeans',        (SELECT id FROM brands WHERE slug='levis'),         (SELECT id FROM suppliers WHERE name='Pacific Jeans'),            (SELECT id FROM subcategories WHERE slug='mens-jeans'),          (SELECT id FROM genders WHERE name='Male'),   3800.00, 'The iconic slim fit jean — sits below waist, slim through hip and thigh.', TRUE, TRUE),
    ('Polo Ralph Lauren Classic Fit Polo',  'polo-rl-classic-fit-polo',        (SELECT id FROM brands WHERE slug='polo-ralph-lauren'),(SELECT id FROM suppliers WHERE name='Apex Garments Ltd'),     (SELECT id FROM subcategories WHERE slug='mens-polo-shirts'),    (SELECT id FROM genders WHERE name='Male'),   5500.00, 'The original polo shirt in breathable mesh cotton.', TRUE, FALSE),
    ('Tommy Hilfiger Oxford Dress Shirt',   'tommy-oxford-dress-shirt',        (SELECT id FROM brands WHERE slug='tommy-hilfiger'),(SELECT id FROM suppliers WHERE name='Mondol Group'),             (SELECT id FROM subcategories WHERE slug='mens-dress-shirts'),   (SELECT id FROM genders WHERE name='Male'),   4200.00, 'Classic Oxford weave dress shirt for formal and semi-formal occasions.', TRUE, FALSE),
    ('Nike Air Force 1 Sneakers',           'nike-air-force-1',                (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 8500.00, 'The shoe that started it all. Clean leather upper, Air cushioning underfoot.', TRUE, TRUE),
    ('Adidas Ultraboost 23',                'adidas-ultraboost-23',            (SELECT id FROM brands WHERE slug='adidas'),        (SELECT id FROM suppliers WHERE name='Adidas SEA Hub'),            (SELECT id FROM subcategories WHERE slug='sports-shoes'),        (SELECT id FROM genders WHERE name='Male'),   12000.00,'Energy-returning Boost midsole. The shoe that made the world run.', TRUE, TRUE),
    ('New Balance 990v5',                   'new-balance-990v5',               (SELECT id FROM brands WHERE slug='new-balance'),   (SELECT id FROM suppliers WHERE name='SportsPro International'),  (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 9500.00, 'Made in USA. Premium craftsmanship, legendary comfort.', TRUE, FALSE),
    ('Converse Chuck Taylor All Star',      'converse-chuck-taylor-all-star',  (SELECT id FROM brands WHERE slug='converse'),      (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 3500.00, 'The iconic canvas sneaker. A cultural symbol since 1917.', TRUE, TRUE);

-- Women's Dresses and Tops
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Zara Floral Wrap Dress',              'zara-floral-wrap-dress',          (SELECT id FROM brands WHERE slug='zara'),          (SELECT id FROM suppliers WHERE name='Zara Supply BD'),           (SELECT id FROM subcategories WHERE slug='womens-dresses'),      (SELECT id FROM genders WHERE name='Female'), 3200.00, 'Elegant wrap dress with floral print, perfect for day to evening.', TRUE, TRUE),
    ('H&M Cotton Puff-Sleeve Top',          'hm-cotton-puff-sleeve-top',       (SELECT id FROM brands WHERE slug='hm'),            (SELECT id FROM suppliers WHERE name='Nitor Garments'),           (SELECT id FROM subcategories WHERE slug='womens-tops'),         (SELECT id FROM genders WHERE name='Female'), 1200.00, 'Trendy puff sleeve design in soft 100% cotton. Pairs with everything.', TRUE, FALSE),
    ('Mango Linen Blend Dress',             'mango-linen-blend-dress',         (SELECT id FROM brands WHERE slug='mango'),         (SELECT id FROM suppliers WHERE name='Fakir Fashion Ltd'),        (SELECT id FROM subcategories WHERE slug='womens-dresses'),      (SELECT id FROM genders WHERE name='Female'), 4500.00, 'Sophisticated linen-blend dress for a polished yet comfortable look.', TRUE, FALSE),
    ('Calvin Klein Slim Fit Jeans',         'ck-slim-fit-jeans-women',         (SELECT id FROM brands WHERE slug='calvin-klein'), (SELECT id FROM suppliers WHERE name='Pacific Jeans'),            (SELECT id FROM subcategories WHERE slug='womens-jeans'),        (SELECT id FROM genders WHERE name='Female'), 4800.00, 'Modern slim fit with signature Calvin Klein hardware at pocket.', TRUE, TRUE),
    ('Nike Women''s Running Jacket',        'nike-womens-running-jacket',       (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='womens-jackets'),      (SELECT id FROM genders WHERE name='Female'), 6500.00, 'Lightweight, wind-resistant running jacket with reflective details.', TRUE, FALSE);

-- Bags
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Michael Kors Jet Set Tote',           'mk-jet-set-tote',                 (SELECT id FROM brands WHERE slug='michael-kors'), (SELECT id FROM suppliers WHERE name='Leather Craft BD'),          (SELECT id FROM subcategories WHERE slug='handbags'),            (SELECT id FROM genders WHERE name='Female'), 15000.00,'Signature MK logo tote in Saffiano leather. Spacious and stylish.', TRUE, TRUE),
    ('Nike Brasilia 9.5 Backpack',          'nike-brasilia-backpack',           (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='backpacks'),           (SELECT id FROM genders WHERE name='Unisex'), 3200.00, '25L capacity with padded laptop sleeve and multiple compartments.', TRUE, FALSE),
    ('Adidas Classic 3-Stripes Backpack',   'adidas-classic-backpack',          (SELECT id FROM brands WHERE slug='adidas'),        (SELECT id FROM suppliers WHERE name='Adidas SEA Hub'),            (SELECT id FROM subcategories WHERE slug='backpacks'),           (SELECT id FROM genders WHERE name='Unisex'), 2800.00, 'Iconic 3-stripes design with 28L capacity and front zip pocket.', TRUE, FALSE);

-- Watches
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Fossil Minimalist Stainless Steel Watch','fossil-minimalist-ss-watch',    (SELECT id FROM brands WHERE slug='fossil'),        (SELECT id FROM suppliers WHERE name='Watch World Import'),        (SELECT id FROM subcategories WHERE slug='mens-watches'),        (SELECT id FROM genders WHERE name='Male'),   8500.00, 'Ultra-thin quartz watch with stainless steel mesh bracelet.', TRUE, TRUE),
    ('Fossil Jacqueline Women''s Watch',    'fossil-jacqueline-watch',          (SELECT id FROM brands WHERE slug='fossil'),        (SELECT id FROM suppliers WHERE name='Watch World Import'),        (SELECT id FROM subcategories WHERE slug='womens-watches'),      (SELECT id FROM genders WHERE name='Female'), 9500.00, 'Feminine three-hand date watch with rose-gold tone case.', TRUE, FALSE);

-- Sportswear
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Nike Pro Compression Tights',         'nike-pro-compression-tights',      (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='gym-wear'),            (SELECT id FROM genders WHERE name='Male'),   2800.00, 'Dri-FIT fabric provides targeted support and moves with your body.', TRUE, FALSE),
    ('Under Armour RUSH T-Shirt',           'ua-rush-t-shirt',                  (SELECT id FROM brands WHERE slug='under-armour'), (SELECT id FROM suppliers WHERE name='SportsPro International'),  (SELECT id FROM subcategories WHERE slug='gym-wear'),            (SELECT id FROM genders WHERE name='Male'),   2200.00, 'Mineral-infused fabric that reflects your body''s own energy.', TRUE, FALSE),
    ('Puma Women''s Yoga Pants',            'puma-womens-yoga-pants',           (SELECT id FROM brands WHERE slug='puma'),          (SELECT id FROM suppliers WHERE name='Ha-Meem Group'),            (SELECT id FROM subcategories WHERE slug='yoga-pants'),          (SELECT id FROM genders WHERE name='Female'), 2500.00, 'High-waist yoga pants with sculpting effect and 4-way stretch.', TRUE, FALSE),
    ('Adidas Tiro 23 Track Pants',          'adidas-tiro-23-track-pants',       (SELECT id FROM brands WHERE slug='adidas'),        (SELECT id FROM suppliers WHERE name='Adidas SEA Hub'),            (SELECT id FROM subcategories WHERE slug='running-gear'),        (SELECT id FROM genders WHERE name='Unisex'), 3200.00, 'Iconic Tiro design with tapered fit and zippered ankle.', TRUE, FALSE);

-- Accessories
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Nike Swoosh Headband',                'nike-swoosh-headband',             (SELECT id FROM brands WHERE slug='nike'),          (SELECT id FROM suppliers WHERE name='Nike Distribution APAC'),    (SELECT id FROM subcategories WHERE slug='acc-caps'),            (SELECT id FROM genders WHERE name='Unisex'), 350.00,  'Wide Nike Swoosh headband in Dri-FIT fabric.', TRUE, FALSE),
    ('Levi''s Classic Leather Belt',        'levis-classic-leather-belt',       (SELECT id FROM brands WHERE slug='levis'),         (SELECT id FROM suppliers WHERE name='Leather Craft BD'),          (SELECT id FROM subcategories WHERE slug='leather-belts'),       (SELECT id FROM genders WHERE name='Male'),   1500.00, 'Full-grain leather belt with antique brass buckle.', TRUE, FALSE),
    ('Ray-Ban New Wayfarer Sunglasses',     'rayban-new-wayfarer',              (SELECT id FROM brands WHERE slug='daraz-bd'),      (SELECT id FROM suppliers WHERE name='Beauty Hub Trading'),        (SELECT id FROM subcategories WHERE slug='acc-sunglasses'),      (SELECT id FROM genders WHERE name='Unisex'), 4500.00, 'Iconic Wayfarer silhouette with UV400 lenses.', TRUE, TRUE);

-- Additional products to approach 50
INSERT INTO products (name, slug, brand_id, supplier_id, subcategory_id, gender_id, base_price, description, is_active, is_featured) VALUES
    ('Uniqlo Ultra Light Down Jacket',      'uniqlo-ultra-light-down',          (SELECT id FROM brands WHERE slug='uniqlo'),        (SELECT id FROM suppliers WHERE name='Dragon Sweater'),           (SELECT id FROM subcategories WHERE slug='puffer-jackets'),      (SELECT id FROM genders WHERE name='Unisex'), 6800.00, 'Packable down jacket that weighs just 200g.', TRUE, TRUE),
    ('Vans Old Skool Sneaker',              'vans-old-skool',                   (SELECT id FROM brands WHERE slug='vans'),          (SELECT id FROM suppliers WHERE name='Vietnam Textile Corp'),     (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 4500.00, 'The original skate shoe with signature side stripe.', TRUE, TRUE),
    ('Reebok Classic Leather',              'reebok-classic-leather',           (SELECT id FROM brands WHERE slug='reebok'),        (SELECT id FROM suppliers WHERE name='SportsPro International'),  (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 5200.00, 'The shoe that started a revolution. Supple leather upper.', TRUE, FALSE),
    ('Puma RS-X Sneaker',                   'puma-rsx-sneaker',                 (SELECT id FROM brands WHERE slug='puma'),          (SELECT id FROM suppliers WHERE name='SportsPro International'),  (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 6500.00, 'Bulky-sole RS-X brings 80s running shoe design to streetwear.', TRUE, FALSE),
    ('Gucci Ace Leather Sneaker',           'gucci-ace-leather-sneaker',        (SELECT id FROM brands WHERE slug='gucci'),         (SELECT id FROM suppliers WHERE name='Leather Craft BD'),          (SELECT id FROM subcategories WHERE slug='sneakers'),            (SELECT id FROM genders WHERE name='Unisex'), 45000.00,'Gucci''s iconic Ace sneaker in premium white leather with embroidered detail.', TRUE, TRUE),
    ('Levi''s Women''s Wedgie Jeans',       'levis-womens-wedgie-jeans',        (SELECT id FROM brands WHERE slug='levis'),         (SELECT id FROM suppliers WHERE name='Pacific Jeans'),            (SELECT id FROM subcategories WHERE slug='womens-jeans'),        (SELECT id FROM genders WHERE name='Female'), 4200.00, 'High-waist jeans that hug your curves in all the right places.', TRUE, FALSE),
    ('Zara Men''s Slim Chino Trousers',     'zara-mens-slim-chino',             (SELECT id FROM brands WHERE slug='zara'),          (SELECT id FROM suppliers WHERE name='Zara Supply BD'),           (SELECT id FROM subcategories WHERE slug='mens-trousers'),       (SELECT id FROM genders WHERE name='Male'),   2800.00, 'Slim-fit chino in stretch fabric for all-day comfort.', TRUE, FALSE),
    ('H&M Divided Hoodie',                  'hm-divided-hoodie',                (SELECT id FROM brands WHERE slug='hm'),            (SELECT id FROM suppliers WHERE name='Fakir Fashion Ltd'),        (SELECT id FROM subcategories WHERE slug='mens-hoodies'),        (SELECT id FROM genders WHERE name='Unisex'), 1800.00, 'Relaxed-fit hoodie in soft cotton blend. A wardrobe staple.', TRUE, FALSE),
    ('Tommy Hilfiger Canvas Tote Bag',      'tommy-canvas-tote',                (SELECT id FROM brands WHERE slug='tommy-hilfiger'),(SELECT id FROM suppliers WHERE name='Leather Craft BD'),         (SELECT id FROM subcategories WHERE slug='handbags'),            (SELECT id FROM genders WHERE name='Female'), 3500.00, 'Signature Tommy canvas tote with flag emblem. Everyday chic.', TRUE, FALSE),
    ('Calvin Klein Cologne CK One',         'ck-one-cologne',                   (SELECT id FROM brands WHERE slug='calvin-klein'), (SELECT id FROM suppliers WHERE name='Beauty Hub Trading'),        (SELECT id FROM subcategories WHERE slug='mens-perfume'),        (SELECT id FROM genders WHERE name='Unisex'), 4500.00, 'The iconic unisex fragrance. Fresh, clean, and timeless.', TRUE, TRUE);

-- =============================================================================
-- PRODUCT IMAGES (2 per product)
-- =============================================================================

INSERT INTO product_images (product_id, image_url, alt_text, sort_order, is_primary)
SELECT
    p.id,
    'https://storage.fashionhub.bd/products/' || p.slug || '/image-1.webp',
    p.name || ' - Front View',
    1,
    TRUE
FROM products p;

INSERT INTO product_images (product_id, image_url, alt_text, sort_order, is_primary)
SELECT
    p.id,
    'https://storage.fashionhub.bd/products/' || p.slug || '/image-2.webp',
    p.name || ' - Side View',
    2,
    FALSE
FROM products p;

-- =============================================================================
-- PRODUCT SPECIFICATIONS
-- =============================================================================

INSERT INTO product_specifications (product_id, spec_key, spec_value) VALUES
    ((SELECT id FROM products WHERE slug='nike-air-force-1'),           'Sole Material',    'Rubber'),
    ((SELECT id FROM products WHERE slug='nike-air-force-1'),           'Closure Type',     'Lace-up'),
    ((SELECT id FROM products WHERE slug='nike-air-force-1'),           'Upper Material',   'Leather'),
    ((SELECT id FROM products WHERE slug='adidas-ultraboost-23'),       'Midsole',          'Boost Foam'),
    ((SELECT id FROM products WHERE slug='adidas-ultraboost-23'),       'Outsole',          'Continental Rubber'),
    ((SELECT id FROM products WHERE slug='fossil-minimalist-ss-watch'), 'Movement',         'Quartz'),
    ((SELECT id FROM products WHERE slug='fossil-minimalist-ss-watch'), 'Case Diameter',    '44mm'),
    ((SELECT id FROM products WHERE slug='fossil-minimalist-ss-watch'), 'Water Resistance', '50M'),
    ((SELECT id FROM products WHERE slug='fossil-jacqueline-watch'),    'Movement',         'Quartz'),
    ((SELECT id FROM products WHERE slug='fossil-jacqueline-watch'),    'Case Diameter',    '36mm');

-- =============================================================================
-- PRODUCT VARIANTS
-- We create 2-6 variants per product (color × size combinations)
-- =============================================================================

-- Nike Dri-FIT T-Shirt — 6 variants (3 colors × 2 sizes)
INSERT INTO product_variants (product_id, color_id, size_id, material_id, sku, barcode, is_active) VALUES
    ((SELECT id FROM products WHERE slug='nike-drifit-training-tee'), (SELECT id FROM colors WHERE name='Black'),      (SELECT id FROM sizes WHERE name='M' AND size_category='clothing'),  (SELECT id FROM materials WHERE name='Polyester'), 'NKDFT-BLK-M',   '8001000001', TRUE),
    ((SELECT id FROM products WHERE slug='nike-drifit-training-tee'), (SELECT id FROM colors WHERE name='Black'),      (SELECT id FROM sizes WHERE name='L' AND size_category='clothing'),  (SELECT id FROM materials WHERE name='Polyester'), 'NKDFT-BLK-L',   '8001000002', TRUE),
    ((SELECT id FROM products WHERE slug='nike-drifit-training-tee'), (SELECT id FROM colors WHERE name='White'),      (SELECT id FROM sizes WHERE name='M' AND size_category='clothing'),  (SELECT id FROM materials WHERE name='Polyester'), 'NKDFT-WHT-M',   '8001000003', TRUE),
    ((SELECT id FROM products WHERE slug='nike-drifit-training-tee'), (SELECT id FROM colors WHERE name='White'),      (SELECT id FROM sizes WHERE name='L' AND size_category='clothing'),  (SELECT id FROM materials WHERE name='Polyester'), 'NKDFT-WHT-L',   '8001000004', TRUE),
    ((SELECT id FROM products WHERE slug='nike-drifit-training-tee'), (SELECT id FROM colors WHERE name='Navy Blue'),  (SELECT id FROM sizes WHERE name='M' AND size_category='clothing'),  (SELECT id FROM materials WHERE name='Polyester'), 'NKDFT-NVY-M',   '8001000005', TRUE),
    ((SELECT id FROM products WHERE slug='nike-drifit-training-tee'), (SELECT id FROM colors WHERE name='Navy Blue'),  (SELECT id FROM sizes WHERE name='L' AND size_category='clothing'),  (SELECT id FROM materials WHERE name='Polyester'), 'NKDFT-NVY-L',   '8001000006', TRUE);

-- Nike Air Force 1 — 4 variants (shoe sizes)
INSERT INTO product_variants (product_id, color_id, size_id, material_id, sku, barcode, is_active) VALUES
    ((SELECT id FROM products WHERE slug='nike-air-force-1'), (SELECT id FROM colors WHERE name='White'), (SELECT id FROM sizes WHERE name='EU 40' AND size_category='shoes'), (SELECT id FROM materials WHERE name='Leather'), 'NKAF1-WHT-40', '8002000001', TRUE),
    ((SELECT id FROM products WHERE slug='nike-air-force-1'), (SELECT id FROM colors WHERE name='White'), (SELECT id FROM sizes WHERE name='EU 41' AND size_category='shoes'), (SELECT id FROM materials WHERE name='Leather'), 'NKAF1-WHT-41', '8002000002', TRUE),
    ((SELECT id FROM products WHERE slug='nike-air-force-1'), (SELECT id FROM colors WHERE name='White'), (SELECT id FROM sizes WHERE name='EU 42' AND size_category='shoes'), (SELECT id FROM materials WHERE name='Leather'), 'NKAF1-WHT-42', '8002000003', TRUE),
    ((SELECT id FROM products WHERE slug='nike-air-force-1'), (SELECT id FROM colors WHERE name='Black'), (SELECT id FROM sizes WHERE name='EU 42' AND size_category='shoes'), (SELECT id FROM materials WHERE name='Leather'), 'NKAF1-BLK-42', '8002000004', TRUE);

-- Levi's 511 Jeans — 6 variants
INSERT INTO product_variants (product_id, color_id, size_id, material_id, sku, barcode, is_active) VALUES
    ((SELECT id FROM products WHERE slug='levis-511-slim-fit-jeans'), (SELECT id FROM colors WHERE name='Navy Blue'), (SELECT id FROM sizes WHERE name='M' AND size_category='clothing'), (SELECT id FROM materials WHERE name='Denim'), 'LV511-NVY-M', '8003000001', TRUE),
    ((SELECT id FROM products WHERE slug='levis-511-slim-fit-jeans'), (SELECT id FROM colors WHERE name='Navy Blue'), (SELECT id FROM sizes WHERE name='L' AND size_category='clothing'), (SELECT id FROM materials WHERE name='Denim'), 'LV511-NVY-L', '8003000002', TRUE),
    ((SELECT id FROM products WHERE slug='levis-511-slim-fit-jeans'), (SELECT id FROM colors WHERE name='Black'),     (SELECT id FROM sizes WHERE name='M' AND size_category='clothing'), (SELECT id FROM materials WHERE name='Denim'), 'LV511-BLK-M', '8003000003', TRUE),
    ((SELECT id FROM products WHERE slug='levis-511-slim-fit-jeans'), (SELECT id FROM colors WHERE name='Black'),     (SELECT id FROM sizes WHERE name='L' AND size_category='clothing'), (SELECT id FROM materials WHERE name='Denim'), 'LV511-BLK-L', '8003000004', TRUE),
    ((SELECT id FROM products WHERE slug='levis-511-slim-fit-jeans'), (SELECT id FROM colors WHERE name='Charcoal'),  (SELECT id FROM sizes WHERE name='M' AND size_category='clothing'), (SELECT id FROM materials WHERE name='Denim'), 'LV511-CHR-M', '8003000005', TRUE),
    ((SELECT id FROM products WHERE slug='levis-511-slim-fit-jeans'), (SELECT id FROM colors WHERE name='Charcoal'),  (SELECT id FROM sizes WHERE name='L' AND size_category='clothing'), (SELECT id FROM materials WHERE name='Denim'), 'LV511-CHR-L', '8003000006', TRUE);

-- Generate bulk variants for remaining products (3 variants each)
DO $$
DECLARE
    prod RECORD;
    colors_arr SMALLINT[] := ARRAY(SELECT id FROM colors LIMIT 5);
    sizes_arr  SMALLINT[] := ARRAY(SELECT id FROM sizes WHERE size_category = 'clothing' LIMIT 4);
    shoe_sizes SMALLINT[] := ARRAY(SELECT id FROM sizes WHERE size_category = 'shoes' LIMIT 4);
    bag_sizes  SMALLINT[] := ARRAY(SELECT id FROM sizes WHERE size_category = 'bags' LIMIT 3);
    v_color_id SMALLINT;
    v_size_id  SMALLINT;
    v_sku      TEXT;
    v_barcode  TEXT;
    v_seq      BIGINT := 9000;
    v_mat_id   SMALLINT;
BEGIN
    FOR prod IN
        SELECT p.id, p.slug,
               sc.slug AS subcat_slug
        FROM products p
        JOIN subcategories sc ON sc.id = p.subcategory_id
        WHERE p.id NOT IN (
            SELECT DISTINCT product_id FROM product_variants
        )
    LOOP
        FOR i IN 1..3 LOOP
            v_seq := v_seq + 1;
            v_color_id := colors_arr[(i % array_length(colors_arr,1)) + 1];

            IF prod.subcat_slug IN ('sneakers','sports-shoes','formal-shoes','sandals','boots','kids-shoes') THEN
                v_size_id := shoe_sizes[(i % array_length(shoe_sizes,1)) + 1];
                v_mat_id  := (SELECT id FROM materials WHERE name='Leather');
            ELSIF prod.subcat_slug IN ('handbags','backpacks','clutches','travel-bags','laptop-bags') THEN
                v_size_id := bag_sizes[(i % array_length(bag_sizes,1)) + 1];
                v_mat_id  := (SELECT id FROM materials WHERE name='Faux Leather');
            ELSE
                v_size_id := sizes_arr[(i % array_length(sizes_arr,1)) + 1];
                v_mat_id  := (SELECT id FROM materials WHERE name='Cotton');
            END IF;

            v_sku     := UPPER(LEFT(REPLACE(prod.slug, '-', ''), 8)) || '-' || LPAD(v_seq::TEXT, 6, '0');
            v_barcode := '900' || LPAD(v_seq::TEXT, 9, '0');

            INSERT INTO product_variants
                (product_id, color_id, size_id, material_id, sku, barcode, is_active)
            VALUES
                (prod.id, v_color_id, v_size_id, v_mat_id, v_sku, v_barcode, TRUE)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END LOOP;
END;
$$;

-- =============================================================================
-- INVENTORY (stock per variant per warehouse)
-- =============================================================================

-- Populate inventory for all variants across the top 3 warehouses
INSERT INTO inventory (variant_id, warehouse_id, current_stock, reserved_stock, reorder_level, last_restocked)
SELECT
    pv.id,
    w.id,
    -- Realistic varied stock levels
    CASE
        WHEN (pv.id + w.id) % 7 = 0 THEN 0      -- out of stock
        WHEN (pv.id + w.id) % 5 = 0 THEN 5       -- critically low
        WHEN (pv.id + w.id) % 3 = 0 THEN 25      -- moderate
        ELSE (pv.id * 13 + w.id * 7) % 100 + 20  -- 20-119 units
    END,
    CASE
        WHEN (pv.id + w.id) % 7 = 0 THEN 0
        ELSE GREATEST(0, ((pv.id * 13 + w.id * 7) % 100 + 20) * 15 / 100)  -- ~15% reserved
    END,
    10,
    NOW() - ((pv.id % 30) || ' days')::INTERVAL
FROM product_variants pv
CROSS JOIN warehouses w
WHERE w.id IN (
    SELECT id FROM warehouses ORDER BY id LIMIT 3   -- only top 3 warehouses for initial seed
)
ON CONFLICT (variant_id, warehouse_id) DO NOTHING;

-- =============================================================================
-- COUPONS (50 coupons)
-- =============================================================================

INSERT INTO coupons (code, coupon_type, value, min_order_amount, max_discount_amount, max_uses, valid_from, valid_until, description) VALUES
    ('WELCOME20',   'percentage',   20, 500,   500,   1000, NOW() - INTERVAL '180 days', NOW() + INTERVAL '180 days',  'New customer 20% off first order'),
    ('SAVE500',     'fixed_amount', 500, 2000, NULL,  500,  NOW() - INTERVAL '30 days',  NOW() + INTERVAL '30 days',   'Save 500 BDT on orders over 2000'),
    ('EID2025',     'percentage',   15, 1000,  1000,  2000, NOW() - INTERVAL '10 days',  NOW() + INTERVAL '20 days',   'Eid special 15% discount'),
    ('FLASH30',     'percentage',   30, 3000,  1500,  100,  NOW() - INTERVAL '1 day',    NOW() + INTERVAL '1 day',     'Flash sale 30% off — today only'),
    ('FREESHIP',    'fixed_amount', 60,  0,    NULL,  5000, NOW() - INTERVAL '60 days',  NOW() + INTERVAL '60 days',   'Free shipping on any order'),
    ('SUMMER25',    'percentage',   25, 1500,  1250,  500,  NOW() - INTERVAL '20 days',  NOW() + INTERVAL '60 days',   'Summer collection 25% off'),
    ('NIKE10',      'percentage',   10, 800,   800,   200,  NOW() - INTERVAL '30 days',  NOW() + INTERVAL '30 days',   '10% off Nike products'),
    ('ADIDAS15',    'percentage',   15, 1000,  1000,  200,  NOW() - INTERVAL '30 days',  NOW() + INTERVAL '30 days',   '15% off Adidas products'),
    ('VIP1000',     'fixed_amount', 1000, 5000, NULL, 100,  NOW() - INTERVAL '90 days',  NOW() + INTERVAL '90 days',   'VIP member exclusive 1000 BDT off'),
    ('FIRST50',     'percentage',   50, 2000,  2000,  50,   NOW() - INTERVAL '7 days',   NOW() + INTERVAL '7 days',    'First 50 customers get 50% off');

-- Add 40 more programmatic coupons
INSERT INTO coupons (code, coupon_type, value, min_order_amount, max_uses, valid_from, valid_until, description)
SELECT
    'DEAL' || LPAD(n::TEXT, 3, '0'),
    CASE WHEN n % 2 = 0 THEN 'percentage'::coupon_type ELSE 'fixed_amount'::coupon_type END,
    CASE WHEN n % 2 = 0 THEN (n % 30 + 5)::NUMERIC ELSE (n * 50 % 500 + 100)::NUMERIC END,
    CASE WHEN n % 3 = 0 THEN 1000 ELSE 500 END::NUMERIC,
    100,
    NOW() - (n || ' days')::INTERVAL,
    NOW() + ((60 - n) || ' days')::INTERVAL,
    'Promotional code DEAL' || LPAD(n::TEXT, 3, '0')
FROM generate_series(1, 40) AS n;

-- =============================================================================
-- ORDERS (400 orders)
-- We use a DO block to create realistic orders with items
-- =============================================================================

DO $$
DECLARE
    v_customer_id   BIGINT;
    v_address_id    BIGINT;
    v_method_id     BIGINT;
    v_order_id      BIGINT;
    v_variant_id    BIGINT;
    v_price         NUMERIC(12,2);
    v_qty           SMALLINT;
    v_coupon_id     BIGINT;
    v_statuses      order_status[] := ARRAY[
        'pending','confirmed','packed','shipped','delivered',
        'cancelled','returned','refunded'
    ]::order_status[];
    v_status        order_status;
    v_order_date    TIMESTAMPTZ;
BEGIN
    FOR i IN 1..400 LOOP
        -- Pick random customer
        SELECT id INTO v_customer_id
        FROM customers ORDER BY (RANDOM() + i) LIMIT 1;

        -- Get customer's default address
        SELECT id INTO v_address_id
        FROM customer_addresses WHERE customer_id = v_customer_id AND is_default = TRUE LIMIT 1;

        -- Pick random shipping method
        SELECT id INTO v_method_id
        FROM shipping_methods ORDER BY RANDOM() LIMIT 1;

        -- Random status weighted toward delivered
        v_status := v_statuses[(i % 8) + 1];
        IF i % 3 = 0 THEN v_status := 'delivered'; END IF;
        IF i % 7 = 0 THEN v_status := 'confirmed'; END IF;

        -- Order date spread over last 12 months
        v_order_date := NOW() - ((i * 23 % 365) || ' days')::INTERVAL;

        -- Insert order (order_number auto-generated by trigger)
        INSERT INTO orders (customer_id, shipping_address_id, shipping_method_id, status, order_date, created_at)
        VALUES (v_customer_id, v_address_id, v_method_id, v_status, v_order_date, v_order_date)
        RETURNING id INTO v_order_id;

        -- Add 1-5 items per order
        FOR j IN 1..(1 + (i % 4)) LOOP
            SELECT pv.id, COALESCE(pv.price_override, p.base_price)
            INTO v_variant_id, v_price
            FROM product_variants pv
            JOIN products p ON p.id = pv.product_id
            WHERE pv.is_active = TRUE
            ORDER BY RANDOM()
            LIMIT 1;

            v_qty := 1 + (i * j % 3);

            INSERT INTO order_items (order_id, variant_id, quantity, unit_price, discount_amount)
            VALUES (v_order_id, v_variant_id, v_qty, v_price, 0)
            ON CONFLICT (order_id, variant_id) DO NOTHING;
        END LOOP;

        -- Calculate totals
        PERFORM calculate_order_total(v_order_id);

        -- Add payment for non-pending orders
        IF v_status NOT IN ('pending', 'cancelled') THEN
            INSERT INTO payments (order_id, payment_method, payment_status, amount, transaction_ref, paid_at)
            SELECT
                v_order_id,
                CASE (i % 4)
                    WHEN 0 THEN 'bkash'
                    WHEN 1 THEN 'nagad'
                    WHEN 2 THEN 'card'
                    ELSE 'cod'
                END,
                CASE
                    WHEN v_status IN ('refunded') THEN 'refunded'::payment_status
                    ELSE 'paid'::payment_status
                END,
                o.total_amount,
                'TXN-' || v_order_id || '-' || i,
                v_order_date + INTERVAL '5 minutes'
            FROM orders o WHERE o.id = v_order_id
            ON CONFLICT (order_id) DO NOTHING;
        END IF;

        -- Add shipment for shipped/delivered orders
        IF v_status IN ('shipped', 'delivered', 'returned') THEN
            INSERT INTO shipments (order_id, shipping_method_id, tracking_number, carrier_name,
                                   shipment_status, shipped_at, estimated_delivery, delivered_at)
            VALUES (
                v_order_id,
                v_method_id,
                'TRK' || LPAD(v_order_id::TEXT, 8, '0'),
                CASE (i % 4) WHEN 0 THEN 'Pathao' WHEN 1 THEN 'Sundarban' WHEN 2 THEN 'Redx' ELSE 'SA Paribahan' END,
                CASE v_status
                    WHEN 'delivered' THEN 'delivered'::shipment_status
                    WHEN 'returned'  THEN 'returned'::shipment_status
                    ELSE 'in_transit'::shipment_status
                END,
                v_order_date + INTERVAL '1 day',
                (v_order_date + INTERVAL '4 days')::DATE,
                CASE WHEN v_status = 'delivered' THEN v_order_date + INTERVAL '3 days' ELSE NULL END
            )
            ON CONFLICT (order_id) DO NOTHING;
        END IF;

    END LOOP;
END;
$$;

-- =============================================================================
-- REVIEWS (300 reviews on delivered orders)
-- =============================================================================

INSERT INTO reviews (customer_id, variant_id, order_id, rating, title, body, is_approved, is_verified)
SELECT DISTINCT ON (o.customer_id, oi.variant_id)
    o.customer_id,
    oi.variant_id,
    o.id AS order_id,
    (1 + (o.customer_id * oi.variant_id % 5))::SMALLINT AS rating,
    CASE (o.customer_id % 5)
        WHEN 0 THEN 'Excellent product!'
        WHEN 1 THEN 'Great quality'
        WHEN 2 THEN 'Good value for money'
        WHEN 3 THEN 'Satisfied with purchase'
        ELSE        'Highly recommended'
    END AS title,
    CASE ((o.customer_id + oi.variant_id) % 4)
        WHEN 0 THEN 'I absolutely love this product. The quality is outstanding and it arrived quickly.'
        WHEN 1 THEN 'Very good product. Exactly as described. Would buy again from this brand.'
        WHEN 2 THEN 'Decent quality for the price. Shipping was fast and packaging was great.'
        ELSE        'Good product overall. Minor issues with sizing but the material quality is good.'
    END AS body,
    TRUE AS is_approved,
    TRUE AS is_verified
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'delivered'
LIMIT 300;

-- =============================================================================
-- COUPON USAGES (link some coupons to orders)
-- =============================================================================

UPDATE orders SET coupon_id = (SELECT id FROM coupons WHERE code = 'WELCOME20')
WHERE id IN (SELECT id FROM orders ORDER BY id LIMIT 50);

INSERT INTO coupon_usages (coupon_id, customer_id, order_id, discount_applied)
SELECT DISTINCT
    o.coupon_id,
    o.customer_id,
    o.id,
    LEAST(o.subtotal * 0.20, 500)
FROM orders o
WHERE o.coupon_id IS NOT NULL
ON CONFLICT (coupon_id, customer_id) DO NOTHING;

-- =============================================================================
-- PRODUCT COLLECTIONS (link products to collections)
-- =============================================================================

INSERT INTO product_collections (product_id, collection_id)
SELECT DISTINCT
    p.id,
    c.id
FROM products p
CROSS JOIN collections c
WHERE (p.id + c.id) % 4 = 0  -- assign ~25% of product-collection combos
LIMIT 200
ON CONFLICT (product_id, collection_id) DO NOTHING;

-- =============================================================================
-- REFRESH MATERIALIZED VIEWS
-- =============================================================================

REFRESH MATERIALIZED VIEW mat_product_sales_summary;
REFRESH MATERIALIZED VIEW mat_daily_revenue;
REFRESH MATERIALIZED VIEW mat_inventory_health;

COMMIT;

-- =============================================================================
-- END OF SEED DATA
-- =============================================================================
