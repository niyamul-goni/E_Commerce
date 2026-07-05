"""
FashionHub — Real Schema Seed Script
Populates Supabase using the actual 45-table schema with raw SQL.
Run: .\\venv\\Scripts\\python.exe seed_real.py
"""
import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

def slug(name):
    return name.lower().replace(' ', '-').replace("'", '').replace('&', 'and').replace(',', '').replace('.', '')

# ── DATA ──────────────────────────────────────────────────────
CATEGORIES = [
    ("T-Shirts",    "Everyday cotton and blended T-shirts for men and women"),
    ("Shirts",      "Formal and casual shirts, button-up and polo styles"),
    ("Pants",       "Casual pants, chinos and cargo pants for everyday wear"),
    ("Trousers",    "Formal and semi-formal trousers for office and occasions"),
    ("Jeans",       "Denim jeans in slim, straight, and wide-leg cuts"),
    ("Shoes",       "Sneakers, loafers, oxfords, and casual footwear"),
    ("Jackets",     "Light jackets, blazers, windbreakers, and hoodies"),
    ("Activewear",  "Sports and gym wear — shorts, tracks, and compression gear"),
    ("Accessories", "Belts, caps, wallets, and sunglasses"),
    ("Winterwear",  "Sweaters, cardigans, coats, and thermal inner layers"),
]

# category_name → subcategories
SUBCATEGORIES = {
    "T-Shirts":    ["Graphic Tees", "Plain Tees", "Polo Tees", "Oversized Tees"],
    "Shirts":      ["Formal Shirts", "Casual Shirts", "Polo Shirts", "Linen Shirts"],
    "Pants":       ["Cargo Pants", "Chino Pants", "Track Pants", "Joggers"],
    "Trousers":    ["Formal Trousers", "Suit Trousers", "Dress Trousers"],
    "Jeans":       ["Slim Fit", "Straight Fit", "Skinny Fit", "Wide Leg"],
    "Shoes":       ["Sneakers", "Running Shoes", "Casual Shoes", "Formal Shoes"],
    "Jackets":     ["Windbreakers", "Blazers", "Track Jackets", "Padded Jackets"],
    "Activewear":  ["Running Shorts", "Track Pants", "Leggings", "Compression Gear"],
    "Accessories": ["Caps", "Belts", "Wallets", "Bags"],
    "Winterwear":  ["Hoodies", "Sweaters", "Cardigans", "Thermal Innerwear"],
}

BRANDS = [
    ("Nike",              "USA",     "https://www.nike.com",             "The world's leading sportswear brand."),
    ("Adidas",            "Germany", "https://www.adidas.com",           "Three stripes, endless performance."),
    ("Levi's",            "USA",     "https://www.levi.com",             "The original denim brand since 1853."),
    ("Zara",              "Spain",   "https://www.zara.com",             "Fast fashion with a premium edge."),
    ("H&M",               "Sweden",  "https://www.hm.com",              "Affordable fashion for everyone."),
    ("Puma",              "Germany", "https://www.puma.com",             "Sport lifestyle and performance."),
    ("Uniqlo",            "Japan",   "https://www.uniqlo.com",           "Life wear — elevated basics."),
    ("Polo Ralph Lauren", "USA",     "https://www.ralphlauren.com",      "Classic American luxury fashion."),
]

# (category, subcategory, brand, name, base_price, description, available_sizes, is_featured)
PRODUCTS = [
    # T-Shirts
    ("T-Shirts","Graphic Tees","Nike",         "Nike Dri-FIT Training Tee",       1850, "Lightweight moisture-wicking Dri-FIT fabric. Crew neck, short sleeve.", "XS,S,M,L,XL,XXL", True),
    ("T-Shirts","Plain Tees","Adidas",          "Adidas Essentials 3-Stripe Tee",  1650, "Classic 3-stripe tee in 100% cotton. Regular fit, ribbed crew neck.",    "XS,S,M,L,XL,XXL", True),
    ("T-Shirts","Oversized Tees","Puma",        "Puma Graphic Oversize Tee",       1400, "Relaxed oversize fit with bold Puma graphic print. Soft cotton jersey.", "S,M,L,XL,XXL",    False),
    ("T-Shirts","Plain Tees","H&M",             "H&M Slim-Fit Jersey T-Shirt",     699,  "Slim-fit tee in soft cotton jersey. Ribbed round neckline.",              "XS,S,M,L,XL",     False),
    ("T-Shirts","Graphic Tees","Uniqlo",        "Uniqlo UT Graphic Tee",           990,  "100% cotton UT graphic collection tee. Regular fit, pre-washed.",        "XS,S,M,L,XL,XXL", False),
    ("T-Shirts","Plain Tees","Zara",            "Zara Structured Collar Tee",      1290, "Premium cotton structured collar T-shirt. Subtle Zara branding.",        "XS,S,M,L,XL",     True),

    # Shirts
    ("Shirts","Formal Shirts","Polo Ralph Lauren","Ralph Lauren Classic Oxford Shirt",6500,"Iconic Oxford button-down in pure cotton. Signature pony embroidered.", "S,M,L,XL,XXL",    True),
    ("Shirts","Formal Shirts","Zara",           "Zara Slim-Fit Formal Shirt",      2490, "Slim-fit in easy-iron poplin. Spread collar, single-button cuffs.",      "XS,S,M,L,XL",     True),
    ("Shirts","Linen Shirts","H&M",             "H&M Regular-Fit Linen Shirt",     1499, "Breathable regular-fit in linen blend. Button-down with chest pocket.", "XS,S,M,L,XL,XXL", False),
    ("Shirts","Casual Shirts","Uniqlo",         "Uniqlo Extra Fine Cotton Shirt",  2490, "Ultra-soft extra-fine cotton. Non-iron, regular fit.",                   "XS,S,M,L,XL,XXL", False),
    ("Shirts","Polo Shirts","Polo Ralph Lauren","Ralph Lauren Polo Shirt",          5990, "The original polo in mesh pique cotton. Ribbed collar and cuffs.",       "S,M,L,XL,XXL",    True),
    ("Shirts","Polo Shirts","Adidas",           "Adidas Sports Polo Shirt",        2200, "AEROREADY fabric polo. Ribbed collar, 2-button placket.",                "XS,S,M,L,XL,XXL", False),

    # Pants
    ("Pants","Cargo Pants","Zara",              "Zara Cargo Pants",                3990, "Relaxed-fit cargo with multiple pockets. Elastic waistband.",            "XS,S,M,L,XL",     False),
    ("Pants","Chino Pants","H&M",               "H&M Chino Pants Slim Fit",        1999, "Slim-fit chino in cotton twill. Button and zip fly.",                    "28,30,32,34,36,38",True),
    ("Pants","Joggers","Uniqlo",                "Uniqlo Smart Ankle Pants",        2990, "Tapered ankle-length in stretch material. Smart casual silhouette.",     "28,30,32,34,36",   False),
    ("Pants","Track Pants","Nike",              "Nike Sportswear Tech Fleece Pants",5500,"Tech Fleece — warmth without bulk. Tapered fit, zippered pockets.",      "XS,S,M,L,XL,XXL", True),

    # Trousers
    ("Trousers","Suit Trousers","Zara",         "Zara Suit Trouser",               4490, "Tailored in wool-blend. Flat front, side pockets, belt loops.",          "28,30,32,34,36,38",True),
    ("Trousers","Formal Trousers","H&M",        "H&M Formal Slim Trousers",        2499, "Slim stretch formal trousers. Flat front with front creases.",           "28,30,32,34,36",   False),
    ("Trousers","Dress Trousers","Polo Ralph Lauren","Ralph Lauren Wool Dress Trouser",9500,"Fine wool dress trouser in classic fit. Dry clean.",               "30,32,34,36,38",   True),

    # Jeans
    ("Jeans","Straight Fit","Levi's",           "Levi's 501 Original Jeans",       4999, "The original since 1873. 100% cotton denim, button fly, 5-pocket.",      "28,30,32,34,36,38,40",True),
    ("Jeans","Slim Fit","Levi's",               "Levi's 511 Slim Jeans",           4499, "Slim from hip to ankle. Sits below waist, narrow leg opening.",          "28,30,32,34,36,38",True),
    ("Jeans","Skinny Fit","Zara",               "Zara Skinny Jeans",               3490, "Super-skinny stretch denim. Mid-rise with elasticated back panel.",      "24,26,28,30,32,34",False),
    ("Jeans","Straight Fit","H&M",              "H&M Straight Regular Jeans",      1999, "Regular waist, straight leg. 5-pocket styling, zip fly.",               "28,30,32,34,36,38",False),
    ("Jeans","Slim Fit","Levi's",               "Levi's 502 Taper Jeans",          4999, "Classic fit hip and thigh with a tapered leg. Mid-rise.",               "28,30,32,34,36,38",True),

    # Shoes
    ("Shoes","Sneakers","Nike",                 "Nike Air Force 1 '07",            8500, "Clean court styling with durable rubber sole. Classic silhouette.",      "38,39,40,41,42,43,44,45",True),
    ("Shoes","Casual Shoes","Adidas",           "Adidas Stan Smith",               7999, "Legendary tennis shoe since 1971. Leather upper, perforated detailing.", "38,39,40,41,42,43,44,45",True),
    ("Shoes","Sneakers","Puma",                 "Puma Suede Classic XXI",          6500, "Iconic suede leather upper. Rubber sole with Puma formstrip.",           "38,39,40,41,42,43,44",  False),
    ("Shoes","Running Shoes","Nike",            "Nike React Infinity Run Flyknit", 12999,"Designed to reduce injury. Flyknit upper, Nike React foam.",             "38,39,40,41,42,43,44,45,46",True),
    ("Shoes","Running Shoes","Adidas",          "Adidas Ultraboost 22",            14999,"Incredible energy return. Primeknit+ upper, Continental rubber.",        "38,39,40,41,42,43,44,45,46",True),
    ("Shoes","Sneakers","Puma",                 "Puma RS-X3 Puzzle Sneaker",       7800, "Bulky 90s runner. RS (Running System) technology, mesh upper.",          "38,39,40,41,42,43,44,45",  False),

    # Jackets
    ("Jackets","Windbreakers","Nike",           "Nike Windrunner Jacket",          6500, "Iconic Windrunner in lightweight ripstop. Raglan sleeves.",              "XS,S,M,L,XL,XXL", True),
    ("Jackets","Track Jackets","Adidas",        "Adidas Tiro Track Jacket",        4500, "AEROREADY slim-fit track jacket. 3-stripe sleeves, full-zip front.",     "XS,S,M,L,XL,XXL", True),
    ("Jackets","Blazers","Zara",                "Zara Structured Blazer",          7990, "Textured fabric blazer. Lapel collar, welt pockets, single button.",     "XS,S,M,L,XL",     True),
    ("Jackets","Windbreakers","H&M",            "H&M Hooded Windbreaker",          3499, "Lightweight hooded windbreaker. Elastic cuffs and hem.",                "XS,S,M,L,XL,XXL", False),
    ("Jackets","Padded Jackets","Puma",         "Puma Essentials Padded Jacket",   5500, "Lightweight padded jacket. Regular fit, full-zip, kangaroo pockets.",    "S,M,L,XL,XXL",    False),

    # Activewear
    ("Activewear","Running Shorts","Nike",      "Nike Dri-FIT Training Shorts",    2200, "Lightweight Dri-FIT shorts with inner lining. Elastic waistband.",       "XS,S,M,L,XL,XXL", False),
    ("Activewear","Track Pants","Adidas",       "Adidas Tiro 23 Track Pants",      3500, "AEROREADY track pants. Side zip pockets, ankle zips.",                  "XS,S,M,L,XL,XXL", False),
    ("Activewear","Leggings","Puma",            "Puma Run Favourite Running Leggings",3200,"4-way stretch for max comfort. High waist, hidden pocket.",            "XS,S,M,L,XL",     False),
    ("Activewear","Compression Gear","Nike",    "Nike Pro Compression Shorts",     2800, "Snug fit for muscle support. Dri-FIT technology, tight fit.",            "XS,S,M,L,XL,XXL", False),

    # Accessories
    ("Accessories","Caps","Nike",               "Nike Heritage86 Cap",             1500, "Classic 6-panel cap. Adjustable snap-back. Embroidered Swoosh.",         "One Size",         False),
    ("Accessories","Caps","Adidas",             "Adidas Linear Cap",               1299, "Curved-brim cap with Adidas logo. 6-panel, adjustable strap.",           "One Size",         False),
    ("Accessories","Belts","Polo Ralph Lauren", "Ralph Lauren Reversible Belt",    4500, "Reversible leather belt (black/brown). Silver-tone logo buckle.",        "30,32,34,36,38,40",False),
    ("Accessories","Wallets","Levi's",          "Levi's Slim Leather Wallet",      2500, "Slim bifold in genuine leather. Card slots, note compartment.",          "One Size",         False),

    # Winterwear
    ("Winterwear","Thermal Innerwear","Uniqlo", "Uniqlo Heattech Crew-Neck Tee",  1490, "HEATTECH generates heat from moisture. Stretchy slim inner layer.",     "XS,S,M,L,XL,XXL", True),
    ("Winterwear","Sweaters","Polo Ralph Lauren","Ralph Lauren Wool Crewneck Sweater",12500,"Merino wool crewneck. Ribbed neckline, cuffs and hem.",             "S,M,L,XL,XXL",    True),
    ("Winterwear","Hoodies","H&M",              "H&M Regular Fit Hoodie",          2499, "Cotton blend hoodie. Kangaroo pocket, ribbed cuffs, adjustable hood.",  "XS,S,M,L,XL,XXL", False),
    ("Winterwear","Cardigans","Zara",           "Zara Knit Cardigan",              4990, "Open-front cardigan in soft knit. V-neckline, two front pockets.",      "XS,S,M,L,XL",     False),
]

# ── SEED ──────────────────────────────────────────────────────
def run():
    with engine.connect() as conn:
        print("=" * 60)
        print("  FashionHub Real Schema Seeder")
        print("=" * 60)

        # 1. Brands
        print("\n[1/4] Seeding brands...")
        brand_ids = {}
        for name, country, website, desc in BRANDS:
            existing = conn.execute(text("SELECT id FROM brands WHERE name=:n"), {"n": name}).fetchone()
            if existing:
                brand_ids[name] = existing[0]
                print(f"  ~ exists: {name}")
            else:
                r = conn.execute(text(
                    "INSERT INTO brands(name,slug,country_of_origin,website_url,description,is_active) "
                    "VALUES(:n,:s,:c,:w,:d,true) RETURNING id"
                ), {"n": name, "s": slug(name), "c": country, "w": website, "d": desc})
                brand_ids[name] = r.fetchone()[0]
                print(f"  + {name}")
        conn.commit()
        print(f"  -> {len(brand_ids)} brands ready.")

        # 2. Categories
        print("\n[2/4] Seeding categories...")
        cat_ids = {}
        for name, desc in CATEGORIES:
            existing = conn.execute(text("SELECT id FROM categories WHERE name=:n"), {"n": name}).fetchone()
            if existing:
                cat_ids[name] = existing[0]
                print(f"  ~ exists: {name}")
            else:
                r = conn.execute(text(
                    "INSERT INTO categories(name,slug,description,is_active,sort_order) "
                    "VALUES(:n,:s,:d,true,0) RETURNING id"
                ), {"n": name, "s": slug(name), "d": desc})
                cat_ids[name] = r.fetchone()[0]
                print(f"  + {name}")
        conn.commit()
        print(f"  -> {len(cat_ids)} categories ready.")

        # 3. Subcategories
        print("\n[3/4] Seeding subcategories...")
        subcat_ids = {}
        for cat_name, subs in SUBCATEGORIES.items():
            cid = cat_ids.get(cat_name)
            if not cid:
                continue
            for sub in subs:
                key = f"{cat_name}/{sub}"
                existing = conn.execute(
                    text("SELECT id FROM subcategories WHERE name=:n AND category_id=:c"),
                    {"n": sub, "c": cid}
                ).fetchone()
                if existing:
                    subcat_ids[key] = existing[0]
                else:
                    r = conn.execute(text(
                        "INSERT INTO subcategories(category_id,name,slug,is_active,sort_order) "
                        "VALUES(:c,:n,:s,true,0) RETURNING id"
                    ), {"c": cid, "n": sub, "s": slug(cat_name) + '-' + slug(sub)})
                    subcat_ids[key] = r.fetchone()[0]
                    print(f"  + {cat_name} / {sub}")
        conn.commit()
        print(f"  -> {len(subcat_ids)} subcategories ready.")

        # 4. Suppliers (one per brand)
        print("\n[4/5] Seeding suppliers...")
        supplier_ids = {}
        brand_to_country = {b[0]: b[1] for b in BRANDS}
        for bname in brand_ids:
            existing = conn.execute(text("SELECT id FROM suppliers WHERE name=:n"), {"n": bname}).fetchone()
            if existing:
                supplier_ids[bname] = existing[0]
                print(f"  ~ exists: {bname}")
            else:
                r = conn.execute(text(
                    "INSERT INTO suppliers(name,contact_email,country,is_active) "
                    "VALUES(:n,:e,:c,true) RETURNING id"
                ), {"n": bname, "e": f"supply@{slug(bname)}.com", "c": brand_to_country.get(bname, 'Unknown')})
                supplier_ids[bname] = r.fetchone()[0]
                print(f"  + {bname}")
        conn.commit()
        print(f"  -> {len(supplier_ids)} suppliers ready.")

        # 5. Products
        print("\n[5/5] Seeding products...")
        created = 0
        skipped = 0
        for cat_name, subcat_name, brand_name, name, price, desc, sizes, featured in PRODUCTS:
            cid = cat_ids.get(cat_name)
            bid = brand_ids.get(brand_name)
            sid = supplier_ids.get(brand_name)
            scid = subcat_ids.get(f"{cat_name}/{subcat_name}")

            if not cid or not bid or not sid:
                print(f"  [!] Missing ref for: {name}")
                skipped += 1
                continue

            existing = conn.execute(text("SELECT id FROM products WHERE name=:n"), {"n": name}).fetchone()
            if existing:
                # update sizes
                conn.execute(text("UPDATE products SET available_sizes=:s WHERE id=:id"),
                             {"s": sizes, "id": existing[0]})
                skipped += 1
                continue

            conn.execute(text(
                "INSERT INTO products(name,slug,brand_id,supplier_id,subcategory_id,base_price,description,is_active,is_featured,available_sizes) "
                "VALUES(:n,:s,:b,:sid,:sc,:p,:d,true,:f,:sz)"
            ), {
                "n": name, "s": slug(name), "b": bid, "sid": sid,
                "sc": scid, "p": price, "d": desc,
                "f": featured, "sz": sizes
            })
            created += 1
            print(f"  + {name} | BDT {price:,}")

        conn.commit()
        print(f"  -> {created} products created, {skipped} skipped.")

        print("\n" + "=" * 60)
        print("  [DONE] Seeding complete!")
        print(f"  Brands       : {len(brand_ids)}")
        print(f"  Categories   : {len(cat_ids)}")
        print(f"  Subcategories: {len(subcat_ids)}")
        print(f"  Products     : {created} new | {skipped} already existed")
        print("=" * 60)

if __name__ == "__main__":
    run()
