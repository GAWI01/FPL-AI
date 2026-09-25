import pandas as pd
import pytest

from transfer_in import (
    TransferInAnalysisError,
    analyze_transfer_in,
)


def make_team():
    return {
        "name": "Test Team",
        "picks": [
            {"player_id": 1, "position": 1, "multiplier": 1},
            {"player_id": 2, "position": 2, "multiplier": 1},
            {"player_id": 3, "position": 3, "multiplier": 1},
        ],
    }


def make_predictions():
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5, 6],
            "name": [
                "Keeper",
                "Defender A",
                "Midfielder A",
                "Defender B",
                "Defender C",
                "Midfielder B",
            ],
            "position": [
                "GK",
                "DEF",
                "MID",
                "DEF",
                "DEF",
                "MID",
            ],
            "price": [5.0, 5.0, 8.0, 6.0, 4.0, 7.0],
            "predicted_points": [4.0, 3.0, 6.0, 7.0, 5.0, 8.0],
        }
    )


def test_transfer_in_returns_candidates():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
    )

    assert set(result["player_id"]) == {4, 5, 6}


def test_transfer_in_excludes_owned_players():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
    )

    assert 1 not in set(result["player_id"])
    assert 2 not in set(result["player_id"])
    assert 3 not in set(result["player_id"])


def test_transfer_in_matches_outgoing_position():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    assert set(result["player_id"]) == {4, 5}
    assert set(result["position"]) == {"DEF"}


def test_transfer_in_respects_budget():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
        player_out_id=2,
        budget=5.0,
    )

    assert set(result["player_id"]) == {5}
    assert result.iloc[0]["price"] == 4.0


def test_transfer_in_calculates_transfer_gain():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    player_b = result[
        result["player_id"] == 4
    ].iloc[0]

    assert player_b["transfer_gain"] == 4.0


def test_transfer_in_contains_value_and_score():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    assert "points_per_million" in result.columns
    assert "transfer_score" in result.columns


def test_transfer_in_ranks_best_gain_first():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    assert result.iloc[0]["player_id"] == 4


def test_transfer_in_empty_result_has_expected_columns():
    result = analyze_transfer_in(
        make_team(),
        make_predictions(),
        player_out_id=2,
        budget=3.0,
    )

    assert result.empty
    assert "transfer_gain" in result.columns


def test_missing_outgoing_player_raises():
    with pytest.raises(TransferInAnalysisError):
        analyze_transfer_in(
            make_team(),
            make_predictions(),
            player_out_id=99,
        )