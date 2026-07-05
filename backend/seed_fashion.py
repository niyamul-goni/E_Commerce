"""
FashionHub — Seed Script
Populates Supabase with fashion categories, brands (suppliers), and products.
Run from the backend directory:
    .\\venv\\Scripts\\python.exe seed_fashion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make sure app is importable
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.product import Product

# ──────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────

CATEGORIES = [
    {"name": "T-Shirts",    "description": "Casual everyday cotton and blended T-shirts for men and women"},
    {"name": "Shirts",      "description": "Formal and casual shirts, button-up and polo styles"},
    {"name": "Pants",       "description": "Casual pants, chinos and cargo pants for everyday wear"},
    {"name": "Trousers",    "description": "Formal and semi-formal trousers for office and occasions"},
    {"name": "Jeans",       "description": "Denim jeans in slim, straight, and wide-leg cuts"},
    {"name": "Shoes",       "description": "Sneakers, loafers, oxfords, and casual footwear"},
    {"name": "Jackets",     "description": "Light jackets, blazers, windbreakers, and hoodies"},
    {"name": "Activewear",  "description": "Sports and gym wear — shorts, tracks, and compression gear"},
    {"name": "Accessories", "description": "Belts, caps, wallets, watches, and sunglasses"},
    {"name": "Winterwear",  "description": "Sweaters, cardigans, coats, and thermal inner layers"},
]

SUPPLIERS = [
    {
        "name": "Nike",
        "contact_email": "partners@nike.com",
        "contact_phone": "+1-800-806-6453",
        "address": "One Bowerman Drive, Beaverton, OR 97005, USA",
    },
    {
        "name": "Adidas",
        "contact_email": "partners@adidas.com",
        "contact_phone": "+49-9132-84-0",
        "address": "Adi-Dassler-Strasse 1, 91074 Herzogenaurach, Germany",
    },
    {
        "name": "Levi's",
        "contact_email": "wholesale@levis.com",
        "contact_phone": "+1-415-501-6000",
        "address": "Levi's Plaza, 1155 Battery Street, San Francisco, CA, USA",
    },
    {
        "name": "Zara",
        "contact_email": "b2b@zara.com",
        "contact_phone": "+34-981-185-400",
        "address": "Avenida de la Diputación, Edificio Inditex, Arteixo, Spain",
    },
    {
        "name": "H&M",
        "contact_email": "wholesale@hm.com",
        "contact_phone": "+46-8-796-5500",
        "address": "Mäster Samuelsgatan 46A, Stockholm, Sweden",
    },
    {
        "name": "Puma",
        "contact_email": "trade@puma.com",
        "contact_phone": "+49-9132-81-0",
        "address": "PUMA Way 1, 91074 Herzogenaurach, Germany",
    },
    {
        "name": "Uniqlo",
        "contact_email": "partners@uniqlo.com",
        "contact_phone": "+81-3-6865-0930",
        "address": "717-1 Sayama, Yamaguchi City, Yamaguchi Prefecture, Japan",
    },
    {
        "name": "Polo Ralph Lauren",
        "contact_email": "wholesale@ralphlauren.com",
        "contact_phone": "+1-212-318-7000",
        "address": "650 Madison Avenue, New York, NY 10022, USA",
    },
]


# category_name, supplier_name, name, sku, price, stock, description
PRODUCTS = [
    # ── T-Shirts ──────────────────────────────────────────────────────
    ("T-Shirts", "Nike",           "Nike Dri-FIT Training Tee",         "NK-DFIT-001", 1850, 120, "Lightweight moisture-wicking Dri-FIT fabric keeps you dry during workouts. Crew neck, short sleeve."),
    ("T-Shirts", "Adidas",         "Adidas Essentials 3-Stripe Tee",    "AD-3STR-001", 1650, 95,  "Classic Adidas 3-stripe tee in 100% cotton. Regular fit, ribbed crew neck."),
    ("T-Shirts", "Puma",           "Puma Graphic Oversize Tee",         "PM-GRFX-001", 1400, 80,  "Relaxed oversize fit with bold Puma graphic print on chest. Soft cotton jersey."),
    ("T-Shirts", "H&M",            "H&M Slim-Fit Jersey T-Shirt",       "HM-SLIM-001", 699,  200, "Slim-fit tee in soft cotton jersey. Ribbed round neckline with short sleeves."),
    ("T-Shirts", "Uniqlo",         "Uniqlo UT Graphic Tee",             "UQ-UTGR-001", 990,  150, "100% cotton UT graphic collection tee. Comfortable regular fit, pre-washed for softness."),
    ("T-Shirts", "Zara",           "Zara Structured Collar Tee",        "ZR-SCOL-001", 1290, 70,  "Premium cotton structured collar T-shirt. Subtle Zara branding at hem. Semi-fitted."),

    # ── Shirts ────────────────────────────────────────────────────────
    ("Shirts",   "Polo Ralph Lauren", "Ralph Lauren Classic Oxford Shirt", "RL-OXFD-001", 6500, 45,  "Iconic Oxford button-down shirt in pure cotton. Signature pony embroidered on chest."),
    ("Shirts",   "Zara",           "Zara Slim-Fit Formal Shirt",        "ZR-SLIM-001", 2490, 60,  "Slim-fit formal shirt in easy-iron poplin. Spread collar, single-button cuffs."),
    ("Shirts",   "H&M",            "H&M Regular-Fit Linen Shirt",       "HM-LIN-001",  1499, 90,  "Breathable regular-fit shirt in linen blend. Button-down front with one chest pocket."),
    ("Shirts",   "Uniqlo",         "Uniqlo Extra Fine Cotton Shirt",    "UQ-EFC-001",  2490, 75,  "Crafted from extra-fine cotton for ultra-soft feel. Non-iron, regular fit."),
    ("Shirts",   "Polo Ralph Lauren", "Ralph Lauren Polo Shirt",        "RL-POLO-001", 5990, 55,  "The original polo shirt in mesh piqué cotton. Ribbed collar and cuffs, 2-button placket."),
    ("Shirts",   "Adidas",         "Adidas Sports Polo Shirt",          "AD-POLO-001", 2200, 65,  "Polo shirt with moisture-wicking AEROREADY fabric. Ribbed collar, 2-button placket."),

    # ── Pants ─────────────────────────────────────────────────────────
    ("Pants",    "Zara",           "Zara Cargo Pants",                  "ZR-CRGO-001", 3990, 50,  "Relaxed-fit cargo pants with multiple pockets. Elastic waistband with drawstring."),
    ("Pants",    "H&M",            "H&M Chino Pants Slim Fit",          "HM-CHIN-001", 1999, 80,  "Slim-fit chino pants in cotton twill. Button and zip fly with belt loops."),
    ("Pants",    "Uniqlo",         "Uniqlo Smart Ankle Pants",          "UQ-SMAR-001", 2990, 65,  "Tapered ankle-length pants in stretch material. Neat slim silhouette for smart casual wear."),
    ("Pants",    "Nike",           "Nike Sportswear Tech Fleece Pants",  "NK-TECH-001", 5500, 40,  "Tech Fleece fabric delivers warmth without bulk. Tapered fit with zippered side pockets."),

    # ── Trousers ──────────────────────────────────────────────────────
    ("Trousers", "Zara",           "Zara Suit Trouser",                 "ZR-SUIT-001", 4490, 35,  "Tailored suit trouser in wool-blend fabric. Flat front, side pockets, belt loops."),
    ("Trousers", "H&M",            "H&M Formal Slim Trousers",          "HM-FRML-001", 2499, 55,  "Slim-fit formal trousers in stretch fabric. Flat front with front creases for a sharp look."),
    ("Trousers", "Polo Ralph Lauren", "Ralph Lauren Wool Dress Trouser", "RL-DRSS-001", 9500, 25,  "Fine wool dress trouser in classic fit. Dry clean recommended. Perfect for formal occasions."),

    # ── Jeans ─────────────────────────────────────────────────────────
    ("Jeans",    "Levi's",         "Levi's 501 Original Jeans",         "LV-501-001",  4999, 100, "The original straight-leg jean since 1873. 100% cotton denim, button fly, 5-pocket styling."),
    ("Jeans",    "Levi's",         "Levi's 511 Slim Jeans",             "LV-511-001",  4499, 90,  "Slim fit from hip to ankle. Sits below waist, close to thigh and knee, narrow leg opening."),
    ("Jeans",    "Zara",           "Zara Skinny Jeans",                 "ZR-SKIN-001", 3490, 75,  "Super-skinny stretch denim. Mid-rise waist with elasticated waistband panel at back."),
    ("Jeans",    "H&M",            "H&M Straight Regular Jeans",        "HM-STRG-001", 1999, 110, "Regular waist, straight leg classic jeans. 5-pocket styling, zip fly."),
    ("Jeans",    "Levi's",         "Levi's 502 Taper Jeans",            "LV-502-001",  4999, 60,  "A classic fit through the hip and thigh with a tapered leg. Mid-rise, regular fit."),

    # ── Shoes ─────────────────────────────────────────────────────────
    ("Shoes",    "Nike",           "Nike Air Force 1 '07",              "NK-AF1-001",  8500, 55,  "The radiance lives on in the Nike Air Force 1. Clean court styling with a durable rubber sole."),
    ("Shoes",    "Adidas",         "Adidas Stan Smith",                 "AD-STAN-001", 7999, 50,  "The original tennis shoe since 1971. Leather upper, perforated 3-stripe detailing."),
    ("Shoes",    "Puma",           "Puma Suede Classic XXI",            "PM-SUED-001", 6500, 40,  "Legendary suede leather upper in iconic silhouette. Rubber sole with Puma formstrip."),
    ("Shoes",    "Nike",           "Nike React Infinity Run Flyknit",   "NK-RFLY-001", 12999, 30, "Designed to reduce injury with more foam and a secure fit. Flyknit upper, Nike React foam."),
    ("Shoes",    "Adidas",         "Adidas Ultraboost 22",              "AD-UB22-001", 14999, 25, "Incredible energy return with Boost midsole. Primeknit+ textile upper, Continental rubber outsole."),
    ("Shoes",    "Puma",           "Puma RS-X³ Puzzle Sneaker",         "PM-RSX3-001", 7800, 45,  "Bulky 90s runner reinterpreted. RS (Running System) technology, mesh and synthetic upper."),

    # ── Jackets ───────────────────────────────────────────────────────
    ("Jackets",  "Nike",           "Nike Windrunner Jacket",            "NK-WIND-001", 6500, 40,  "Iconic Windrunner in lightweight ripstop fabric. Raglan sleeves, elasticated cuffs and hem."),
    ("Jackets",  "Adidas",         "Adidas Tiro Track Jacket",          "AD-TIRO-001", 4500, 55,  "Slim-fit track jacket in AEROREADY fabric. 3-stripe detailing on sleeves, full-zip front."),
    ("Jackets",  "Zara",           "Zara Structured Blazer",            "ZR-BLZR-001", 7990, 30,  "Structured blazer in textured fabric. Lapel collar, welt pockets, single-button fastening."),
    ("Jackets",  "H&M",            "H&M Hooded Windbreaker",            "HM-HOOD-001", 3499, 70,  "Lightweight hooded windbreaker with front zip. Elastic cuffs and hem, kangaroo pocket."),
    ("Jackets",  "Puma",           "Puma Essentials Padded Jacket",     "PM-PADD-001", 5500, 35,  "Lightweight padded jacket for cooler days. Regular fit, full-zip, kangaroo pockets."),

    # ── Activewear ────────────────────────────────────────────────────
    ("Activewear", "Nike",         "Nike Dri-FIT Training Shorts",      "NK-SHRT-001", 2200, 90,  "Lightweight Dri-FIT shorts with inner lining. Elastic waistband with drawstring, side pockets."),
    ("Activewear", "Adidas",       "Adidas Tiro 23 Track Pants",        "AD-TR23-001", 3500, 75,  "Regular-fit track pants with AEROREADY fabric. Side zip pockets, ankle zips."),
    ("Activewear", "Puma",         "Puma Run Favourite Running Leggings","PM-LEGG-001", 3200, 60,  "4-way stretch fabric for maximum comfort. High waist, hidden pocket, reflective logo."),
    ("Activewear", "Nike",         "Nike Pro Compression Shorts",        "NK-COMP-001", 2800, 80,  "Snug fit for targeted muscle support. Dri-FIT technology, tight fit, no seam at crotch."),

    # ── Accessories ───────────────────────────────────────────────────
    ("Accessories", "Nike",        "Nike Heritage86 Cap",               "NK-CAP-001",  1500, 150, "Classic 6-panel structured cap. Adjustable snap-back closure, embroidered Nike Swoosh."),
    ("Accessories", "Adidas",      "Adidas Linear Cap",                 "AD-CAP-001",  1299, 130, "Curved-brim cap with Adidas linear logo. 6-panel construction, adjustable strap."),
    ("Accessories", "Polo Ralph Lauren", "Ralph Lauren Reversible Belt", "RL-BELT-001", 4500, 60,  "Reversible leather belt (black/brown) with logo silver-tone buckle. Genuine leather."),
    ("Accessories", "Levi's",      "Levi's Slim Leather Wallet",        "LV-WALT-001", 2500, 80,  "Slim bifold wallet in genuine leather. Card slots, note compartment, Levi's branding."),

    # ── Winterwear ────────────────────────────────────────────────────
    ("Winterwear", "Uniqlo",       "Uniqlo Heattech Crew-Neck T-Shirt", "UQ-HEAT-001", 1490, 120, "HEATTECH technology generates heat from body moisture. Stretchy, slim-fit inner layer."),
    ("Winterwear", "Polo Ralph Lauren", "Ralph Lauren Wool Crewneck Sweater","RL-WSWT-001",12500,30, "Merino wool crewneck sweater. Ribbed neckline, cuffs and hem. Signature Pony embroidery."),
    ("Winterwear", "H&M",          "H&M Regular Fit Hoodie",            "HM-HOOD-W01", 2499, 100, "Regular-fit hoodie in cotton blend. Kangaroo pocket, ribbed cuffs and hem, adjustable hood."),
    ("Winterwear", "Zara",         "Zara Knit Cardigan",                "ZR-CARD-001", 4990, 40,  "Open-front cardigan in soft knit fabric. V-neckline, long sleeves, two front pockets."),
]


# ──────────────────────────────────────────────
# SEEDER
# ──────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("  FashionHub — Database Seeder")
        print("=" * 60)

        # ── 1. Categories ──────────────────────────────────────────
        print("\n[1/3] Seeding categories…")
        category_map: dict[str, int] = {}
        for cat_data in CATEGORIES:
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if existing:
                category_map[cat_data["name"]] = existing.id
                print(f"  ✓ Already exists: {cat_data['name']}")
            else:
                cat = Category(name=cat_data["name"], description=cat_data["description"], is_active=True)
                db.add(cat)
                db.flush()
                category_map[cat_data["name"]] = cat.id
                print(f"  + Created: {cat_data['name']}")
        db.commit()
        print(f"  -> {len(category_map)} categories ready.")

        # ── 2. Suppliers (Brands) ──────────────────────────────────
        print("\n[2/3] Seeding brands (suppliers)…")
        supplier_map: dict[str, int] = {}
        for sup_data in SUPPLIERS:
            existing = db.query(Supplier).filter(Supplier.name == sup_data["name"]).first()
            if existing:
                supplier_map[sup_data["name"]] = existing.id
                print(f"  ✓ Already exists: {sup_data['name']}")
            else:
                sup = Supplier(
                    name=sup_data["name"],
                    contact_email=sup_data["contact_email"],
                    contact_phone=sup_data["contact_phone"],
                    address=sup_data["address"],
                    is_active=True,
                )
                db.add(sup)
                db.flush()
                supplier_map[sup_data["name"]] = sup.id
                print(f"  + Created: {sup_data['name']}")
        db.commit()
        print(f"  -> {len(supplier_map)} brands ready.")

        # ── 3. Products ────────────────────────────────────────────
        print("\n[3/3] Seeding products…")
        created = 0
        skipped = 0
        for cat_name, sup_name, name, sku, price, stock, desc in PRODUCTS:
            existing = db.query(Product).filter(Product.sku == sku).first()
            if existing:
                print(f"  ✓ Already exists: {name} ({sku})")
                skipped += 1
                continue

            cat_id = category_map.get(cat_name)
            sup_id = supplier_map.get(sup_name)
            if not cat_id or not sup_id:
                print(f"  [!] Skipping {name} — missing category or supplier mapping")
                skipped += 1
                continue

            product = Product(
                name=name,
                sku=sku,
                description=desc,
                price=price,
                stock_quantity=stock,
                is_active=True,
                category_id=cat_id,
                supplier_id=sup_id,
            )
            db.add(product)
            created += 1
            print(f"  + Created: {name} | BDT {price:,} | Stock: {stock}")

        db.commit()
        print(f"  -> {created} products created, {skipped} skipped.")

        print("\n" + "=" * 60)
        print("  [DONE]  Seeding complete!")
        print(f"  Categories : {len(category_map)}")
        print(f"  Brands     : {len(supplier_map)}")
        print(f"  Products   : {created} new  |  {skipped} already existed")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Error during seeding: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
