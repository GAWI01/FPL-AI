from __future__ import annotations

from typing import Any

import pandas as pd


class TeamIdError(ValueError):
    """Raised when an FPL Team ID is invalid."""


def normalize_team_id(value: Any) -> int:
    """Convert a user-provided Team ID into a positive integer."""

    if value is None:
        raise TeamIdError(
            "Team ID must be a positive integer"
        )

    if isinstance(value, bool):
        raise TeamIdError(
            "Team ID must be a positive integer"
        )

    if isinstance(value, int):
        team_id = value

    elif isinstance(value, str):
        value = value.strip()

        if not value:
            raise TeamIdError(
                "Team ID cannot be empty"
            )

        if not value.isdigit():
            raise TeamIdError(
                "Team ID must contain only numbers"
            )

        team_id = int(value)

    else:
        raise TeamIdError(
            "Team ID must be a positive integer"
        )

    if team_id <= 0:
        raise TeamIdError(
            "Team ID must be a positive integer"
        )

    return team_id


def merge_team_with_predictions(
    team: dict,
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Merge an imported FPL team with player prediction data."""

    if not isinstance(team, dict):
        raise ValueError(
            "team must be a dictionary"
        )

    if not isinstance(predictions, pd.DataFrame):
        raise ValueError(
            "predictions must be a pandas DataFrame"
        )

    if "picks" not in team:
        raise ValueError(
            "team is missing picks"
        )

    picks = team["picks"]

    if not isinstance(picks, list):
        raise ValueError(
            "team picks must be a list"
        )

    prediction_columns = set(
        predictions.columns
    )

    if "player_id" not in prediction_columns:
        raise ValueError(
            "predictions is missing player_id"
        )

    rows = []

    for pick in picks:

        if not isinstance(pick, dict):
            raise ValueError(
                "team pick must be a dictionary"
            )

        if "player_id" not in pick:
            raise ValueError(
                "team pick is missing player_id"
            )

        row = {
            "player_id": pick["player_id"],
            "position": pick.get("position"),
            "multiplier": pick.get("multiplier"),
        }

        rows.append(row)

    team_picks = pd.DataFrame(rows)

    if team_picks.empty:
        return team_picks

    prediction_data = predictions.copy()

    prediction_data = prediction_data.drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    result = team_picks.merge(
        prediction_data,
        on="player_id",
        how="left",
        suffixes=("_team", ""),
    )

    if "position_team" in result.columns:

        if "position" not in result.columns:

            result["position"] = (
                result["position_team"]
            )

        else:

            result["position"] = (
                result["position"]
                .fillna(
                    result["position_team"]
                )
            )

        result = result.drop(
            columns=["position_team"]
        )

    return result


def _is_starter(pick: dict) -> bool:
    """
    Determine whether an FPL pick belongs to the starting XI.

    FPL position values are:
        1 = goalkeeper
        2 = defender
        3 = midfielder
        4 = forward

    The normal public FPL team response uses multiplier 0
    for bench players and a positive multiplier for starters.
    """

    multiplier = pick.get(
        "multiplier",
        1,
    )

    try:
        return int(multiplier) > 0

    except (
        TypeError,
        ValueError,
    ):
        return True


def _position_sort_key(pick: dict) -> tuple[int, int]:
    """Return a stable FPL position ordering key."""

    position_order = {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
    }

    position = pick.get(
        "position"
    )

    try:
        normalized_position = int(
            position
        )

    except (
        TypeError,
        ValueError,
    ):
        normalized_position = 99

    return (
        position_order.get(
            normalized_position,
            99,
        ),
        int(
            pick.get(
                "_original_index",
                0,
            )
        ),
    )


def prepare_team_selection(
    team: dict,
) -> dict:
    """
    Split an FPL team into starting XI and bench.

    Returns:
        {
            "starting_xi": [...],
            "bench": [...],
            "captain_id": ...,
            "vice_captain_id": ...,
        }

    The function deliberately keeps the original pick dictionaries
    intact so downstream code can still access all FPL pick fields.
    """

    if not isinstance(team, dict):
        raise ValueError(
            "team must be a dictionary"
        )

    picks = team.get(
        "picks",
        []
    )

    if not isinstance(picks, list):
        raise ValueError(
            "team picks must be a list"
        )

    normalized_picks = []

    for index, pick in enumerate(picks):

        if not isinstance(pick, dict):
            raise ValueError(
                "team pick must be a dictionary"
            )

        if "player_id" not in pick:
            raise ValueError(
                "team pick is missing player_id"
            )

        normalized_pick = dict(
            pick
        )

        normalized_pick[
            "_original_index"
        ] = index

        normalized_picks.append(
            normalized_pick
        )

    starting_xi = [
        pick
        for pick in normalized_picks
        if _is_starter(pick)
    ]

    bench = [
        pick
        for pick in normalized_picks
        if not _is_starter(pick)
    ]

    starting_xi.sort(
        key=_position_sort_key
    )

    bench.sort(
        key=_position_sort_key
    )

    captain_id = None

    for pick in normalized_picks:

        try:
            multiplier = int(
                pick.get(
                    "multiplier",
                    1,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            multiplier = 1

        if multiplier == 2:

            captain_id = pick[
                "player_id"
            ]

            break

    vice_captain_id = team.get(
        "vice_captain"
    )

    if vice_captain_id is not None:

        try:
            vice_captain_id = int(
                vice_captain_id
            )

        except (
            TypeError,
            ValueError,
        ):
            pass

    # Remove our internal ordering field before returning
    # the original FPL pick shape.
    for pick in (
        starting_xi + bench
    ):
        pick.pop(
            "_original_index",
            None,
        )

    return {
        "starting_xi": starting_xi,
        "bench": bench,
        "captain_id": captain_id,
        "vice_captain_id": vice_captain_id,
    }