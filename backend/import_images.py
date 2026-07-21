#!/usr/bin/env python3
"""
import_images.py — Scans a local directory for product images and inserts
them into the product_images table in the Supabase database.

Usage:
    python import_images.py [--dir path/to/images]

By default, scans `static/products/` for files named like:
    <product_id>_<anything>.jpg
    <sku>_<anything>.png
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session

# Allow running from backend/ directory
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal


DEFAULT_DIR = Path(__file__).resolve().parent / "static" / "products"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _find_product_id(filename: str, db: Session) -> int | None:
    """Try to resolve a filename to a product_id."""
    stem = Path(filename).stem.lower()

    # Pattern: <product_id>_<anything>
    match = re.match(r"^(\d+)_", stem)
    if match:
        pid = int(match.group(1))
        exists = db.execute(text("SELECT id FROM products WHERE id = :pid"), {"pid": pid}).fetchone()
        return pid if exists else None

    # Pattern: <sku>_<anything>  (slug match)
    slug_part = stem.split("_")[0] if "_" in stem else stem
    row = db.execute(
        text("SELECT id FROM products WHERE slug ILIKE :pattern LIMIT 1"),
        {"pattern": f"%{slug_part}%"},
    ).fetchone()
    return row[0] if row else None


def import_images(image_dir: Path):
    db = SessionLocal()
    try:
        files = sorted(
            f for f in image_dir.iterdir()
            if f.is_file() and f.suffix.lower() in EXTENSIONS
        )
        if not files:
            print(f"No image files found in {image_dir}")
            return

        inserted = 0
        skipped = 0
        for f in files:
            product_id = _find_product_id(f.name, db)
            if product_id is None:
                print(f"  SKIP: {f.name} (no matching product)")
                skipped += 1
                continue

            image_url = f"/static/products/{f.name}"

            # Check if already exists
            existing = db.execute(
                text("SELECT id FROM product_images WHERE image_url = :url"),
                {"url": image_url},
            ).fetchone()
            if existing:
                skipped += 1
                continue

            # Get sort order
            max_sort = db.execute(
                text("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM product_images WHERE product_id = :pid"),
                {"pid": product_id},
            ).scalar()

            # Check if product has a primary image
            has_primary = db.execute(
                text("SELECT id FROM product_images WHERE product_id = :pid AND is_primary = true"),
                {"pid": product_id},
            ).fetchone()

            db.execute(text(
                "INSERT INTO product_images (product_id, image_url, alt_text, is_primary, sort_order) "
                "VALUES (:pid, :url, :alt, :primary, :sort)"
            ), {
                "pid": product_id,
                "url": image_url,
                "alt": f"Product {product_id} image",
                "primary": not has_primary,
                "sort": max_sort,
            })
            inserted += 1

        db.commit()
        print(f"[OK] Imported {inserted} images, skipped {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import product images from a directory")
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="Directory to scan")
    args = parser.parse_args()
    import_images(Path(args.dir))
