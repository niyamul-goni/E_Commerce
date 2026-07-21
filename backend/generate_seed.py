#!/usr/bin/env python3
"""
generate_seed.py — Generates seed_products.sql for the FashionHub Supabase schema.

Creates ~70 realistic Bangladeshi fashion products with:
  - Categories & subcategories
  - Brands (Infinity, Richman, Yellow, Easy, Sailor, Ecstasy, Westecs, Texmart)
  - Products with descriptions, prices (BDT), images, sizes, colors
  - Product variants with inventory
  - Product images (using picsum.photos placeholders)
  - Reviews

Run:  python generate_seed.py
Output: ../database/seed_products.sql
"""
from __future__ import annotations

import random
import textwrap
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "database" / "seed_products.sql"

# ─── Reference Data ──────────────────────────────────────────────────────────

BRANDS = [
    ("Infinity", "Premium Bangladeshi fashion brand known for formal and casual wear"),
    ("Richman", "Leading menswear brand offering shirts, trousers, and suits"),
    ("Yellow", "Trendy youth fashion brand with colorful collections"),
    ("Easy", "Affordable everyday clothing for the modern family"),
    ("Sailor", "Casual and streetwear brand popular with young adults"),
    ("Ecstasy", "Contemporary fashion brand with bold designs"),
    ("Westecs", "Western-inspired clothing line with Bangladeshi craftsmanship"),
    ("Texmart", "Value fashion retailer with wide product range"),
]

CATEGORIES = [
    ("Men's Fashion", "Complete men's clothing and accessories collection"),
    ("Women's Fashion", "Stylish women's clothing and accessories"),
    ("Kids' Fashion", "Trendy and comfortable children's clothing"),
    ("Footwear", "Shoes, sandals, and boots for all occasions"),
    ("Accessories", "Bags, watches, belts, and fashion accessories"),
]

SUBCATEGORIES = {
    "Men's Fashion": [
        "Shirts", "T-Shirts", "Pants", "Jeans", "Jackets",
        "Suits & Blazers", "Kurta & Punjabi", "Activewear",
    ],
    "Women's Fashion": [
        "Tops & Blouses", "Dresses", "Saree", "Salwar Kameez",
        "Jeans & Pants", "Jackets & Coats",
    ],
    "Kids' Fashion": [
        "Boys Clothing", "Girls Clothing", "Baby Clothing",
    ],
    "Footwear": [
        "Formal Shoes", "Casual Shoes", "Sports Shoes", "Sandals",
    ],
    "Accessories": [
        "Bags & Backpacks", "Watches", "Belts", "Sunglasses",
    ],
}

SUPPLIERS = [
    ("Dhaka Garments Ltd", "supply@dhakagarments.com", "01711000001", "Uttara, Dhaka"),
    ("BD Fashion House", "info@bdfashion.com", "01711000002", "Gulshan, Dhaka"),
    ("Chittagong Textiles", "sales@ctgtextiles.com", "01711000003", "Agrabad, Chittagong"),
    ("Rajshahi Fabrics", "contact@rajfabrics.com", "01711000004", "Rajshahi City"),
    ("Sylhet Weavers Co", "hello@sylhetweavers.com", "01711000005", "Sylhet Sadar"),
]

COLORS = [
    ("Black", "#000000"), ("White", "#FFFFFF"), ("Navy Blue", "#1B2A4A"),
    ("Charcoal Grey", "#36454F"), ("Olive Green", "#556B2F"), ("Burgundy", "#800020"),
    ("Sky Blue", "#87CEEB"), ("Beige", "#F5F5DC"), ("Dark Brown", "#3B2F2F"),
    ("Coral Red", "#FF6F61"), ("Forest Green", "#228B22"), ("Slate Grey", "#708090"),
    ("Ivory", "#FFFFF0"), ("Teal", "#008080"), ("Maroon", "#800000"),
    ("Powder Blue", "#B0E0E6"), ("Khaki", "#C3B091"), ("Rust", "#B7410E"),
]

SIZES = {
    "clothing": [("XS", 0), ("S", 1), ("M", 2), ("L", 3), ("XL", 4), ("XXL", 5)],
    "pants": [("28", 0), ("30", 1), ("32", 2), ("34", 3), ("36", 4), ("38", 5)],
    "shoes": [("38", 0), ("39", 1), ("40", 2), ("41", 3), ("42", 4), ("43", 5), ("44", 6)],
    "accessories": [("One Size", 0)],
}

MATERIALS = [
    "100% Cotton", "Cotton Blend", "Premium Linen", "Polyester Mix",
    "Denim", "Silk Blend", "Organic Cotton", "Viscose",
    "Wool Blend", "Synthetic Leather", "Genuine Leather", "Canvas",
]

# ─── Product Templates ──────────────────────────────────────────────────────

PRODUCTS = [
    # Men's Shirts
    {"name": "Oxford Button-Down Shirt", "subcat": "Shirts", "brand": "Infinity", "price": 1890, "discount_price": 1590, "desc": "Classic oxford cotton shirt with button-down collar. Perfect for both office and casual occasions.", "short_desc": "Classic oxford cotton shirt", "tags": "formal,office,cotton", "sizes": "clothing", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Slim Fit Formal Shirt", "subcat": "Shirts", "brand": "Richman", "price": 2290, "discount_price": None, "desc": "Premium slim-fit formal shirt crafted from Egyptian cotton. Features French cuffs and a spread collar.", "short_desc": "Premium slim-fit formal shirt", "tags": "formal,premium,slim-fit", "sizes": "clothing", "featured": True, "trending": True, "new_arrival": False},
    {"name": "Printed Casual Shirt", "subcat": "Shirts", "brand": "Yellow", "price": 1490, "discount_price": 1190, "desc": "Vibrant printed casual shirt with tropical motifs. Lightweight fabric perfect for Bangladeshi summers.", "short_desc": "Vibrant tropical print casual shirt", "tags": "casual,printed,summer", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Linen Summer Shirt", "subcat": "Shirts", "brand": "Sailor", "price": 1690, "discount_price": None, "desc": "Breathable pure linen shirt designed for hot weather. Relaxed fit with rolled-up sleeve buttons.", "short_desc": "Breathable linen summer shirt", "tags": "linen,summer,casual", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Denim Western Shirt", "subcat": "Shirts", "brand": "Westecs", "price": 2090, "discount_price": 1790, "desc": "Rugged denim shirt with pearl snap buttons. Western-inspired design with dual chest pockets.", "short_desc": "Rugged denim western shirt", "tags": "denim,western,casual", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": False},

    # Men's T-Shirts
    {"name": "Essential Crew Neck Tee", "subcat": "T-Shirts", "brand": "Easy", "price": 690, "discount_price": 490, "desc": "Everyday essential crew neck t-shirt in premium combed cotton. Pre-shrunk with reinforced seams.", "short_desc": "Premium combed cotton crew neck", "tags": "basic,cotton,everyday", "sizes": "clothing", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Graphic Print T-Shirt", "subcat": "T-Shirts", "brand": "Yellow", "price": 890, "discount_price": None, "desc": "Bold graphic print t-shirt featuring urban art designs. Soft ring-spun cotton for all-day comfort.", "short_desc": "Bold urban graphic print tee", "tags": "graphic,urban,casual", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Polo Classic Fit", "subcat": "T-Shirts", "brand": "Infinity", "price": 1490, "discount_price": 1290, "desc": "Timeless polo shirt in piqué cotton. Features embroidered logo and ribbed collar for a polished look.", "short_desc": "Classic piqué cotton polo", "tags": "polo,classic,smart-casual", "sizes": "clothing", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Henley Long Sleeve", "subcat": "T-Shirts", "brand": "Sailor", "price": 990, "discount_price": None, "desc": "Comfortable henley with three-button placket. Brushed cotton interior for extra softness.", "short_desc": "Comfortable henley long sleeve", "tags": "henley,casual,layering", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "V-Neck Premium Tee", "subcat": "T-Shirts", "brand": "Texmart", "price": 590, "discount_price": 450, "desc": "Premium V-neck t-shirt in super-soft modal blend. Ideal for layering or wearing on its own.", "short_desc": "Super-soft modal V-neck tee", "tags": "v-neck,modal,layering", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": False},

    # Men's Pants & Jeans
    {"name": "Slim Fit Chinos", "subcat": "Pants", "brand": "Richman", "price": 2490, "discount_price": 1990, "desc": "Tailored slim-fit chinos in stretch twill. Features a flat front and tapered leg for a modern silhouette.", "short_desc": "Tailored stretch twill chinos", "tags": "chinos,slim-fit,office", "sizes": "pants", "featured": True, "trending": True, "new_arrival": False},
    {"name": "Skinny Stretch Jeans", "subcat": "Jeans", "brand": "Yellow", "price": 2290, "discount_price": None, "desc": "Modern skinny jeans with 2% elastane for maximum stretch. Dark indigo wash with whisker detailing.", "short_desc": "Dark indigo skinny stretch jeans", "tags": "jeans,skinny,stretch", "sizes": "pants", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Regular Fit Denim", "subcat": "Jeans", "brand": "Easy", "price": 1890, "discount_price": 1590, "desc": "Classic regular-fit jeans in mid-wash denim. Five-pocket styling with riveted stress points.", "short_desc": "Classic mid-wash regular jeans", "tags": "jeans,regular,classic", "sizes": "pants", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Cargo Jogger Pants", "subcat": "Pants", "brand": "Sailor", "price": 1790, "discount_price": None, "desc": "Utility-inspired cargo joggers with elasticated waist and cuffs. Multiple pocket design for functionality.", "short_desc": "Utility cargo jogger pants", "tags": "cargo,joggers,utility", "sizes": "pants", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Formal Wool Trousers", "subcat": "Pants", "brand": "Infinity", "price": 3290, "discount_price": 2890, "desc": "Impeccably tailored formal trousers in premium wool blend. Features a sharp crease and adjustable waistband.", "short_desc": "Premium wool formal trousers", "tags": "formal,wool,premium", "sizes": "pants", "featured": True, "trending": False, "new_arrival": False},

    # Men's Jackets
    {"name": "Leather Biker Jacket", "subcat": "Jackets", "brand": "Westecs", "price": 5990, "discount_price": 4990, "desc": "Genuine leather biker jacket with asymmetric zip closure. Quilted shoulders and snap-tab collar.", "short_desc": "Genuine leather biker jacket", "tags": "leather,biker,premium", "sizes": "clothing", "featured": True, "trending": True, "new_arrival": False},
    {"name": "Lightweight Bomber", "subcat": "Jackets", "brand": "Sailor", "price": 2990, "discount_price": None, "desc": "Classic bomber jacket in lightweight nylon. Features ribbed cuffs and collar with dual-zip design.", "short_desc": "Classic lightweight bomber jacket", "tags": "bomber,lightweight,casual", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Windbreaker Hooded", "subcat": "Jackets", "brand": "Ecstasy", "price": 2490, "discount_price": 1990, "desc": "Water-resistant windbreaker with adjustable hood. Packable design perfect for monsoon season.", "short_desc": "Water-resistant hooded windbreaker", "tags": "windbreaker,waterproof,monsoon", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},

    # Men's Suits & Blazers
    {"name": "Two-Piece Business Suit", "subcat": "Suits & Blazers", "brand": "Infinity", "price": 8990, "discount_price": 7490, "desc": "Impeccably tailored two-piece business suit in premium wool blend. Notch lapel with dual vents.", "short_desc": "Premium two-piece business suit", "tags": "suit,formal,business", "sizes": "clothing", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Casual Linen Blazer", "subcat": "Suits & Blazers", "brand": "Richman", "price": 4990, "discount_price": None, "desc": "Unstructured linen blazer for a relaxed yet sophisticated look. Patch pockets and half-canvas construction.", "short_desc": "Relaxed linen casual blazer", "tags": "blazer,linen,smart-casual", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},

    # Men's Kurta & Punjabi
    {"name": "Premium Cotton Punjabi", "subcat": "Kurta & Punjabi", "brand": "Infinity", "price": 3490, "discount_price": 2990, "desc": "Handcrafted premium cotton Punjabi with intricate embroidery. Perfect for Eid and festive occasions.", "short_desc": "Handcrafted embroidered Punjabi", "tags": "punjabi,festive,eid", "sizes": "clothing", "featured": True, "trending": True, "new_arrival": True},
    {"name": "Silk Kurta Set", "subcat": "Kurta & Punjabi", "brand": "Ecstasy", "price": 4290, "discount_price": None, "desc": "Luxurious silk kurta with matching bottom. Features delicate hand-embroidery and mandarin collar.", "short_desc": "Luxurious silk kurta set", "tags": "kurta,silk,luxury", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Casual Cotton Kurta", "subcat": "Kurta & Punjabi", "brand": "Easy", "price": 1490, "discount_price": 1190, "desc": "Comfortable everyday cotton kurta in earthy tones. Side slits and relaxed fit for all-day wear.", "short_desc": "Comfortable everyday cotton kurta", "tags": "kurta,cotton,casual", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": False},

    # Men's Activewear
    {"name": "Performance Training Tee", "subcat": "Activewear", "brand": "Ecstasy", "price": 1190, "discount_price": 890, "desc": "Moisture-wicking performance tee with mesh ventilation. Reflective logos for low-light visibility.", "short_desc": "Moisture-wicking training tee", "tags": "activewear,training,sport", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Track Pants Elite", "subcat": "Activewear", "brand": "Ecstasy", "price": 1590, "discount_price": None, "desc": "Premium track pants with zippered side pockets. Tapered leg with articulated knees for mobility.", "short_desc": "Premium tapered track pants", "tags": "activewear,track-pants,sport", "sizes": "pants", "featured": False, "trending": False, "new_arrival": True},

    # Women's Fashion
    {"name": "Floral Wrap Dress", "subcat": "Dresses", "brand": "Yellow", "price": 2690, "discount_price": 2190, "desc": "Elegant floral wrap dress in flowing chiffon. Adjustable wrap tie and flutter sleeves for a feminine silhouette.", "short_desc": "Elegant chiffon floral wrap dress", "tags": "dress,floral,chiffon", "sizes": "clothing", "featured": True, "trending": True, "new_arrival": True},
    {"name": "Banarasi Silk Saree", "subcat": "Saree", "brand": "Infinity", "price": 6990, "discount_price": 5990, "desc": "Exquisite Banarasi silk saree with gold zari work. Comes with matching blouse piece. Perfect for weddings.", "short_desc": "Exquisite Banarasi silk saree", "tags": "saree,silk,wedding", "sizes": "accessories", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Cotton Jamdani Saree", "subcat": "Saree", "brand": "Texmart", "price": 4490, "discount_price": 3790, "desc": "Authentic Jamdani saree handwoven by Bangladeshi artisans. Lightweight cotton with geometric motifs.", "short_desc": "Authentic handwoven Jamdani saree", "tags": "saree,jamdani,handloom", "sizes": "accessories", "featured": True, "trending": True, "new_arrival": False},
    {"name": "Designer Salwar Kameez", "subcat": "Salwar Kameez", "brand": "Ecstasy", "price": 3490, "discount_price": None, "desc": "Contemporary designer salwar kameez with digital prints. Three-piece set with dupatta in georgette.", "short_desc": "Contemporary digital print salwar", "tags": "salwar,designer,three-piece", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Embroidered Kameez", "subcat": "Salwar Kameez", "brand": "Infinity", "price": 2990, "discount_price": 2490, "desc": "Hand-embroidered kameez in premium lawn fabric. Intricate threadwork with mirror accents.", "short_desc": "Hand-embroidered lawn kameez", "tags": "kameez,embroidered,lawn", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Casual Blouse Top", "subcat": "Tops & Blouses", "brand": "Yellow", "price": 1290, "discount_price": 990, "desc": "Versatile casual blouse with puff sleeves and button-front closure. Perfect for brunch or office.", "short_desc": "Versatile puff-sleeve blouse", "tags": "blouse,casual,puff-sleeve", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Cropped Denim Jacket", "subcat": "Jackets & Coats", "brand": "Westecs", "price": 2790, "discount_price": 2290, "desc": "Cropped denim jacket with distressed detailing. Classic button-front with adjustable waist tabs.", "short_desc": "Cropped distressed denim jacket", "tags": "denim,jacket,cropped", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "High-Waist Wide Leg Pants", "subcat": "Jeans & Pants", "brand": "Sailor", "price": 1990, "discount_price": None, "desc": "Flattering high-waist wide-leg pants in premium stretch cotton. Zip fly with hook closure.", "short_desc": "High-waist wide-leg pants", "tags": "pants,wide-leg,high-waist", "sizes": "pants", "featured": False, "trending": False, "new_arrival": True},

    # Kids' Fashion
    {"name": "Boys Graphic Tee Pack", "subcat": "Boys Clothing", "brand": "Easy", "price": 990, "discount_price": 790, "desc": "Pack of 3 colorful graphic t-shirts for boys. Soft cotton with fun adventure-themed prints.", "short_desc": "3-pack boys graphic t-shirts", "tags": "kids,boys,t-shirt,pack", "sizes": "clothing", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Girls Floral Dress", "subcat": "Girls Clothing", "brand": "Yellow", "price": 1290, "discount_price": None, "desc": "Adorable floral dress with tiered skirt and puff sleeves. Made from soft organic cotton.", "short_desc": "Adorable floral tiered dress", "tags": "kids,girls,dress,floral", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Baby Romper Set", "subcat": "Baby Clothing", "brand": "Easy", "price": 790, "discount_price": 590, "desc": "Soft cotton romper set for babies. Snap closure for easy diaper changes. Includes matching hat.", "short_desc": "Soft cotton baby romper with hat", "tags": "baby,romper,cotton", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Boys Denim Shorts", "subcat": "Boys Clothing", "brand": "Sailor", "price": 890, "discount_price": None, "desc": "Durable denim shorts for active boys. Elastic waistband with drawstring for adjustable fit.", "short_desc": "Durable denim shorts for boys", "tags": "kids,boys,shorts,denim", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Girls Party Dress", "subcat": "Girls Clothing", "brand": "Ecstasy", "price": 1890, "discount_price": 1490, "desc": "Sparkly party dress with sequin bodice and tulle skirt. Perfect for birthday parties and celebrations.", "short_desc": "Sparkly sequin party dress", "tags": "kids,girls,party,sparkle", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},

    # Footwear
    {"name": "Classic Oxford Shoes", "subcat": "Formal Shoes", "brand": "Infinity", "price": 4990, "discount_price": 4290, "desc": "Handcrafted genuine leather Oxford shoes with Goodyear welted sole. Timeless formal footwear.", "short_desc": "Handcrafted leather Oxford shoes", "tags": "formal,leather,oxford", "sizes": "shoes", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Monk Strap Loafers", "subcat": "Formal Shoes", "brand": "Richman", "price": 3990, "discount_price": None, "desc": "Elegant double monk strap shoes in burnished leather. Cushioned insole for all-day comfort.", "short_desc": "Elegant double monk strap shoes", "tags": "formal,monk-strap,leather", "sizes": "shoes", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Canvas Sneakers", "subcat": "Casual Shoes", "brand": "Sailor", "price": 1490, "discount_price": 1190, "desc": "Classic canvas sneakers with vulcanized rubber sole. Lightweight and perfect for everyday wear.", "short_desc": "Classic canvas everyday sneakers", "tags": "sneakers,canvas,casual", "sizes": "shoes", "featured": True, "trending": True, "new_arrival": False},
    {"name": "Running Performance Shoes", "subcat": "Sports Shoes", "brand": "Ecstasy", "price": 3490, "discount_price": 2990, "desc": "High-performance running shoes with responsive foam midsole. Breathable mesh upper with heel counter.", "short_desc": "High-performance running shoes", "tags": "running,sport,performance", "sizes": "shoes", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Leather Comfort Sandals", "subcat": "Sandals", "brand": "Easy", "price": 1290, "discount_price": None, "desc": "Comfortable leather sandals with contoured footbed. Adjustable velcro straps for perfect fit.", "short_desc": "Comfortable leather sandals", "tags": "sandals,leather,comfort", "sizes": "shoes", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Suede Chelsea Boots", "subcat": "Casual Shoes", "brand": "Westecs", "price": 4490, "discount_price": 3790, "desc": "Premium suede Chelsea boots with elastic side panels. Stacked leather heel for a sophisticated look.", "short_desc": "Premium suede Chelsea boots", "tags": "boots,chelsea,suede", "sizes": "shoes", "featured": True, "trending": False, "new_arrival": True},

    # Accessories
    {"name": "Leather Messenger Bag", "subcat": "Bags & Backpacks", "brand": "Infinity", "price": 3990, "discount_price": 3290, "desc": "Full-grain leather messenger bag with brass hardware. Multiple compartments including padded laptop sleeve.", "short_desc": "Full-grain leather messenger bag", "tags": "bag,leather,laptop", "sizes": "accessories", "featured": True, "trending": True, "new_arrival": False},
    {"name": "Canvas Weekender Bag", "subcat": "Bags & Backpacks", "brand": "Sailor", "price": 2490, "discount_price": None, "desc": "Spacious canvas weekender with leather trim. Water-resistant base and detachable shoulder strap.", "short_desc": "Spacious canvas weekender bag", "tags": "bag,canvas,travel", "sizes": "accessories", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Urban Backpack", "subcat": "Bags & Backpacks", "brand": "Ecstasy", "price": 1990, "discount_price": 1590, "desc": "Minimalist urban backpack with hidden zip anti-theft pocket. Padded 15-inch laptop compartment.", "short_desc": "Minimalist anti-theft urban backpack", "tags": "backpack,urban,laptop", "sizes": "accessories", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Automatic Chronograph Watch", "subcat": "Watches", "brand": "Infinity", "price": 7990, "discount_price": 6490, "desc": "Japanese automatic movement chronograph with sapphire crystal. 100m water resistance on stainless steel bracelet.", "short_desc": "Japanese automatic chronograph watch", "tags": "watch,automatic,premium", "sizes": "accessories", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Minimalist Quartz Watch", "subcat": "Watches", "brand": "Richman", "price": 2990, "discount_price": None, "desc": "Clean minimalist design with Swiss quartz movement. Genuine leather strap with quick-release spring bars.", "short_desc": "Clean minimalist quartz watch", "tags": "watch,minimalist,quartz", "sizes": "accessories", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Italian Leather Belt", "subcat": "Belts", "brand": "Infinity", "price": 1490, "discount_price": 1190, "desc": "Premium Italian leather belt with brushed nickel buckle. Available in black and dark brown.", "short_desc": "Premium Italian leather belt", "tags": "belt,leather,italian", "sizes": "accessories", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Aviator Sunglasses", "subcat": "Sunglasses", "brand": "Westecs", "price": 1990, "discount_price": 1490, "desc": "Classic aviator sunglasses with polarized lenses. UV400 protection in lightweight metal frame.", "short_desc": "Polarized aviator sunglasses", "tags": "sunglasses,aviator,polarized", "sizes": "accessories", "featured": True, "trending": True, "new_arrival": False},

    # More variety products
    {"name": "Striped Rugby Polo", "subcat": "T-Shirts", "brand": "Sailor", "price": 1390, "discount_price": None, "desc": "Bold striped rugby polo in heavyweight cotton. Rubberized buttons and reinforced collar.", "short_desc": "Bold striped rugby polo", "tags": "polo,rugby,striped", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Stretch Slim Trousers", "subcat": "Pants", "brand": "Texmart", "price": 1690, "discount_price": 1390, "desc": "Comfortable stretch slim trousers for the modern professional. Wrinkle-resistant with permanent crease.", "short_desc": "Wrinkle-resistant stretch trousers", "tags": "trousers,slim,stretch", "sizes": "pants", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Quilted Puffer Vest", "subcat": "Jackets", "brand": "Ecstasy", "price": 2290, "discount_price": 1790, "desc": "Lightweight quilted puffer vest with synthetic down fill. Stand collar and zip front closure.", "short_desc": "Lightweight quilted puffer vest", "tags": "vest,puffer,layering", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Linen Drawstring Pants", "subcat": "Pants", "brand": "Easy", "price": 1390, "discount_price": None, "desc": "Relaxed linen drawstring pants for casual comfort. Side pockets with button closure for security.", "short_desc": "Relaxed linen drawstring pants", "tags": "linen,casual,relaxed", "sizes": "pants", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Floral Maxi Dress", "subcat": "Dresses", "brand": "Ecstasy", "price": 3290, "discount_price": 2790, "desc": "Stunning floral maxi dress with tiered ruffles. Adjustable spaghetti straps and smocked bodice.", "short_desc": "Stunning floral tiered maxi dress", "tags": "dress,maxi,floral", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Printed Lawn Three-Piece", "subcat": "Salwar Kameez", "brand": "Texmart", "price": 2490, "discount_price": 1990, "desc": "Digital printed lawn three-piece set. Includes embroidered kameez, printed trousers, and chiffon dupatta.", "short_desc": "Digital lawn three-piece set", "tags": "lawn,three-piece,printed", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": True},
    {"name": "Sports Training Hoodie", "subcat": "Activewear", "brand": "Ecstasy", "price": 1890, "discount_price": 1490, "desc": "Performance hoodie with kangaroo pocket and thumbhole cuffs. DryFit technology for sweat management.", "short_desc": "DryFit performance training hoodie", "tags": "hoodie,sport,dryfit", "sizes": "clothing", "featured": False, "trending": True, "new_arrival": True},
    {"name": "Kids School Uniform Polo", "subcat": "Boys Clothing", "brand": "Texmart", "price": 590, "discount_price": 490, "desc": "Durable school uniform polo in easy-care fabric. Reinforced stitching for active schoolyard play.", "short_desc": "Durable school uniform polo", "tags": "kids,school,uniform", "sizes": "clothing", "featured": False, "trending": False, "new_arrival": False},
    {"name": "Laptop Leather Briefcase", "subcat": "Bags & Backpacks", "brand": "Richman", "price": 5490, "discount_price": 4490, "desc": "Executive leather briefcase with expandable gusset. Fits up to 16-inch laptop with organized interior.", "short_desc": "Executive leather briefcase", "tags": "bag,briefcase,executive", "sizes": "accessories", "featured": True, "trending": False, "new_arrival": False},
    {"name": "Woven Fabric Belt", "subcat": "Belts", "brand": "Sailor", "price": 690, "discount_price": None, "desc": "Elastic woven belt with metal buckle. Stretchy design fits any waist size comfortably.", "short_desc": "Elastic woven fabric belt", "tags": "belt,woven,elastic", "sizes": "accessories", "featured": False, "trending": False, "new_arrival": True},
]


def _sql_str(val):
    """Escape a value for SQL insertion."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val).replace("'", "''")
    return f"'{s}'"


def _picsum_url(product_id: int, seed: int = 0) -> str:
    """Generate a deterministic picsum placeholder image URL."""
    return f"https://picsum.photos/seed/prod{product_id + seed}/600/800"


def generate():
    lines = ["-- FashionHub Seed Data (auto-generated by generate_seed.py)", "BEGIN;", ""]

    # ── Suppliers ─────────────────────────────────────────────
    lines.append("-- Suppliers")
    for i, (name, email, phone, addr) in enumerate(SUPPLIERS, 1):
        lines.append(
            f"INSERT INTO suppliers (id, name, contact_email, contact_phone, address, is_active) "
            f"VALUES ({i}, {_sql_str(name)}, {_sql_str(email)}, {_sql_str(phone)}, {_sql_str(addr)}, TRUE) "
            f"ON CONFLICT (id) DO NOTHING;"
        )
    lines.append(f"SELECT setval(pg_get_serial_sequence('suppliers', 'id'), {len(SUPPLIERS)}, true);")
    lines.append("")

    # ── Brands ────────────────────────────────────────────────
    lines.append("-- Brands")
    brand_map = {}
    for i, (name, desc) in enumerate(BRANDS, 1):
        brand_map[name] = i
        slug = name.lower().replace(" ", "-").replace("&", "and").replace("'", "")
        lines.append(
            f"INSERT INTO brands (id, name, slug, description, is_active) "
            f"VALUES ({i}, {_sql_str(name)}, {_sql_str(slug)}, {_sql_str(desc)}, TRUE) "
            f"ON CONFLICT (slug) DO NOTHING;"
        )
    lines.append(f"SELECT setval(pg_get_serial_sequence('brands', 'id'), {len(BRANDS)}, true);")
    lines.append("")

    # ── Categories ────────────────────────────────────────────
    lines.append("-- Categories")
    cat_map = {}
    for i, (name, desc) in enumerate(CATEGORIES, 1):
        cat_map[name] = i
        slug = name.lower().replace(" ", "-").replace("&", "and").replace("'", "")
        lines.append(
            f"INSERT INTO categories (id, name, slug, description, is_active) "
            f"VALUES ({i}, {_sql_str(name)}, {_sql_str(slug)}, {_sql_str(desc)}, TRUE) "
            f"ON CONFLICT (slug) DO NOTHING;"
        )
    lines.append(f"SELECT setval(pg_get_serial_sequence('categories', 'id'), {len(CATEGORIES)}, true);")
    lines.append("")

    # ── Subcategories ─────────────────────────────────────────
    lines.append("-- Subcategories")
    subcat_map = {}
    subcat_id = 1
    for cat_name, subcats in SUBCATEGORIES.items():
        for sc_name in subcats:
            subcat_map[sc_name] = subcat_id
            slug = sc_name.lower().replace(" ", "-").replace("&", "and").replace("'", "")
            lines.append(
                f"INSERT INTO subcategories (id, category_id, name, slug, is_active) "
                f"VALUES ({subcat_id}, {cat_map[cat_name]}, {_sql_str(sc_name)}, {_sql_str(slug)}, TRUE) "
                f"ON CONFLICT (slug) DO NOTHING;"
            )
            subcat_id += 1
    lines.append(f"SELECT setval(pg_get_serial_sequence('subcategories', 'id'), {subcat_id - 1}, true);")
    lines.append("")

    # ── Colors ────────────────────────────────────────────────
    lines.append("-- Colors")
    color_map = {}
    for i, (name, hex_code) in enumerate(COLORS, 1):
        color_map[name] = i
        lines.append(
            f"INSERT INTO colors (id, name, hex_code) "
            f"VALUES ({i}, {_sql_str(name)}, {_sql_str(hex_code)}) "
            f"ON CONFLICT (name) DO NOTHING;"
        )
    lines.append(f"SELECT setval(pg_get_serial_sequence('colors', 'id'), {len(COLORS)}, true);")
    lines.append("")

    # ── Sizes ─────────────────────────────────────────────────
    lines.append("-- Sizes")
    size_map = {}  # name -> id
    size_id = 1
    all_sizes_flat = set()
    for cat_key, group_sizes in SIZES.items():
        size_category = "clothing" if cat_key == "pants" else cat_key
        for name, _ in group_sizes:
            if name not in all_sizes_flat:
                all_sizes_flat.add(name)
                size_map[name] = size_id
                lines.append(
                    f"INSERT INTO sizes (id, name, size_category, sort_order) "
                    f"VALUES ({size_id}, {_sql_str(name)}, {_sql_str(size_category)}, {size_id}) "
                    f"ON CONFLICT (name, size_category) DO NOTHING;"
                )
                size_id += 1
    lines.append(f"SELECT setval(pg_get_serial_sequence('sizes', 'id'), {size_id - 1}, true);")
    lines.append("")

    # ── Materials ─────────────────────────────────────────────
    lines.append("-- Materials")
    material_map = {}
    for i, name in enumerate(MATERIALS, 1):
        material_map[name] = i
        lines.append(
            f"INSERT INTO materials (id, name) "
            f"VALUES ({i}, {_sql_str(name)}) "
            f"ON CONFLICT (name) DO NOTHING;"
        )
    lines.append(f"SELECT setval(pg_get_serial_sequence('materials', 'id'), {len(MATERIALS)}, true);")
    lines.append("")

    # ── Products ──────────────────────────────────────────────
    lines.append("-- Products")
    random.seed(42)
    variant_id = 1
    image_id = 1

    for prod_idx, p in enumerate(PRODUCTS, 1):
        brand_id = brand_map[p["brand"]]
        subcat_id_val = subcat_map[p["subcat"]]
        supplier_id = random.randint(1, len(SUPPLIERS))
        slug = f"{p['brand'].lower()}-{p['name'].lower().replace(' ', '-').replace('&', 'and')}-{prod_idx}"
        size_names = [s[0] for s in SIZES[p["sizes"]]]
        avail_sizes = ",".join(size_names)

        lines.append(
            f"INSERT INTO products (id, name, slug, description, short_description, base_price, discount_price, "
            f"brand_id, subcategory_id, supplier_id, is_active, is_featured, is_trending, is_new_arrival, "
            f"available_sizes, tags) "
            f"VALUES ({prod_idx}, {_sql_str(p['name'])}, {_sql_str(slug)}, "
            f"{_sql_str(p['desc'])}, {_sql_str(p['short_desc'])}, "
            f"{p['price']}, {_sql_str(p.get('discount_price'))}, "
            f"{brand_id}, {subcat_id_val}, {supplier_id}, TRUE, "
            f"{_sql_str(p['featured'])}, {_sql_str(p['trending'])}, {_sql_str(p['new_arrival'])}, "
            f"{_sql_str(avail_sizes)}, {_sql_str(p['tags'])}) "
            f"ON CONFLICT (id) DO NOTHING;"
        )

        # ── Product images (3 per product) ────────────────────
        for img_idx in range(3):
            url = _picsum_url(prod_idx, img_idx)
            is_primary = "TRUE" if img_idx == 0 else "FALSE"
            alt = f"{p['name']} - Image {img_idx + 1}"
            lines.append(
                f"INSERT INTO product_images (id, product_id, image_url, alt_text, is_primary, sort_order) "
                f"VALUES ({image_id}, {prod_idx}, {_sql_str(url)}, {_sql_str(alt)}, {is_primary}, {img_idx}) "
                f"ON CONFLICT (id) DO NOTHING;"
            )
            image_id += 1

        # ── Product variants (2-4 per product) ────────────────
        selected_colors = random.sample(list(color_map.keys()), min(3, len(color_map)))
        selected_sizes = size_names[:4]
        material = random.choice(MATERIALS)
        material_id = material_map[material]

        for color_name in selected_colors:
            for sz_name in selected_sizes:
                color_id = color_map[color_name]
                sz_id = size_map[sz_name]
                stock = random.randint(5, 60)
                variant_sku = f"{slug[:20]}-{color_name[:3].upper()}-{sz_name}".replace(" ", "")
                price_override = p["price"] if random.random() > 0.3 else None

                lines.append(
                    f"INSERT INTO product_variants (id, product_id, color_id, size_id, material_id, "
                    f"sku, price_override, is_active) "
                    f"VALUES ({variant_id}, {prod_idx}, {color_id}, {sz_id}, {material_id}, "
                    f"{_sql_str(variant_sku)}, {_sql_str(price_override)}, TRUE) "
                    f"ON CONFLICT (id) DO NOTHING;"
                )

                # Inventory for this variant
                lines.append(
                    f"INSERT INTO inventory (variant_id, current_stock, reserved_stock, reorder_level) "
                    f"VALUES ({variant_id}, {stock}, 0, 5) "
                    f"ON CONFLICT (variant_id) DO NOTHING;"
                )

                variant_id += 1

    lines.append(f"SELECT setval(pg_get_serial_sequence('products', 'id'), {len(PRODUCTS)}, true);")
    lines.append(f"SELECT setval(pg_get_serial_sequence('product_images', 'id'), {image_id - 1}, true);")
    lines.append(f"SELECT setval(pg_get_serial_sequence('product_variants', 'id'), {variant_id - 1}, true);")
    lines.append("")

    # ── Reviews (sample) ──────────────────────────────────────
    lines.append("-- Sample Reviews")
    review_comments = [
        "Excellent quality! The fabric is so soft and comfortable.",
        "Perfect fit, true to size. Very happy with my purchase.",
        "Great value for the price. Will definitely buy again.",
        "Beautiful color, exactly as shown in the picture.",
        "Good quality but the delivery took a bit long.",
        "My husband loves this. The stitching is impeccable.",
        "Amazing product! Got compliments everywhere I wore it.",
        "Comfortable for all-day wear. Highly recommend.",
        "The material is premium. Worth every taka.",
        "Nice design but runs slightly small. Order one size up.",
    ]
    review_id = 1
    for prod_idx in range(1, min(40, len(PRODUCTS) + 1)):
        num_reviews = random.randint(1, 4)
        # We need variant IDs — approximate: each product has ~12 variants,
        # so variant 1 for product 1 is at offset based on cumulative count.
        # Simplification: use a generated variant ID for the first variant of each product
        first_variant = sum(
            min(3, len(color_map)) * min(4, len(SIZES[PRODUCTS[i]["sizes"]]))
            for i in range(prod_idx - 1)
        ) + 1
        for _ in range(num_reviews):
            rating = random.choices([5, 4, 3, 4, 5], k=1)[0]
            comment = random.choice(review_comments)
            lines.append(
                f"INSERT INTO reviews (id, variant_id, rating, body) "
                f"VALUES ({review_id}, {first_variant}, {rating}, {_sql_str(comment)}) "
                f"ON CONFLICT (id) DO NOTHING;"
            )
            review_id += 1
    lines.append(f"SELECT setval(pg_get_serial_sequence('reviews', 'id'), {review_id - 1}, true);")
    lines.append("")

    lines.append("COMMIT;")
    lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Generated {len(PRODUCTS)} products with variants, images, and reviews")
    print(f"     Output: {OUTPUT}")


if __name__ == "__main__":
    generate()
