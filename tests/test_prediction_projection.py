import pandas as pd

from backend.main import _prediction_by_id


def test_team_prediction_projection_keeps_minutes_and_start_probability():
    frame = pd.DataFrame([{
        "player_id": 411,
        "predicted_points": 5.2,
        "xmins": 82.0,
        "start_probability": 0.91,
        "opponent": "Arsenal",
        "difficulty": 4,
    }])

    projection = _prediction_by_id(frame)[411]

    assert projection["xmins"] == 82.0
    assert projection["start_probability"] == 0.91
