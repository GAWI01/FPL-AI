"""Leakage-safe feature engineering for FPL predictions."""

from __future__ import annotations

import pandas as pd


class FeatureEngineError(ValueError):
    """Raised when features cannot be built safely."""


REQUIRED_PLAYER_COLUMNS = {
    "player_id",
    "price",
    "position",
    "team",
}


CURRENT_SIGNAL_DEFAULTS = {
    "expected_goals": 0.0,
    "expected_assists": 0.0,
    "expected_goal_involvements": 0.0,
    "chance_of_playing_next_round": 100.0,
    "status": "a",
    "xmins": 0.0,
    "availability": "AVAILABLE",
    "start_probability": 0.0,
    "rotation_risk": "VERY_HIGH",
}


AVAILABILITY_MULTIPLIER = {
    "AVAILABLE": 1.0,
    "MINOR_RISK": 0.85,
    "RISK": 0.60,
    "UNAVAILABLE": 0.0,
}


ROTATION_RISK_MULTIPLIER = {
    "LOW": 1.00,
    "MEDIUM": 0.85,
    "HIGH": 0.65,
    "VERY_HIGH": 0.40,
    "OUT": 0.00,
}


HISTORY_ALIASES = {
    "minutes": ["minutes", "minutes_gw1"],
    "goals": ["goals", "goals_gw1"],
    "assists": ["assists", "assists_gw1"],
    "total_points": ["total_points", "total_points_gw1"],
    "started": ["started", "started_gw1"],
}


def _require_columns(
    frame: pd.DataFrame,
    required: set[str],
    frame_name: str,
) -> None:
    missing = required - set(frame.columns)

    if missing:
        raise FeatureEngineError(
            f"Missing {frame_name} column(s): "
            + ", ".join(sorted(missing))
        )


def _numeric(value: object, column: str) -> float:
    if pd.isna(value):
        raise FeatureEngineError(
            f"{column} contains a missing value"
        )

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise FeatureEngineError(
            f"{column} must be numeric"
        ) from exc


def _current_signal(
    player: pd.Series,
    column: str,
) -> object:
    if column not in player.index:
        return CURRENT_SIGNAL_DEFAULTS[column]

    value = player[column]

    if pd.isna(value):
        return CURRENT_SIGNAL_DEFAULTS[column]

    if column == "status":
        return str(value).strip().lower()

    if column == "availability":
        normalized = str(value).strip().upper()

        # Real FPL data uses categorical availability values.
        if normalized in AVAILABILITY_MULTIPLIER:
            return normalized

        # Test/legacy data may provide a numeric availability value.
        try:
            numeric = float(value)

            if 0.0 <= numeric <= 1.0:
                return numeric
        except (TypeError, ValueError):
            pass

        raise FeatureEngineError(
            f"Unknown availability value: {value}"
        )

    if column == "rotation_risk":
        normalized = str(value).strip().upper()

        if normalized in ROTATION_RISK_MULTIPLIER:
            return normalized

        try:
            numeric = float(value)

            if 0.0 <= numeric <= 1.0:
                return numeric
        except (TypeError, ValueError):
            pass

        raise FeatureEngineError(
            f"Unknown rotation_risk value: {value}"
        )

    return _numeric(value, column)


def _availability_multiplier(value: object) -> float:
    """Convert availability into a model-friendly multiplier."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)

        if 0.0 <= numeric <= 1.0:
            return numeric

        raise FeatureEngineError(
            f"availability numeric value must be between 0 and 1: {value}"
        )

    normalized = str(value).strip().upper()

    if normalized in AVAILABILITY_MULTIPLIER:
        return AVAILABILITY_MULTIPLIER[normalized]

    try:
        numeric = float(normalized)

        if 0.0 <= numeric <= 1.0:
            return numeric
    except (TypeError, ValueError):
        pass

    raise FeatureEngineError(
        f"Unknown availability value: {value}"
    )


def _rotation_multiplier(value: object) -> float:
    """Convert rotation risk into a model-friendly multiplier."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)

        if 0.0 <= numeric <= 1.0:
            return numeric

        raise FeatureEngineError(
            f"rotation_risk numeric value must be between 0 and 1: {value}"
        )

    normalized = str(value).strip().upper()

    if normalized in ROTATION_RISK_MULTIPLIER:
        return ROTATION_RISK_MULTIPLIER[normalized]

    try:
        numeric = float(normalized)

        if 0.0 <= numeric <= 1.0:
            return numeric
    except (TypeError, ValueError):
        pass

    raise FeatureEngineError(
        f"Unknown rotation_risk value: {value}"
    )


def _normalise_history(history: pd.DataFrame) -> pd.DataFrame:
    """Convert supported history formats into one canonical schema."""

    result = history.copy()

    if "event" not in result.columns:
        result["event"] = 1

    for canonical, aliases in HISTORY_ALIASES.items():
        if canonical in result.columns:
            continue

        source = next(
            (
                column
                for column in aliases
                if column in result.columns
            ),
            None,
        )

        if source is None:
            raise FeatureEngineError(
                f"Missing history column for '{canonical}'"
            )

        result[canonical] = result[source]

    return result


def build_features(
    players: pd.DataFrame,
    history: pd.DataFrame,
    target_gw: int,
) -> pd.DataFrame:
    """Build player features using only information before target_gw."""

    if not isinstance(target_gw, int) or target_gw < 1:
        raise FeatureEngineError("target_gw must be >= 1")

    _require_columns(
        players,
        REQUIRED_PLAYER_COLUMNS,
        "players",
    )

    history = _normalise_history(history)

    historical = history.copy()

    historical["event"] = pd.to_numeric(
        historical["event"],
        errors="coerce",
    )

    if historical["event"].isna().any():
        raise FeatureEngineError(
            "history.event contains invalid values"
        )

    # Critical leakage barrier:
    # Prediction for GW N may only use information from GW < N.
    historical = historical.loc[
        historical["event"] < target_gw
    ].copy()

    if historical.empty:
        raise FeatureEngineError(
            f"No historical data available before GW{target_gw}"
        )

    historical = historical.sort_values(
        ["player_id", "event"]
    )

    # Keep the five most recent historical gameweeks.
    historical = (
        historical
        .groupby("player_id", group_keys=False)
        .tail(5)
    )

    rows: list[dict[str, object]] = []

    for _, player in players.iterrows():
        player_id = player["player_id"]

        player_history = historical.loc[
            historical["player_id"] == player_id
        ]

        if player_history.empty:
            raise FeatureEngineError(
                f"No historical data available for player {player_id}"
            )

        availability = _current_signal(
            player,
            "availability",
        )

        rotation_risk = _current_signal(
            player,
            "rotation_risk",
        )

        rows.append(
            {
                "player_id": player_id,
                "price": _numeric(
                    player["price"],
                    "price",
                ),
                "position": str(player["position"]),
                "team": player["team"],

                # Historical performance
                "points_last_5": float(
                    pd.to_numeric(
                        player_history["total_points"],
                        errors="coerce",
                    ).sum()
                ),
                "minutes_last_5": float(
                    pd.to_numeric(
                        player_history["minutes"],
                        errors="coerce",
                    ).sum()
                ),
                "starts_last_5": float(
                    pd.to_numeric(
                        player_history["started"],
                        errors="coerce",
                    ).sum()
                ),
                "goals_last_5": float(
                    pd.to_numeric(
                        player_history["goals"],
                        errors="coerce",
                    ).sum()
                ),
                "assists_last_5": float(
                    pd.to_numeric(
                        player_history["assists"],
                        errors="coerce",
                    ).sum()
                ),

                # Current player signals
                "expected_goals": _current_signal(
                    player,
                    "expected_goals",
                ),
                "expected_assists": _current_signal(
                    player,
                    "expected_assists",
                ),
                "expected_goal_involvements": _current_signal(
                    player,
                    "expected_goal_involvements",
                ),

                "chance_of_playing_next_round": _current_signal(
                    player,
                    "chance_of_playing_next_round",
                ),
                "status": _current_signal(
                    player,
                    "status",
                ),

                # Minutes / availability
                "xmins": _current_signal(
                    player,
                    "xmins",
                ),
                "availability": availability,
                "availability_multiplier": _availability_multiplier(
                    availability
                ),
                "start_probability": _current_signal(
                    player,
                    "start_probability",
                ),
                "rotation_risk": rotation_risk,
                "rotation_risk_multiplier": _rotation_multiplier(
                    rotation_risk
                ),
            }
        )

    return pd.DataFrame(rows)