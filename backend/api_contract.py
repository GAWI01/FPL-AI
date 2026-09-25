from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable


SOURCE_CLASSES = frozenset({"live", "official", "model", "derived"})


def source_meta(
    source: str,
    fetched_at: datetime,
    *,
    stale: bool = False,
    version: str | None = None,
) -> dict[str, Any]:
    if source not in SOURCE_CLASSES:
        raise ValueError(f"Unsupported source class: {source}")

    if fetched_at.tzinfo is None:
        raise ValueError("fetched_at must be timezone-aware")

    return {
        "source": source,
        "fetched_at": fetched_at.astimezone(timezone.utc).isoformat(),
        "stale": stale,
        "version": version,
    }


def api_envelope(
    data: Any,
    meta: dict[str, Any],
    errors: Iterable[dict[str, str]] = (),
) -> dict[str, Any]:
    return {
        "data": data,
        "meta": meta,
        "errors": list(errors),
    }
