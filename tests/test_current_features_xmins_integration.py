import pandas as pd

from historical_data.current_data import build_player_features
from historical_data.current_data.xmins import calculate_xmins as canonical_calculate_xmins


def test_current_feature_builder_uses_canonical_xmins_engine():
    row = pd.Series({
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 90,
        "minutes_gw1": 90,
        "started_gw1": 1,
        "played_gw1": 1,
    })

    builder_xmins = build_player_features.calculate_xmins(row)
    canonical_xmins = canonical_calculate_xmins(row)

    assert builder_xmins == canonical_xmins


def test_current_feature_builder_does_not_use_current_minutes_when_gw1_says_zero():
    row = pd.Series({
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 90,
        "minutes_gw1": 0,
        "started_gw1": 0,
        "played_gw1": 0,
    })

    builder_xmins = build_player_features.calculate_xmins(row)
    canonical_xmins = canonical_calculate_xmins(row)

    assert canonical_xmins == 0.0
    assert builder_xmins == canonical_xmins
