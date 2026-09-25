import pandas as pd
import pytest

from player_validation import (
    PlayerValidationError,
    filter_current_fpl_players,
    validate_current_fpl_players,
)


def test_current_fpl_validation_accepts_canonical_team_names():
    players = pd.DataFrame(
        [
            {"player_id": 1, "team": "Arsenal"},
            {"player_id": 2, "team": "Liverpool"},
            {"player_id": 999, "team": "Former PL Club"},
        ]
    )
    teams = pd.DataFrame(
        [
            {"id": 1, "name": "Arsenal"},
            {"id": 2, "name": "Liverpool"},
        ]
    )

    result = validate_current_fpl_players(players, teams)

    assert result.valid_player_ids == {1, 2}
    assert result.invalid_player_ids == {999}


def test_filter_current_fpl_players_removes_historical_player_by_team_name():
    players = pd.DataFrame(
        [
            {"player_id": 1, "name": "Current Player", "team": "Arsenal"},
            {"player_id": 2, "name": "Historical Player", "team": "Former PL Club"},
        ]
    )
    teams = pd.DataFrame(
        [
            {"id": 1, "name": "Arsenal"},
            {"id": 2, "name": "Liverpool"},
        ]
    )

    result = filter_current_fpl_players(players, teams)

    assert result["player_id"].tolist() == [1]
    assert "Historical Player" not in result["name"].tolist()


def test_current_fpl_validation_still_accepts_numeric_team_ids():
    players = pd.DataFrame(
        [
            {"player_id": 1, "team": 1},
            {"player_id": 2, "team": 99},
        ]
    )
    teams = pd.DataFrame(
        [
            {"id": 1, "name": "Arsenal"},
            {"id": 2, "name": "Liverpool"},
        ]
    )

    result = validate_current_fpl_players(players, teams)

    assert result.valid_player_ids == {1}
    assert result.invalid_player_ids == {2}


def test_current_fpl_validation_rejects_missing_team_name_column():
    players = pd.DataFrame([{"player_id": 1, "team": "Arsenal"}])
    teams = pd.DataFrame([{"id": 1}])

    with pytest.raises(
        PlayerValidationError,
        match="teams is missing required column",
    ):
        validate_current_fpl_players(players, teams)
