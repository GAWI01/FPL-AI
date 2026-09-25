from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from .api_contract import api_envelope


TeamReader = Callable[[int], dict[str, Any]]
TeamAreaReader = Callable[[int], dict[str, Any]]
PlayerReader = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class DashboardDependencies:
    team: TeamReader
    live: TeamAreaReader
    history: TeamAreaReader
    fixtures: TeamAreaReader
    players: PlayerReader
    decision: TeamAreaReader


_AREA_MESSAGES = {
    "live": "Live data is unavailable",
    "history": "Team history is unavailable",
    "fixtures": "Fixture data is unavailable",
    "players": "Player data is unavailable",
    "decision": "Decision data is unavailable",
}


def build_dashboard(
    team_id: int,
    dependencies: DashboardDependencies,
) -> dict[str, Any]:
    if not isinstance(team_id, int) or team_id <= 0:
        raise ValueError("team_id must be a positive integer")

    team = dependencies.team(team_id)
    data: dict[str, Any] = {"team": team}
    errors: list[dict[str, str]] = []

    readers: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
        ("live", lambda: dependencies.live(team_id)),
        ("history", lambda: dependencies.history(team_id)),
        ("fixtures", lambda: dependencies.fixtures(team_id)),
        ("players", dependencies.players),
        ("decision", lambda: dependencies.decision(team_id)),
    )

    for area, read in readers:
        try:
            data[area] = read()
        except Exception:
            data[area] = None
            errors.append({"area": area, "message": _AREA_MESSAGES[area]})

    generated_at = datetime.now(timezone.utc).isoformat()
    return api_envelope(
        data,
        {
            "event": team.get("event"),
            "generated_at": generated_at,
            "degraded": bool(errors),
        },
        errors,
    )
