import pandas as pd
import pytest

from app_team import (
    TeamIdError,
    merge_team_with_predictions,
    normalize_team_id,
)


def test_normalize_team_id_accepts_integer():
    assert normalize_team_id(1234567) == 1234567


def test_normalize_team_id_accepts_string():
    assert normalize_team_id("1234567") == 1234567


def test_normalize_team_id_strips_whitespace():
    assert normalize_team_id(" 1234567 ") == 1234567


def test_normalize_team_id_rejects_empty_value():
    with pytest.raises(
        TeamIdError,
        match="Team ID",
    ):
        normalize_team_id("")


def test_normalize_team_id_rejects_non_numeric_value():
    with pytest.raises(
        TeamIdError,
        match="Team ID",
    ):
        normalize_team_id("abc")


def test_normalize_team_id_rejects_zero():
    with pytest.raises(
        TeamIdError,
        match="Team ID",
    ):
        normalize_team_id(0)


def test_normalize_team_id_rejects_negative_value():
    with pytest.raises(
        TeamIdError,
        match="Team ID",
    ):
        normalize_team_id(-123)


def test_merge_my_team_with_predictions():
    team = {
        "team_id": 1234567,
        "name": "Test Team",
        "bank": 15,
        "event": 3,
        "transfers": 1,
        "picks": [
            {
                "player_id": 10,
                "position": 1,
                "multiplier": 1,
            },
            {
                "player_id": 20,
                "position": 2,
                "multiplier": 1,
            },
        ],
    }

    predictions = pd.DataFrame(
        {
            "player_id": [10, 20],
            "name": ["Player A", "Player B"],
            "position": ["GK", "DEF"],
            "team": ["Team A", "Team B"],
            "price": [5.0, 5.5],
            "predicted_points": [6.5, 4.2],
        }
    )

    result = merge_team_with_predictions(
        team,
        predictions,
    )

    assert len(result) == 2
    assert list(result["name"]) == [
        "Player A",
        "Player B",
    ]
    assert list(result["predicted_points"]) == [
        6.5,
        4.2,
    ]


def test_merge_my_team_with_predictions_uses_player_id():
    team = {
        "team_id": 1234567,
        "name": "Test Team",
        "picks": [
            {
                "player_id": 10,
                "position": 1,
            },
        ],
    }

    predictions = pd.DataFrame(
        {
            "player_id": [10, 999],
            "name": ["Correct Player", "Wrong Player"],
            "predicted_points": [7.0, 99.0],
        }
    )

    result = merge_team_with_predictions(
        team,
        predictions,
    )

    assert len(result) == 1
    assert result.iloc[0]["name"] == "Correct Player"
    assert result.iloc[0]["predicted_points"] == 7.0


def test_merge_keeps_player_when_prediction_is_missing():
    team = {
        "team_id": 1234567,
        "name": "Test Team",
        "picks": [
            {
                "player_id": 10,
                "position": 1,
            },
        ],
    }

    predictions = pd.DataFrame(
        {
            "player_id": [999],
            "name": ["Other Player"],
            "predicted_points": [8.0],
        }
    )

    result = merge_team_with_predictions(
        team,
        predictions,
    )

    assert len(result) == 1
    assert result.iloc[0]["player_id"] == 10
    assert pd.isna(result.iloc[0]["predicted_points"])


def test_merge_preserves_team_pick_information():
    team = {
        "team_id": 1234567,
        "name": "Test Team",
        "picks": [
            {
                "player_id": 10,
                "position": 1,
                "multiplier": 2,
            },
        ],
    }

    predictions = pd.DataFrame(
        {
            "player_id": [10],
            "name": ["Player A"],
            "predicted_points": [7.0],
        }
    )

    result = merge_team_with_predictions(
        team,
        predictions,
    )

    assert result.iloc[0]["player_id"] == 10
    assert result.iloc[0]["position"] == 1
    assert result.iloc[0]["multiplier"] == 2

def test_prepare_team_selection_splits_starting_xi_and_bench():
    from app_team import prepare_team_selection

    team = {
        "picks": [
            {"player_id": 1, "position": 1, "multiplier": 1},
            {"player_id": 2, "position": 2, "multiplier": 1},
            {"player_id": 3, "position": 2, "multiplier": 1},
            {"player_id": 4, "position": 2, "multiplier": 1},
            {"player_id": 5, "position": 2, "multiplier": 1},
            {"player_id": 6, "position": 3, "multiplier": 1},
            {"player_id": 7, "position": 3, "multiplier": 1},
            {"player_id": 8, "position": 3, "multiplier": 1},
            {"player_id": 9, "position": 3, "multiplier": 1},
            {"player_id": 10, "position": 4, "multiplier": 1},
            {"player_id": 11, "position": 4, "multiplier": 1},
            {"player_id": 12, "position": 2, "multiplier": 0},
            {"player_id": 13, "position": 3, "multiplier": 0},
            {"player_id": 14, "position": 3, "multiplier": 0},
            {"player_id": 15, "position": 4, "multiplier": 0},
        ]
    }

    result = prepare_team_selection(team)

    assert len(result["starting_xi"]) == 11
    assert len(result["bench"]) == 4


def test_prepare_team_selection_identifies_captain():
    from app_team import prepare_team_selection

    team = {
        "picks": [
            {"player_id": 1, "position": 1, "multiplier": 1},
            {"player_id": 2, "position": 2, "multiplier": 2},
        ]
    }

    result = prepare_team_selection(team)

    assert result["captain_id"] == 2


def test_prepare_team_selection_identifies_vice_captain():
    from app_team import prepare_team_selection

    team = {
        "picks": [
            {"player_id": 1, "position": 1, "multiplier": 1},
            {"player_id": 2, "position": 2, "multiplier": 2},
            {"player_id": 3, "position": 2, "multiplier": 1},
        ]
    }

    # FPL uses multiplier 2 for captain and 1 for vice-captain,
    # but vice-captain is represented separately by the vice_captain
    # field when available.
    team["vice_captain"] = 3

    result = prepare_team_selection(team)

    assert result["captain_id"] == 2
    assert result["vice_captain_id"] == 3


def test_prepare_team_selection_preserves_player_ids():
    from app_team import prepare_team_selection

    team = {
        "picks": [
            {"player_id": 10, "position": 1, "multiplier": 1},
            {"player_id": 20, "position": 2, "multiplier": 1},
        ]
    }

    result = prepare_team_selection(team)

    assert [
        pick["player_id"]
        for pick in result["starting_xi"]
    ] == [10, 20]


def test_prepare_team_selection_handles_empty_team():
    from app_team import prepare_team_selection

    result = prepare_team_selection({"picks": []})

    assert result["starting_xi"] == []
    assert result["bench"] == []
    assert result["captain_id"] is None
    assert result["vice_captain_id"] is None