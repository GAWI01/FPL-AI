import pandas as pd
import pytest

from app import build_transfer_center


def make_team():
    return {
        "name": "Test Team",
        "picks": [
            {
                "player_id": 1,
                "position": 1,
                "multiplier": 1,
            },
            {
                "player_id": 2,
                "position": 2,
                "multiplier": 1,
            },
        ],
    }


def make_predictions():
    return pd.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5],
            "name": [
                "Keeper",
                "Defender A",
                "Defender B",
                "Defender Value",
                "Midfielder",
            ],
            "position": [
                "GK",
                "DEF",
                "DEF",
                "DEF",
                "MID",
            ],
            "price": [
                5.0,
                5.0,
                6.0,
                5.0,
                8.0,
            ],
            "predicted_points": [
                5.0,
                3.0,
                8.0,
                6.0,
                10.0,
            ],
        }
    )


def test_build_transfer_center_returns_transfer_data():
    result = build_transfer_center(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    assert isinstance(result, dict)
    assert result["player_out_id"] == 2
    assert result["recommended_player_id"] == 3


def test_build_transfer_center_includes_recommendation():
    result = build_transfer_center(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    assert result["recommended_player"] == "Defender B"
    assert result["predicted_gain"] == 5.0


def test_build_transfer_center_includes_price_and_points():
    result = build_transfer_center(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    assert result["recommended_price"] == 6.0
    assert result["recommended_predicted_points"] == 8.0


def test_build_transfer_center_includes_alternatives():
    result = build_transfer_center(
        make_team(),
        make_predictions(),
        player_out_id=2,
    )

    alternatives = result["alternatives"]

    assert not alternatives.empty
    assert 4 in alternatives["player_id"].tolist()


def test_build_transfer_center_requires_player():
    with pytest.raises(ValueError):
        build_transfer_center(
            make_team(),
            make_predictions(),
        )