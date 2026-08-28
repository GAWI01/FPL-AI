import pandas as pd
import pytest

from feature_engine import build_features, FeatureEngineError


def make_history():
    return pd.DataFrame(
        [
            {
                "player_id": 1,
                "event": 1,
                "minutes": 90,
                "goals": 1,
                "assists": 1,
                "total_points": 12,
                "started": 1,
            }
        ]
    )


def make_players():
    return pd.DataFrame(
        [
            {
                "player_id": 1,
                "price": 10.0,
                "position": "MID",
                "team": 1,
                "expected_goals": 0.75,
                "expected_assists": 0.42,
                "expected_goal_involvements": 1.17,
                "chance_of_playing_next_round": 100.0,
                "status": "a",
                "xmins": 90.0,
                "availability": 1.0,
                "start_probability": 1.0,
                "rotation_risk": 0.0,
            }
        ]
    )


def test_build_features_uses_gw1_for_gw2():
    features = build_features(
        make_players(),
        make_history(),
        target_gw=2,
    )

    assert len(features) == 1

    row = features.iloc[0]

    assert row["points_last_5"] == 12
    assert row["minutes_last_5"] == 90
    assert row["starts_last_5"] == 1
    assert row["goals_last_5"] == 1
    assert row["assists_last_5"] == 1


def test_future_gameweeks_are_not_used():
    history = pd.DataFrame(
        [
            {
                "player_id": 1,
                "event": 1,
                "minutes": 90,
                "goals": 1,
                "assists": 0,
                "total_points": 10,
                "started": 1,
            },
            {
                "player_id": 1,
                "event": 2,
                "minutes": 90,
                "goals": 5,
                "assists": 5,
                "total_points": 30,
                "started": 1,
            },
        ]
    )

    features = build_features(
        make_players(),
        history,
        target_gw=2,
    )

    row = features.iloc[0]

    # GW2 itself must NOT be included.
    assert row["points_last_5"] == 10
    assert row["minutes_last_5"] == 90
    assert row["goals_last_5"] == 1
    assert row["assists_last_5"] == 0


def test_missing_required_history_raises():
    players = make_players()

    history = pd.DataFrame(
        columns=[
            "player_id",
            "event",
            "minutes",
            "goals",
            "assists",
            "total_points",
            "started",
        ]
    )

    with pytest.raises(FeatureEngineError):
        build_features(
            players,
            history,
            target_gw=2,
        )


def test_build_features_includes_current_player_signals():
    features = build_features(
        make_players(),
        make_history(),
        target_gw=2,
    )

    row = features.iloc[0]

    assert row["expected_goals"] == 0.75
    assert row["expected_assists"] == 0.42
    assert row["expected_goal_involvements"] == 1.17

    assert row["chance_of_playing_next_round"] == 100.0
    assert row["status"] == "a"

    assert row["xmins"] == 90.0
    assert row["availability"] == 1.0
    assert row["start_probability"] == 1.0
    assert row["rotation_risk"] == 0.0


def test_player_without_history_raises():
    players = pd.DataFrame(
        [
            {
                "player_id": 1,
                "price": 10.0,
                "position": "MID",
                "team": 1,
            }
        ]
    )

    history = pd.DataFrame(
        [
            {
                "player_id": 2,
                "event": 1,
                "minutes": 90,
                "goals": 0,
                "assists": 0,
                "total_points": 2,
                "started": 1,
            }
        ]
    )

    with pytest.raises(FeatureEngineError):
        build_features(
            players,
            history,
            target_gw=2,
        )


def test_invalid_target_gameweek_raises():
    with pytest.raises(FeatureEngineError):
        build_features(
            make_players(),
            make_history(),
            target_gw=0,
        )


def test_features_are_built_from_only_previous_gameweeks():
    history = pd.DataFrame(
        [
            {
                "player_id": 1,
                "event": 1,
                "minutes": 90,
                "goals": 1,
                "assists": 1,
                "total_points": 12,
                "started": 1,
            },
            {
                "player_id": 1,
                "event": 2,
                "minutes": 60,
                "goals": 0,
                "assists": 1,
                "total_points": 7,
                "started": 1,
            },
            {
                "player_id": 1,
                "event": 3,
                "minutes": 90,
                "goals": 10,
                "assists": 10,
                "total_points": 100,
                "started": 1,
            },
        ]
    )

    features = build_features(
        make_players(),
        history,
        target_gw=3,
    )

    row = features.iloc[0]

    # Only GW1 + GW2 may be used for a GW3 prediction.
    assert row["points_last_5"] == 19
    assert row["minutes_last_5"] == 150
    assert row["goals_last_5"] == 1
    assert row["assists_last_5"] == 2