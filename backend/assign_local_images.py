"""
Assign Local Images to Products
=================================
Scans backend/static/products/<product_folders>/ for image files
and updates the database so each product shows the image you placed.

Usage:
  1. Run: python setup_image_folders.py   (creates folders)
  2. Place your .jpg/.png/.webp images in the matching folders
  3. Run: python assign_local_images.py   (updates database)
"""
import os, sys
sys.path.append(os.getcwd())
from app.database import engine
from sqlalchemy import text

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def find_image_in_folder(folder_path: str):
    """Return the first image file found in a folder, or None."""
    if not os.path.isdir(folder_path):
        return None
    for fname in sorted(os.listdir(folder_path)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            return fname
    return None


def run():
    base_dir = os.path.join(os.path.dirname(__file__), "static", "products")

    if not os.path.isdir(base_dir):
        print("ERROR: static/products/ directory not found.")
        print("Run 'python setup_image_folders.py' first.")
        return

    with engine.connect() as conn:
        products = conn.execute(text("SELECT id, name FROM products ORDER BY id")).fetchall()

        updated = 0
        skipped = 0

        print(f"\n{'='*60}")
        print(f"  ASSIGNING LOCAL IMAGES TO PRODUCTS")
        print(f"{'='*60}\n")

        for pid, pname in products:
            # Find the matching folder (starts with the product ID)
            product_folder = None
            for dirname in sorted(os.listdir(base_dir)):
                full_path = os.path.join(base_dir, dirname)
                if os.path.isdir(full_path) and dirname.startswith(f"{pid:02d}_"):
                    product_folder = dirname
                    break

            if not product_folder:
                print(f"  [{pid:2d}] {pname} — ⚠ No folder found, skipped")
                skipped += 1
                continue

            folder_path = os.path.join(base_dir, product_folder)
            image_name = find_image_in_folder(folder_path)

            if not image_name:
                print(f"  [{pid:2d}] {pname} — ⚠ No image in folder, skipped")
                skipped += 1
                continue

            # The URL the frontend will use (served by FastAPI static mount)
            image_url = f"/static/products/{product_folder}/{image_name}"

            # Upsert into product_images table
            existing = conn.execute(
                text("SELECT id FROM product_images WHERE product_id = :pid AND is_primary = true"),
                {"pid": pid}
            ).fetchone()

            if existing:
                conn.execute(
                    text("UPDATE product_images SET image_url = :url WHERE id = :id"),
                    {"url": image_url, "id": existing[0]}
                )
            else:
                conn.execute(
                    text(
                        "INSERT INTO product_images (product_id, image_url, is_primary, sort_order) "
                        "VALUES (:pid, :url, true, 0)"
                    ),
                    {"pid": pid, "url": image_url}
                )

            updated += 1
            print(f"  [{pid:2d}] {pname} — ✔ {image_name}")

        conn.commit()

        print(f"\n{'='*60}")
        print(f"  ✔ Updated: {updated} products")
        print(f"  ⚠ Skipped: {skipped} products (no image found)")
        print(f"{'='*60}\n")


if __name__ == '__main__':
    run()
