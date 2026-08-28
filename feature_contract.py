"""Canonical, validated model-input contract shared by training and live runs."""

from __future__ import annotations

from collections.abc import Mapping


# This must match the persisted model exactly.
FEATURE_COLUMNS = (
    "xP",
    "price",
    "was_home",
    "points_last_3",
    "points_last_5",
    "points_avg_5",
    "minutes_last_5",
    "starts_last_5",
    "goals_last_5",
    "assists_last_5",
    "bps_avg_5",
    "influence_avg_5",
    "creativity_avg_5",
    "threat_avg_5",
    "ict_index_avg_5",
    "form_5",
    "position",
    "opponent_team",
)

CATEGORICAL_COLUMNS = (
    "position",
)

NUMERIC_COLUMNS = tuple(
    column
    for column in FEATURE_COLUMNS
    if column not in CATEGORICAL_COLUMNS
)


class FeatureContractError(ValueError):
    """Raised when a source cannot provide a valid canonical model row."""


def build_feature_row(
    source: Mapping[str, object],
) -> dict[str, object]:
    """
    Normalize one source row into the canonical model-input contract.

    xP is optional for backwards compatibility with older training/test
    sources. When it is absent, it defaults to 0.0.

    The returned dictionary always follows FEATURE_COLUMNS order.
    """

    # xP was added to the live/model contract later than some of the
    # original training/test fixtures. Keep it optional at the boundary,
    # while always emitting it in the canonical row.
    missing = [
        column
        for column in FEATURE_COLUMNS
        if column != "xP" and column not in source
    ]

    if missing:
        raise FeatureContractError(
            f"Missing required feature(s): {', '.join(missing)}"
        )

    row: dict[str, object] = {}

    for column in FEATURE_COLUMNS:
        # Backwards-compatible default for old training/test rows.
        if column == "xP" and column not in source:
            row[column] = 0.0
            continue

        value = source[column]

        if column == "position":
            if not isinstance(value, str) or not value.strip():
                raise FeatureContractError(
                    "position must be a non-empty string"
                )

            row[column] = value.strip()
            continue

        if isinstance(value, bool):
            row[column] = float(value)
            continue

        try:
            row[column] = float(value)
        except (TypeError, ValueError) as error:
            raise FeatureContractError(
                f"{column} must be numeric"
            ) from error

    return row


def validate_model_feature_names(
    feature_names: list[str] | tuple[str, ...],
) -> None:
    """
    Reject a persisted model trained against a different feature contract.
    """

    if tuple(feature_names) != FEATURE_COLUMNS:
        raise FeatureContractError(
            "Persisted model feature contract differs from "
            "the current contract; retrain required."
        )