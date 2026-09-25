import pandas as pd
import pytest

from player_validation import (
    PlayerValidationError,
    filter_current_fpl_players,
    validate_current_fpl_players,
)


def _players():
    return pd.DataFrame([
        {"player_id": 1, "name": "Current Player", "team": 1, "status": "a"},
        {"player_id": 2, "name": "Transferred Player", "team": 2, "status": "a"},
        {"player_id": 3, "name": "Old Player", "team": 99, "status": "a"},
        {"player_id": 4, "name": "Unavailable Current", "team": 1, "status": "i"},
    ])


def _teams():
    return pd.DataFrame([
        {"id": 1, "name": "Arsenal"},
        {"id": 2, "name": "Liverpool"},
    ])


def test_accepts_players_belonging_to_current_fpl_teams():
    result = validate_current_fpl_players(_players(), _teams())

    assert result.valid_player_ids == {1, 2, 4}
    assert result.invalid_player_ids == {3}


def test_does_not_treat_unavailable_player_as_non_premier_league():
    result = validate_current_fpl_players(_players(), _teams())

    assert 4 in result.valid_player_ids
    assert 4 not in result.invalid_player_ids


def test_filter_removes_players_not_in_current_fpl_team_pool():
    filtered = filter_current_fpl_players(_players(), _teams())

    assert list(filtered["player_id"]) == [1, 2, 4]
    assert 3 not in set(filtered["player_id"])


def test_filter_preserves_prediction_rows_and_columns():
    predictions = pd.DataFrame([
        {"player_id": 1, "name": "Current Player", "predicted_points": 6.2},
        {"player_id": 99, "name": "Historical Player", "predicted_points": 8.9},
    ])

    filtered = filter_current_fpl_players(
        predictions,
        _teams(),
        require_team_column=False,
        player_pool=_players(),
    )

    assert list(filtered["player_id"]) == [1]
    assert list(filtered.columns) == list(predictions.columns)


def test_rejects_missing_player_id_column():
    with pytest.raises(PlayerValidationError, match="player_id"):
        validate_current_fpl_players(
            pd.DataFrame([{"name": "Player", "team": 1}]),
            _teams(),
        )


def test_rejects_missing_team_id_column():
    with pytest.raises(PlayerValidationError, match="team"):
        validate_current_fpl_players(
            pd.DataFrame([{"player_id": 1, "name": "Player"}]),
            _teams(),
        )


def test_rejects_invalid_team_source():
    with pytest.raises(PlayerValidationError, match="id"):
        validate_current_fpl_players(
            _players(),
            pd.DataFrame([{"name": "Arsenal"}]),
        )
