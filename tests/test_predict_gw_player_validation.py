import pandas as pd

from player_validation import filter_current_fpl_players


def test_live_prediction_pool_excludes_historical_player_not_in_current_pl():
    players_features = pd.DataFrame(
        [
            {
                "player_id": 1,
                "name": "Current Player",
                "team": "Arsenal",
            },
            {
                "player_id": 2,
                "name": "Historical Player",
                "team": "Former PL Club",
            },
        ]
    )

    teams_current = pd.DataFrame(
        [
            {"id": 1, "name": "Arsenal"},
            {"id": 2, "name": "Liverpool"},
        ]
    )

    filtered = filter_current_fpl_players(
        players_features,
        teams_current,
    )

    assert filtered["player_id"].tolist() == [1]
    assert filtered["name"].tolist() == ["Current Player"]
