"""Validate that live FPL player data belongs to the current FPL team pool.

This module deliberately separates historical ML data from current player
eligibility. Historical players must remain available to model training, while
live predictions and transfer candidates must be restricted to the current
FPL player/team universe.

The current-data pipeline may represent player teams either as FPL numeric
team IDs or as canonical team names. Both forms are supported.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class PlayerValidationError(ValueError):
    """Raised when current FPL player/team data cannot be validated."""


@dataclass(frozen=True)
class CurrentPlayerValidationResult:
    """Validation result for a current FPL player dataset."""

    valid_player_ids: set[int]
    invalid_player_ids: set[int]


def _require_columns(
    frame: pd.DataFrame,
    required: set[str],
    label: str,
) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise PlayerValidationError(
            f"{label} is missing required column(s): "
            + ", ".join(sorted(missing))
        )


def _normalise_ids(series: pd.Series, label: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise PlayerValidationError(
            f"{label} contains missing or non-numeric IDs"
        )
    return numeric.astype(int)


def _normalise_team_names(series: pd.Series, label: str) -> pd.Series:
    values = series.astype("string").str.strip()
    if values.isna().any() or (values == "").any():
        raise PlayerValidationError(
            f"{label} contains missing or empty team names"
        )
    return values


def validate_current_fpl_players(
    players: pd.DataFrame,
    teams: pd.DataFrame,
) -> CurrentPlayerValidationResult:
    """Validate players against the current FPL team universe.

    The player ``team`` column may contain either numeric FPL team IDs or
    current FPL team names. Availability status is intentionally ignored:
    injured/suspended players remain valid FPL players and are handled by the
    availability/xMins layer.
    """
    if not isinstance(players, pd.DataFrame):
        raise PlayerValidationError("players must be a pandas DataFrame")
    if not isinstance(teams, pd.DataFrame):
        raise PlayerValidationError("teams must be a pandas DataFrame")

    _require_columns(players, {"player_id", "team"}, "players")
    _require_columns(teams, {"id"}, "teams")

    player_ids = _normalise_ids(players["player_id"], "players.player_id")

    # Raw FPL data normally stores numeric team IDs. The canonical current
    # player table used by this project stores team names, so support both.
    player_team_numeric = pd.to_numeric(players["team"], errors="coerce")
    team_id_like = player_team_numeric.notna().all()

    if team_id_like:
        team_ids = player_team_numeric.astype(int)
        current_team_ids = set(_normalise_ids(teams["id"], "teams.id"))
        valid_mask = team_ids.isin(current_team_ids)
    else:
        _require_columns(teams, {"name"}, "teams")
        player_team_names = _normalise_team_names(
            players["team"],
            "players.team",
        )
        current_team_names = set(
            _normalise_team_names(
                teams["name"],
                "teams.name",
            ).tolist()
        )
        valid_mask = player_team_names.isin(current_team_names)

    return CurrentPlayerValidationResult(
        valid_player_ids=set(player_ids[valid_mask].tolist()),
        invalid_player_ids=set(player_ids[~valid_mask].tolist()),
    )


def filter_current_fpl_players(
    frame: pd.DataFrame,
    teams: pd.DataFrame,
    *,
    require_team_column: bool = True,
    player_pool: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return only rows belonging to the current FPL player universe.

    ``player_pool`` may be supplied when filtering a prediction table that
    does not itself contain team data. The pool is validated against the
    current FPL teams and its valid player IDs are used as the allow-list.
    """
    if not isinstance(frame, pd.DataFrame):
        raise PlayerValidationError("frame must be a pandas DataFrame")

    if "player_id" not in frame.columns:
        raise PlayerValidationError(
            "frame is missing required column(s): player_id"
        )

    if require_team_column and "team" not in frame.columns:
        raise PlayerValidationError(
            "frame is missing required column(s): team"
        )

    if player_pool is None:
        validation = validate_current_fpl_players(frame, teams)
        valid_ids = validation.valid_player_ids
    else:
        pool_validation = validate_current_fpl_players(player_pool, teams)
        valid_ids = pool_validation.valid_player_ids

    frame_ids = _normalise_ids(frame["player_id"], "frame.player_id")

    mask = frame_ids.isin(valid_ids)
    return frame.loc[mask].copy().reset_index(drop=True)
