from __future__ import annotations
from typing import Any

def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

def choose_transfer_action(
    net_gain: float,
    gross_gain: float,
    transfers_used: int,
    *,
    horizon_gain: float = 0.0,
    confidence: float = 0.5,
    transfer_pressure: float = 0.0,
    hit_cost: float = 0.0,
) -> str:
    if transfers_used <= 0 or net_gain <= 0:
        return "HOLD"
    if hit_cost > 0 and net_gain < max(0.75, hit_cost * 0.75):
        return "HOLD"
    if horizon_gain < 0 and net_gain < 1.5:
        return "HOLD"
    if transfers_used > 1 or transfer_pressure >= 0.65:
        return "MULTI_TRANSFER"
    return "TRANSFER"

def confidence_score(
    *,
    decision_margin: float,
    minutes_certainty: float,
    fixture_certainty: float,
    signal_agreement: float,
) -> dict[str, Any]:
    vals = [_clip(x) for x in (decision_margin, minutes_certainty, fixture_certainty, signal_agreement)]
    score = sum(vals) / 4.0
    label = "HIGH" if score >= .75 else "MEDIUM" if score >= .50 else "LOW"
    return {
        "score": round(score, 3),
        "label": label,
        "components": {
            "decision_margin": round(vals[0], 3),
            "minutes_certainty": round(vals[1], 3),
            "fixture_certainty": round(vals[2], 3),
            "signal_agreement": round(vals[3], 3),
        },
    }

def transfer_pressure(current_player: dict[str, Any], horizon_player: dict[str, Any] | None) -> float:
    current_points = float(current_player.get("predicted_points", 0.0) or 0.0)
    future_points = float((horizon_player or {}).get("minutes_adjusted_points", 0.0) or 0.0)
    return _clip(max(0.0, future_points - current_points) / 8.0)

def chip_advisor(
    *,
    free_transfers: int,
    net_gain: float,
    squad_health_status: str,
    wildcard_available: bool = True,
    free_hit_available: bool = True,
    bench_boost_available: bool = True,
    triple_captain_available: bool = True,
    double_gameweek: bool = False,
    blank_gameweek: bool = False,
    wildcard_pressure: float = 0.0,
) -> dict[str, Any]:
    options = []
    if wildcard_available and (squad_health_status == "CRITICAL" or wildcard_pressure >= .75):
        options.append(("WILDCARD", .90 if squad_health_status == "CRITICAL" else .78))
    if free_hit_available and blank_gameweek:
        options.append(("FREE_HIT", .88))
    if bench_boost_available and double_gameweek:
        options.append(("BENCH_BOOST", .80))
    if triple_captain_available and double_gameweek and net_gain > 3:
        options.append(("TRIPLE_CAPTAIN", .72))
    options.sort(key=lambda x: (-x[1], x[0]))
    return {
        "recommended_chip": options[0][0] if options else None,
        "score": options[0][1] if options else 0.0,
        "alternatives": [{"chip": c, "score": s} for c, s in options[1:]],
    }
