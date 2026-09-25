from __future__ import annotations

from typing import Any

import pandas as pd


class TransferInAnalysisError(ValueError):
    """Raised when transfer-in analysis cannot be performed."""


REQUIRED_COLUMNS = {
    "player_id",
    "name",
    "position",
    "price",
    "predicted_points",
}


def analyze_transfer_in(
    team: dict[str, Any],
    predictions: pd.DataFrame,
    player_out_id: int | None = None,
    budget: float | None = None,
) -> pd.DataFrame:
    """Rank transfer-in candidates for a player's position.

    Candidates must:
    - not already be in the user's team
    - match the outgoing player's prediction position
    - fit the supplied budget when one is supplied

    Candidates are ranked using transfer gain, predicted points,
    and points per million.
    """

    if not isinstance(team, dict):
        raise TransferInAnalysisError(
            "team must be a dictionary"
        )

    if not isinstance(predictions, pd.DataFrame):
        raise TransferInAnalysisError(
            "predictions must be a pandas DataFrame"
        )

    if "picks" not in team:
        raise TransferInAnalysisError(
            "team is missing picks"
        )

    missing = REQUIRED_COLUMNS - set(predictions.columns)

    if missing:
        raise TransferInAnalysisError(
            "predictions is missing columns: "
            + ", ".join(sorted(missing))
        )

    picks = team["picks"]

    if not isinstance(picks, list):
        raise TransferInAnalysisError(
            "team picks must be a list"
        )

    owned_ids: set[Any] = set()

    for pick in picks:
        if not isinstance(pick, dict):
            raise TransferInAnalysisError(
                "team pick must be a dictionary"
            )

        if "player_id" not in pick:
            raise TransferInAnalysisError(
                "team pick is missing player_id"
            )

        owned_ids.add(pick["player_id"])

    outgoing_position = None

    if player_out_id is not None:
        outgoing_rows = predictions[
            predictions["player_id"] == player_out_id
        ]

        if outgoing_rows.empty:
            raise TransferInAnalysisError(
                f"player {player_out_id} is not in the team"
            )

        outgoing_position = outgoing_rows.iloc[0]["position"]

    if budget is not None:
        try:
            budget = float(budget)
        except (TypeError, ValueError) as exc:
            raise TransferInAnalysisError(
                "budget must be a number"
            ) from exc

        if budget < 0:
            raise TransferInAnalysisError(
                "budget cannot be negative"
            )

    result = predictions.copy()

    result["price"] = pd.to_numeric(
        result["price"],
        errors="coerce",
    )

    result["predicted_points"] = pd.to_numeric(
        result["predicted_points"],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            "price",
            "predicted_points",
        ]
    ).copy()

    result = result[
        result["price"] > 0
    ].copy()

    # Never recommend a player already owned.
    result = result[
        ~result["player_id"].isin(owned_ids)
    ].copy()

    # Match the actual football position from predictions.
    if outgoing_position is not None:
        result = result[
            result["position"].astype(str).str.upper()
            == str(outgoing_position).upper()
        ].copy()

    if budget is not None:
        result = result[
            result["price"] <= budget
        ].copy()

    columns = [
        "player_id",
        "name",
        "position",
        "price",
        "predicted_points",
        "points_per_million",
        "transfer_gain",
        "transfer_score",
    ]

    if result.empty:
        return pd.DataFrame(
            columns=columns
        )

    result["points_per_million"] = (
        result["predicted_points"]
        / result["price"]
    )

    baseline = 0.0

    if player_out_id is not None:
        outgoing = predictions[
            predictions["player_id"] == player_out_id
        ].copy()

        if not outgoing.empty:
            outgoing_points = pd.to_numeric(
                outgoing["predicted_points"],
                errors="coerce",
            ).dropna()

            if not outgoing_points.empty:
                baseline = float(
                    outgoing_points.iloc[0]
                )

    result["transfer_gain"] = (
        result["predicted_points"]
        - baseline
    )

    points_min = result["predicted_points"].min()
    points_max = result["predicted_points"].max()

    value_min = result["points_per_million"].min()
    value_max = result["points_per_million"].max()

    if points_max == points_min:
        points_score = pd.Series(
            1.0,
            index=result.index,
        )
    else:
        points_score = (
            result["predicted_points"]
            - points_min
        ) / (
            points_max
            - points_min
        )

    if value_max == value_min:
        value_score = pd.Series(
            1.0,
            index=result.index,
        )
    else:
        value_score = (
            result["points_per_million"]
            - value_min
        ) / (
            value_max
            - value_min
        )

    result["transfer_score"] = (
        points_score * 0.6
        + value_score * 0.4
    )

    result = result.sort_values(
        [
            "transfer_gain",
            "transfer_score",
            "predicted_points",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    return result[columns]