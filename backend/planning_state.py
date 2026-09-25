from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_deadline(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def build_planning_state(
    bootstrap: dict[str, Any],
    *,
    prediction_event: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Resolve plan availability against the prediction target's deadline.

    The active/live event and the event a manager can transfer for are often
    different.  Action availability must therefore never be inferred from a
    live-score status flag.
    """
    if not isinstance(prediction_event, int) or prediction_event <= 0:
        raise ValueError("prediction_event must be a positive integer")
    events = bootstrap.get("events") if isinstance(bootstrap, dict) else None
    if not isinstance(events, list):
        raise ValueError("bootstrap events must be a list")

    valid_events = [item for item in events if isinstance(item, dict)]
    current = next((item for item in valid_events if item.get("is_current")), None)
    if current is None:
        current = max(
            (item for item in valid_events if item.get("finished") and item.get("id")),
            key=lambda item: int(item["id"]),
            default=None,
        )
    target = next(
        (item for item in valid_events if int(item.get("id", 0) or 0) == prediction_event),
        None,
    )
    deadline = _parse_deadline(target.get("deadline_time")) if target else None
    clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    return {
        "current_event": int(current["id"]) if current and current.get("id") else None,
        "prediction_event": prediction_event,
        "target_deadline_time": deadline.isoformat() if deadline else None,
        # Missing/invalid deadline metadata fails closed. Showing a plan is
        # safe; presenting it as currently actionable without a deadline is not.
        "actions_locked": deadline is None or clock >= deadline,
    }
