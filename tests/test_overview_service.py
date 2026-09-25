import pandas as pd
from backend.overview_service import build_top_players


def test_build_top_players_ranks_predictions_and_adds_market_fields():
    predictions = pd.DataFrame([
        {"player_id": 2, "name": "Second", "position": "FWD", "team": "Team B", "price": 7.0, "opponent": "Team C", "predicted_points": 8.5, "form": 6.0, "value": 1.2},
        {"player_id": 1, "name": "First", "position": "MID", "team": "Team A", "price": 8.0, "opponent": "Team D", "predicted_points": 9.5, "form": 7.0, "value": 1.3},
    ])
    players = pd.DataFrame([
        {"player_id": 1, "selected_by_percent": 42.5},
        {"player_id": 2, "selected_by_percent": 12.5},
    ])
    teams = pd.DataFrame([
        {"name": "Team A", "short_name": "TMA"},
        {"name": "Team B", "short_name": "TMB"},
    ])
    result = build_top_players(predictions, players, teams, limit=2)
    assert [row["player_id"] for row in result] == [1, 2]
    assert result[0]["team_short"] == "TMA"
    assert result[0]["ownership"] == 42.5
    assert result[0]["predicted_points"] == 9.5
