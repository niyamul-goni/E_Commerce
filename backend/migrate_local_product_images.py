"""Migrate legacy local product uploads to shared Supabase Storage.

Run this on the computer that contains the original files in
backend/static/products. The default mode is read-only. Pass --apply only after
reviewing the dry-run summary.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text

from app.core.config import settings
from app.core.product_image_storage import (
    ProductImageStorageError,
    delete_managed_product_image,
    store_product_image,
)
from app.database import SessionLocal


UPLOAD_DIR = Path(__file__).resolve().parent / "static" / "products"
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


@dataclass(frozen=True)
class LegacyImage:
    image_id: int
    product_id: int
    image_url: str
    file_path: Path


def load_legacy_images() -> tuple[list[LegacyImage], list[LegacyImage]]:
    with SessionLocal() as db:
        rows = db.execute(
            text(
                "SELECT id, product_id, image_url "
                "FROM product_images "
                "WHERE image_url LIKE '/static/products/%' "
                "ORDER BY product_id, id"
            )
        ).fetchall()

    found: list[LegacyImage] = []
    missing: list[LegacyImage] = []
    for row in rows:
        image = LegacyImage(
            image_id=row[0],
            product_id=row[1],
            image_url=row[2],
            file_path=UPLOAD_DIR / Path(row[2]).name,
        )
        (found if image.file_path.is_file() else missing).append(image)
    return found, missing


async def migrate(found: list[LegacyImage]) -> tuple[int, int]:
    migrated = 0
    failed = 0

    for image in found:
        extension = image.file_path.suffix.lower()
        content_type = CONTENT_TYPES.get(extension)
        if not content_type:
            print(f"SKIP product {image.product_id}: unsupported {extension}")
            failed += 1
            continue

        new_url: str | None = None
        try:
            new_url = await store_product_image(
                product_id=image.product_id,
                extension=extension,
                content=image.file_path.read_bytes(),
                content_type=content_type,
                local_dir=UPLOAD_DIR,
            )

            with SessionLocal() as db:
                result = db.execute(
                    text(
                        "UPDATE product_images SET image_url = :new_url "
                        "WHERE id = :image_id AND image_url = :old_url"
                    ),
                    {
                        "new_url": new_url,
                        "image_id": image.image_id,
                        "old_url": image.image_url,
                    },
                )
                if result.rowcount != 1:
                    db.rollback()
                    raise RuntimeError(
                        "the database image changed after the migration scan"
                    )
                db.commit()

            migrated += 1
            print(f"OK   product {image.product_id}: {image.file_path.name}")
        except Exception as exc:
            failed += 1
            if new_url:
                await delete_managed_product_image(new_url, local_dir=UPLOAD_DIR)
            print(f"FAIL product {image.product_id}: {exc}")

    return migrated, failed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move legacy local product images to shared Supabase Storage."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upload found files and update their matching product_images rows.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="List missing filenames in addition to the summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    found, missing = load_legacy_images()

    print(f"Legacy database paths: {len(found) + len(missing)}")
    print(f"Files found on this computer: {len(found)}")
    print(f"Files missing on this computer: {len(missing)}")

    if args.verbose:
        for image in missing:
            print(f"MISSING product {image.product_id}: {image.file_path.name}")

    if not args.apply:
        print("Dry run only. Re-run with --apply on the computer holding the files.")
        return 0

    if settings.PRODUCT_IMAGE_STORAGE == "local":
        raise ProductImageStorageError(
            "Set PRODUCT_IMAGE_STORAGE=auto or supabase before applying migration."
        )
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ProductImageStorageError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required."
        )

    migrated, failed = asyncio.run(migrate(found))
    print(f"Migration complete: {migrated} migrated, {failed} failed.")
    print("Original local files were preserved.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
