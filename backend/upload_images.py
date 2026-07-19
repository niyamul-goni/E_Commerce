import os, sys, urllib.parse
sys.path.append(os.getcwd())
from app.database import engine
from sqlalchemy import text

def run():
    with engine.connect() as conn:
        print("Uploading images for products and variants...")
        
        # 1. Products
        products = conn.execute(text("""
            SELECT p.id, p.name, c.name 
            FROM products p
            LEFT JOIN subcategories c ON p.subcategory_id = c.id
        """)).fetchall()
        
        for pid, pname, cname in products:
            keyword = urllib.parse.quote(cname.lower()) if cname else 'clothing'
            # Using loremflickr to get a realistic picture matching the product category
            img_url = f"https://loremflickr.com/800/800/{keyword}?lock={pid}"
            
            exists = conn.execute(text("SELECT id FROM product_images WHERE product_id = :pid AND is_primary = true"), {"pid": pid}).fetchone()
            if not exists:
                conn.execute(text("""
                    INSERT INTO product_images (product_id, image_url, is_primary, sort_order)
                    VALUES (:pid, :img_url, true, 0)
                """), {"pid": pid, "img_url": img_url})
            else:
                conn.execute(text("""
                    UPDATE product_images SET image_url = :img_url WHERE id = :id
                """), {"img_url": img_url, "id": exists[0]})
                
        # 2. Variants
        variants = conn.execute(text("""
            SELECT pv.id, p.name, c.name, cat.name
            FROM product_variants pv 
            JOIN products p ON p.id = pv.product_id
            LEFT JOIN colors c ON c.id = pv.color_id
            LEFT JOIN subcategories cat ON p.subcategory_id = cat.id
        """)).fetchall()
        
        for vid, pname, cname, catname in variants:
            keyword = urllib.parse.quote(catname.lower()) if catname else 'clothing'
            color = urllib.parse.quote(cname.lower()) if cname else ''
            
            search_query = f"{color},{keyword}" if color else keyword
            img_url = f"https://loremflickr.com/800/800/{search_query}?lock={vid}"
            
            conn.execute(text("UPDATE product_variants SET image_url=:url WHERE id=:id"), {"url": img_url, "id": vid})
            
        conn.commit()
        print(f"Updated images for {len(products)} products and {len(variants)} variants.")

if __name__ == '__main__':
    run()
