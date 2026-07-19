from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def generate_order_number() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%y%m%d%H%M")
    return f"ORD-{timestamp}-{uuid4().hex[:4].upper()}"
