"""
Setup Product Image Folders
============================
Creates one folder per product inside backend/static/products/
so you know exactly where to place each product's image.

After placing images, run: python assign_local_images.py
"""
import os, sys, re
sys.path.append(os.getcwd())
from app.database import engine
from sqlalchemy import text


def sanitize(name: str) -> str:
    """Convert product name to a safe folder name."""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()


def run():
    with engine.connect() as conn:
        products = conn.execute(text("SELECT id, name FROM products ORDER BY id")).fetchall()

        base_dir = os.path.join(os.path.dirname(__file__), "static", "products")
        os.makedirs(base_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"  PRODUCT IMAGE FOLDERS")
        print(f"  Base path: {os.path.abspath(base_dir)}")
        print(f"{'='*60}\n")

        for pid, pname in products:
            folder_name = f"{pid:02d}_{sanitize(pname)}"
            folder_path = os.path.join(base_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            # Create a placeholder readme inside each folder
            readme_path = os.path.join(folder_path, "PUT_IMAGE_HERE.txt")
            if not os.path.exists(readme_path):
                with open(readme_path, "w") as f:
                    f.write(f"Place ONE image file here for: {pname}\n")
                    f.write(f"Supported formats: .jpg, .jpeg, .png, .gif, .webp\n")
                    f.write(f"Filename can be anything (e.g., product.jpg)\n")

            print(f"  [{pid:2d}] {folder_name}/")

        print(f"\n{'='*60}")
        print(f"  Total: {len(products)} folders created")
        print(f"\n  NEXT STEP: Place your product images in the folders above,")
        print(f"  then run:  python assign_local_images.py")
        print(f"{'='*60}\n")


if __name__ == '__main__':
    run()
