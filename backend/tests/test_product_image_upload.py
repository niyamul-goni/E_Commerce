import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.routers import catalog


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeDatabase:
    def __init__(self, primary_image=None):
        self.primary_image = primary_image
        self.executed = []
        self.committed = False
        self.rolled_back = False

    def execute(self, statement, parameters):
        sql = str(statement)
        self.executed.append((sql, parameters))
        if "SELECT id, name FROM products" in sql:
            return _Result((7, "Test Shirt"))
        if "SELECT id, image_url FROM product_images" in sql:
            return _Result(self.primary_image)
        return _Result()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _upload(filename, content_type, content=b"not-empty"):
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


def test_upload_replaces_primary_and_removes_previous_local_file(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "_UPLOAD_DIR", tmp_path)
    previous = tmp_path / "7_previous.jpg"
    previous.write_bytes(b"previous")
    db = _FakeDatabase(primary_image=(11, "/static/products/7_previous.jpg"))

    result = asyncio.run(
        catalog.upload_product_image(
            product_id=7,
            file=_upload("shirt.jpg", "image/jpeg", b"new-image"),
            db=db,
        )
    )

    assert db.committed is True
    assert db.rolled_back is False
    assert result["product_id"] == 7
    assert result["image_url"].startswith("/static/products/7_")
    assert not previous.exists()
    assert len(list(tmp_path.glob("7_*.jpg"))) == 1
    assert any("UPDATE product_images" in sql for sql, _ in db.executed)


def test_upload_rejects_extension_content_type_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "_UPLOAD_DIR", tmp_path)
    db = _FakeDatabase()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            catalog.upload_product_image(
                product_id=7,
                file=_upload("shirt.jpg", "image/png"),
                db=db,
            )
        )

    assert exc_info.value.status_code == 400
    assert "does not match" in exc_info.value.detail
    assert db.committed is False
    assert list(tmp_path.iterdir()) == []
