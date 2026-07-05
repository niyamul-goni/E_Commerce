"""
Bangladeshi Fashion Brands Migration
Replaces all existing brands, categories, subcategories, suppliers and products
with authentic Bangladeshi fashion brand data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("Starting Bangladeshi fashion data migration...")

    # ── 1. Clear existing data ─────────────────────────────────────────────────
    print("Clearing existing product data...")
    db.execute(text("DELETE FROM product_images"))
    db.execute(text("DELETE FROM product_specifications"))
    db.execute(text("DELETE FROM product_variants"))
    db.execute(text("DELETE FROM product_collections"))
    db.execute(text("DELETE FROM products"))
    db.execute(text("DELETE FROM subcategories"))
    db.execute(text("DELETE FROM categories"))
    db.execute(text("DELETE FROM brands"))
    db.execute(text("DELETE FROM suppliers"))
    db.commit()
    print("Cleared existing data.")

    # ── 2. Insert Bangladeshi Brands ───────────────────────────────────────────
    print("Inserting Bangladeshi brands...")
    brands_data = [
        (1, 'Infinity',   'infinity',   'BD', 'https://infinitybd.com',   'Bangladesh\'s premium fashion house'),
        (2, 'Richman',    'richman',    'BD', 'https://richmanbd.com',    'Stylish menswear from Dhaka'),
        (3, 'Yellow',     'yellow',     'BD', 'https://yellowbd.com',     'Bright contemporary fashion'),
        (4, 'Easy',       'easy',       'BD', 'https://easybd.com',       'Affordable everyday fashion'),
        (5, 'Sailor',     'sailor',     'BD', 'https://sailorbd.com',     'Maritime-inspired Bangladeshi fashion'),
        (6, 'Ecstasy',    'ecstasy',    'BD', 'https://ecstasybd.com',    'Trendy urban fashion brand'),
        (7, 'Westecs',    'westecs',    'BD', 'https://westecs.com',      'Western-style Bangladeshi clothing'),
        (8, 'Texmart',    'texmart',    'BD', 'https://texmart.com.bd',   'Textile market fashion brand'),
    ]
    for b in brands_data:
        db.execute(text("""
            INSERT INTO brands (id, name, slug, country_of_origin, website_url, description, is_active)
            VALUES (:id, :name, :slug, :country, :website, :desc, true)
        """), {"id": b[0], "name": b[1], "slug": b[2], "country": b[3], "website": b[4], "desc": b[5]})

    # ── 3. Insert Bangladeshi Suppliers ───────────────────────────────────────
    print("Inserting suppliers...")
    suppliers_data = [
        (1, 'Infinity Ltd.',     'info@infinitybd.com',  '01711000001', 'House 12, Banani, Dhaka'),
        (2, 'Richman Trading',   'info@richman.com.bd',  '01711000002', 'Road 5, Gulshan, Dhaka'),
        (3, 'Yellow Fashions',   'info@yellowbd.com',    '01711000003', 'Level 4, Bashundhara, Dhaka'),
        (4, 'Easy Wear',         'info@easybd.com',      '01711000004', 'Block C, Mirpur, Dhaka'),
        (5, 'Sailor Group',      'info@sailorbd.com',    '01711000005', 'Agrabad, Chittagong'),
        (6, 'Ecstasy Apparel',   'info@ecstasybd.com',  '01711000006', 'Dhanmondi, Dhaka'),
        (7, 'Westecs Corp',      'info@westecs.com',     '01711000007', 'Motijheel, Dhaka'),
        (8, 'Texmart BD',        'info@texmart.com.bd',  '01711000008', 'Narayanganj'),
    ]
    for s in suppliers_data:
        db.execute(text("""
            INSERT INTO suppliers (id, name, contact_email, contact_phone, address, is_active)
            VALUES (:id, :name, :email, :phone, :address, true)
        """), {"id": s[0], "name": s[1], "email": s[2], "phone": s[3], "address": s[4]})

    # ── 4. Insert Categories ───────────────────────────────────────────────────
    print("Inserting categories...")
    categories_data = [
        (1, 'Shirts',      'shirts',      'Casual and formal shirts'),
        (2, 'T-Shirts',    't-shirts',    'Everyday comfortable tees'),
        (3, 'Pants',       'pants',       'Trousers and formal pants'),
        (4, 'Jeans',       'jeans',       'Denim jeans and joggers'),
        (5, 'Punjabi',     'punjabi',     'Traditional Bangladeshi Punjabi'),
        (6, 'Shoes',       'shoes',       'Footwear for men and women'),
        (7, 'Jackets',     'jackets',     'Casual and formal jackets'),
        (8, 'Activewear',  'activewear',  'Sports and gym clothing'),
        (9, 'Kurta',       'kurta',       'Traditional Bangladeshi Kurta'),
        (10, 'Accessories', 'accessories', 'Belts, bags and accessories'),
    ]
    for c in categories_data:
        db.execute(text("""
            INSERT INTO categories (id, name, slug, description, is_active, sort_order)
            VALUES (:id, :name, :slug, :desc, true, :id)
        """), {"id": c[0], "name": c[1], "slug": c[2], "desc": c[3]})

    # ── 5. Insert Subcategories ────────────────────────────────────────────────
    print("Inserting subcategories...")
    # Each category gets one subcategory (same category, for the JOIN to work)
    subcats_data = [
        (1, 1, 'Casual Shirts',      'casual-shirts'),
        (2, 2, 'Graphic Tees',       'graphic-tees'),
        (3, 3, 'Formal Pants',       'formal-pants'),
        (4, 4, 'Slim Jeans',         'slim-jeans'),
        (5, 5, 'Cotton Punjabi',     'cotton-punjabi'),
        (6, 6, 'Sneakers',           'sneakers'),
        (7, 7, 'Casual Jackets',     'casual-jackets'),
        (8, 8, 'Gym Wear',           'gym-wear'),
        (9, 9, 'Embroidered Kurta',  'embroidered-kurta'),
        (10, 10, 'Leather Belts',    'leather-belts'),
    ]
    for sc in subcats_data:
        db.execute(text("""
            INSERT INTO subcategories (id, category_id, name, slug, is_active, sort_order)
            VALUES (:id, :cat_id, :name, :slug, true, :id)
        """), {"id": sc[0], "cat_id": sc[1], "name": sc[2], "slug": sc[3]})

    db.commit()
    print("Inserted brands, suppliers, categories, subcategories.")

    # ── 6. Insert Bangladeshi Products ────────────────────────────────────────
    # size mapping:
    # Shirts/T-Shirts/Jackets/Activewear/Kurta/Punjabi → XS,S,M,L,XL,XXL
    # Pants/Jeans → 28,30,32,34,36,38
    # Shoes → 38,39,40,41,42,43,44,45
    # Accessories → One Size
    CLOTH_SIZES  = 'XS,S,M,L,XL,XXL'
    BOTTOM_SIZES = '28,30,32,34,36,38'
    SHOE_SIZES   = '38,39,40,41,42,43,44,45'
    ACC_SIZES    = 'One Size'

    print("Inserting products...")
    products = [
        # (id, name, slug, brand_id, supplier_id, subcat_id, price, description, sizes, is_featured)
        # ── Infinity shirts (subcat 1 = Shirts)
        (1,  'Infinity Classic Oxford Shirt',     'infinity-oxford-shirt',       1, 1, 1, 1490, 'Premium cotton Oxford weave, button-down collar. Regular fit.', CLOTH_SIZES, True),
        (2,  'Infinity Linen Summer Shirt',       'infinity-linen-shirt',        1, 1, 1, 1890, '100% linen fabric. Relaxed fit, perfect for summer.', CLOTH_SIZES, False),
        (3,  'Infinity Formal Dress Shirt',       'infinity-formal-shirt',       1, 1, 1, 2190, 'Spread collar formal shirt. Non-iron finish.', CLOTH_SIZES, False),
        # ── Richman T-Shirts (subcat 2)
        (4,  'Richman Essential Crew Tee',        'richman-crew-tee',            2, 2, 2, 550, '100% cotton jersey. Regular fit everyday tee.', CLOTH_SIZES, True),
        (5,  'Richman Graphic Print Tee',         'richman-graphic-tee',         2, 2, 2, 750, 'Bold Bangladeshi-inspired graphic print on soft cotton.', CLOTH_SIZES, False),
        (6,  'Richman Polo Collar Tee',           'richman-polo-tee',            2, 2, 2, 890, 'Pique cotton polo. Smart-casual style.', CLOTH_SIZES, False),
        # ── Yellow Pants (subcat 3)
        (7,  'Yellow Slim Chino Pants',           'yellow-slim-chino',           3, 3, 3, 1290, 'Stretch chino slim fit. Classic Dhaka street style.', BOTTOM_SIZES, True),
        (8,  'Yellow Formal Trouser',             'yellow-formal-trouser',       3, 3, 3, 1490, 'Flat-front formal trouser. Office-ready.', BOTTOM_SIZES, False),
        (9,  'Yellow Cargo Pocket Pants',         'yellow-cargo-pants',          3, 3, 3, 1190, 'Multi-pocket utility pants. Relaxed waistband.', BOTTOM_SIZES, False),
        # ── Easy Jeans (subcat 4)
        (10, 'Easy Slim Stretch Jeans',           'easy-slim-jeans',             4, 4, 4, 1190, 'Slim fit stretch denim. Comfortable all-day wear.', BOTTOM_SIZES, True),
        (11, 'Easy Relaxed Fit Jeans',            'easy-relaxed-jeans',          4, 4, 4, 990, 'Loose fit denim. Perfect for casual days.', BOTTOM_SIZES, False),
        (12, 'Easy Black Skinny Jeans',           'easy-skinny-jeans',           4, 4, 4, 1090, 'Super stretch black denim. Mid-rise cut.', BOTTOM_SIZES, False),
        # ── Sailor Punjabi (subcat 5)
        (13, 'Sailor Eid Embroidered Punjabi',    'sailor-eid-punjabi',          5, 5, 5, 2490, 'Hand-embroidered cotton Punjabi. Perfect for Eid.', CLOTH_SIZES, True),
        (14, 'Sailor Plain Cotton Punjabi',       'sailor-plain-punjabi',        5, 5, 5, 1290, 'Comfortable plain cotton Punjabi. Everyday wear.', CLOTH_SIZES, False),
        (15, 'Sailor Muslin Punjabi',             'sailor-muslin-punjabi',       5, 5, 5, 3490, 'Authentic Dhakai Muslin Punjabi. Luxury handcraft.', CLOTH_SIZES, True),
        # ── Ecstasy Shoes (subcat 6)
        (16, 'Ecstasy Canvas Sneaker',            'ecstasy-canvas-sneaker',      6, 6, 6, 1890, 'Lightweight canvas upper. Rubber sole. Urban style.', SHOE_SIZES, True),
        (17, 'Ecstasy Leather Oxford',            'ecstasy-leather-oxford',      6, 6, 6, 2990, 'Genuine leather Oxford. Formal occasions.', SHOE_SIZES, False),
        (18, 'Ecstasy Running Shoe',              'ecstasy-running-shoe',        6, 6, 6, 2490, 'Cushioned EVA sole. Breathable mesh upper.', SHOE_SIZES, False),
        (19, 'Ecstasy Loafer Slip-On',            'ecstasy-loafer',              6, 6, 6, 1690, 'Suede loafer. Slip-on comfort with metal buckle.', SHOE_SIZES, False),
        # ── Westecs Jackets (subcat 7)
        (20, 'Westecs Bomber Jacket',             'westecs-bomber',              7, 7, 7, 2890, 'Classic bomber silhouette. Ribbed cuffs and hem.', CLOTH_SIZES, True),
        (21, 'Westecs Denim Jacket',              'westecs-denim-jacket',        7, 7, 7, 2490, 'Classic blue denim jacket. Brass button closure.', CLOTH_SIZES, False),
        (22, 'Westecs Windbreaker',               'westecs-windbreaker',         7, 7, 7, 1990, 'Lightweight wind-resistant jacket. Packable hood.', CLOTH_SIZES, False),
        # ── Texmart Activewear (subcat 8)
        (23, 'Texmart Dry-Fit T-Shirt',           'texmart-dryfit-tee',          8, 8, 8, 690, 'Moisture-wicking poly fabric. Perfect for workouts.', CLOTH_SIZES, False),
        (24, 'Texmart Track Pants',               'texmart-track-pants',         8, 8, 8, 890, 'Elastic waist track pants. Side zip pockets.', BOTTOM_SIZES, False),
        (25, 'Texmart Gym Shorts',                'texmart-gym-shorts',          8, 8, 8, 590, '100% polyester gym shorts. Breathable mesh lining.', CLOTH_SIZES, False),
        # ── Infinity Kurta (subcat 9)
        (26, 'Infinity Cotton Kurta',             'infinity-kurta-cotton',       1, 1, 9, 1190, 'Lightweight cotton kurta. Festive embroidery at cuff.', CLOTH_SIZES, True),
        (27, 'Infinity Silk Blend Kurta',         'infinity-kurta-silk',         1, 1, 9, 2490, 'Silk blend premium kurta. Perfect for occasions.', CLOTH_SIZES, False),
        # ── Richman Accessories (subcat 10)
        (28, 'Richman Leather Belt',              'richman-leather-belt',        2, 2, 10, 690, 'Genuine leather belt. Silver-tone pin buckle.', ACC_SIZES, False),
        (29, 'Richman Canvas Backpack',           'richman-canvas-bag',          2, 2, 10, 1490, 'Durable canvas backpack. Multiple compartments.', ACC_SIZES, False),
        (30, 'Richman Cotton Cap',                'richman-cap',                 2, 2, 10, 390, 'Adjustable cotton cap. Embroidered Richman logo.', ACC_SIZES, False),
        # ── Yellow Shirts (subcat 1)
        (31, 'Yellow Check Casual Shirt',         'yellow-check-shirt',          3, 3, 1, 1190, 'Classic check pattern. Button-down pocket. Easy fit.', CLOTH_SIZES, False),
        (32, 'Yellow Printed Shirt',              'yellow-printed-shirt',        3, 3, 1, 1290, 'Vibrant floral print. Resort-wear style.', CLOTH_SIZES, True),
        # ── Easy T-Shirts (subcat 2)
        (33, 'Easy Oversized Tee',                'easy-oversized-tee',          4, 4, 2, 490, 'Boxy oversized fit. 100% cotton pre-washed.', CLOTH_SIZES, False),
        (34, 'Easy Plain V-Neck Tee',             'easy-vneck-tee',              4, 4, 2, 450, 'Simple V-neck tee. Available in 8 colors.', CLOTH_SIZES, False),
        # ── Sailor Shoes (subcat 6)
        (35, 'Sailor Boat Shoe',                  'sailor-boat-shoe',            5, 5, 6, 2190, 'Moccasin-toe boat shoe. Non-slip sole. Maritime style.', SHOE_SIZES, False),
        (36, 'Sailor Formal Sandal',              'sailor-formal-sandal',        5, 5, 6, 1490, 'Genuine leather formal sandal. Adjustable strap.', SHOE_SIZES, False),
        # ── Ecstasy Punjabi (subcat 5)
        (37, 'Ecstasy Embroidered Punjabi',       'ecstasy-embroidered-punjabi', 6, 6, 5, 2890, 'Festive Eid Punjabi with gold embroidery.', CLOTH_SIZES, True),
        (38, 'Ecstasy Striped Punjabi',           'ecstasy-striped-punjabi',     6, 6, 5, 1590, 'Striped cotton Punjabi. Casual daily wear.', CLOTH_SIZES, False),
        # ── Westecs Pants (subcat 3)
        (39, 'Westecs Executive Trouser',         'westecs-executive-trouser',   7, 7, 3, 1790, 'Wool-blend executive trouser. Flat front.', BOTTOM_SIZES, False),
        (40, 'Westecs Jogger Pants',              'westecs-jogger',              7, 7, 3, 1190, 'Tapered jogger pants. Elasticated cuffs.', BOTTOM_SIZES, False),
        # ── Texmart Jeans (subcat 4)
        (41, 'Texmart Raw Denim Jeans',           'texmart-raw-denim',           8, 8, 4, 1390, 'Unwashed raw denim. Regular fit.', BOTTOM_SIZES, False),
        (42, 'Texmart Distressed Jeans',          'texmart-distressed-jeans',    8, 8, 4, 1190, 'Ripped knee distressed jeans. Slim cut.', BOTTOM_SIZES, False),
        # ── Infinity Accessories (subcat 10)
        (43, 'Infinity Tie Collection',           'infinity-tie',                1, 1, 10, 990, 'Silk blend tie. 12 classic patterns.', ACC_SIZES, False),
        (44, 'Infinity Sunglasses',               'infinity-sunglasses',         1, 1, 10, 890, 'UV400 polarized lenses. Metal frame.', ACC_SIZES, False),
        # ── Richman Jackets (subcat 7)
        (45, 'Richman Blazer Jacket',             'richman-blazer',              2, 2, 7, 3490, 'Single-button slim blazer. Structured shoulders.', CLOTH_SIZES, True),
        (46, 'Richman Hooded Sweatshirt',         'richman-hoodie',              2, 2, 7, 1490, 'Fleece-lined hoodie. Kangaroo pocket.', CLOTH_SIZES, False),
        # ── Yellow Activewear (subcat 8)
        (47, 'Yellow Yoga Leggings',              'yellow-yoga-leggings',        3, 3, 8, 890, 'High-waist 4-way stretch leggings. Squat-proof.', CLOTH_SIZES, False),
    ]

    for p in products:
        db.execute(text("""
            INSERT INTO products
                (id, name, slug, brand_id, supplier_id, subcategory_id, base_price,
                 description, available_sizes, is_featured, is_active, gender_id)
            VALUES
                (:id, :name, :slug, :brand_id, :supplier_id, :subcat_id, :price,
                 :desc, :sizes, :featured, true, NULL)
        """), {
            "id": p[0], "name": p[1], "slug": p[2], "brand_id": p[3],
            "supplier_id": p[4], "subcat_id": p[5], "price": p[6],
            "desc": p[7], "sizes": p[8], "featured": p[9],
        })

    db.commit()
    print(f"Inserted {len(products)} products.")

    # ── 7. Reset sequences ────────────────────────────────────────────────────
    db.execute(text("SELECT setval('brands_id_seq',    (SELECT MAX(id) FROM brands))"))
    db.execute(text("SELECT setval('suppliers_id_seq', (SELECT MAX(id) FROM suppliers))"))
    db.execute(text("SELECT setval('categories_id_seq',(SELECT MAX(id) FROM categories))"))
    db.execute(text("SELECT setval('subcategories_id_seq',(SELECT MAX(id) FROM subcategories))"))
    db.execute(text("SELECT setval('products_id_seq',  (SELECT MAX(id) FROM products))"))
    db.commit()

    # ── 8. Verify ─────────────────────────────────────────────────────────────
    count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
    brands = db.execute(text("SELECT name FROM brands ORDER BY name")).fetchall()
    cats   = db.execute(text("SELECT name FROM categories ORDER BY name")).fetchall()
    print(f"\n=== DONE ===")
    print(f"Products: {count}")
    print(f"Brands: {[b[0] for b in brands]}")
    print(f"Categories: {[c[0] for c in cats]}")

    # Sample product check
    sample = db.execute(text("""
        SELECT p.name, b.name, c.name, p.base_price, p.available_sizes
        FROM products p
        JOIN brands b ON b.id = p.brand_id
        JOIN subcategories sc ON sc.id = p.subcategory_id
        JOIN categories c ON c.id = sc.category_id
        LIMIT 5
    """)).fetchall()
    for row in sample:
        print(f"  {row[0]} | brand={row[1]} | cat={row[2]} | price={row[3]} BDT | sizes={row[4]}")

except Exception as e:
    db.rollback()
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
