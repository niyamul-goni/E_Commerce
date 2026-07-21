#!/usr/bin/env python3
"""
sync_products.py — Ensures data integrity between products, variants, inventory, and images.

Checks:
  1. All products have at least one variant
  2. All variants have inventory rows
  3. All products have at least one image
  4. Creates missing relationships with sensible defaults

Usage:
    python sync_products.py [--fix]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text
from app.database import SessionLocal


def sync(fix: bool = False):
    db = SessionLocal()
    try:
        issues = 0

        # 1. Products without variants
        rows = db.execute(text("""
            SELECT p.id, p.name
            FROM products p
            WHERE NOT EXISTS (
                SELECT 1 FROM product_variants pv WHERE pv.product_id = p.id
            )
        """)).fetchall()
        if rows:
            print(f"\n[WARN] {len(rows)} products without variants:")
            for r in rows:
                print(f"  - Product {r[0]}: {r[1]}")
                issues += 1
                if fix:
                    # Create a default variant
                    db.execute(text("""
                        INSERT INTO product_variants (product_id, sku, is_active)
                        VALUES (:pid, :sku, TRUE)
                        ON CONFLICT DO NOTHING
                    """), {"pid": r[0], "sku": f"default-{r[0]}"})
                    print(f"    -> Created default variant")

        # 2. Variants without inventory
        rows = db.execute(text("""
            SELECT pv.id, pv.sku, p.name
            FROM product_variants pv
            JOIN products p ON p.id = pv.product_id
            WHERE NOT EXISTS (
                SELECT 1 FROM inventory inv WHERE inv.variant_id = pv.id
            )
        """)).fetchall()
        if rows:
            print(f"\n[WARN] {len(rows)} variants without inventory:")
            for r in rows[:10]:
                print(f"  - Variant {r[0]} ({r[1]}): {r[2]}")
                issues += 1
                if fix:
                    db.execute(text("""
                        INSERT INTO inventory (variant_id, current_stock, reserved_stock, reorder_level)
                        VALUES (:vid, 25, 0, 5)
                        ON CONFLICT (variant_id) DO NOTHING
                    """), {"vid": r[0]})
            if len(rows) > 10:
                print(f"  ... and {len(rows) - 10} more")
            if fix:
                print(f"    -> Created inventory for {len(rows)} variants")

        # 3. Products without images
        rows = db.execute(text("""
            SELECT p.id, p.name
            FROM products p
            WHERE NOT EXISTS (
                SELECT 1 FROM product_images pi WHERE pi.product_id = p.id
            )
        """)).fetchall()
        if rows:
            print(f"\n[WARN] {len(rows)} products without images:")
            for r in rows:
                print(f"  - Product {r[0]}: {r[1]}")
                issues += 1
                if fix:
                    url = f"https://picsum.photos/seed/prod{r[0]}/600/800"
                    db.execute(text("""
                        INSERT INTO product_images (product_id, image_url, alt_text, is_primary, sort_order)
                        VALUES (:pid, :url, :alt, TRUE, 0)
                        ON CONFLICT DO NOTHING
                    """), {"pid": r[0], "url": url, "alt": f"{r[1]} image"})
                    print(f"    -> Created placeholder image")

        if fix:
            db.commit()
            print(f"\n[OK] Fixed {issues} issues")
        elif issues:
            print(f"\n[INFO] Found {issues} issues. Run with --fix to resolve.")
        else:
            print("\n[OK] All products are properly synced (variants, inventory, images)")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync product data integrity")
    parser.add_argument("--fix", action="store_true", help="Auto-fix missing data")
    args = parser.parse_args()
    sync(fix=args.fix)
