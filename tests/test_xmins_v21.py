import pandas as pd

from historical_data.current_data.xmins import (
    build_xmins_columns,
    calculate_xmins,
)


def test_gw1_history_overrides_misleading_current_season_minutes():
    row_without_gw1 = pd.Series({
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 90,
    })

    row_with_gw1 = pd.Series({
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 90,
        "minutes_gw1": 0,
        "started_gw1": 0,
        "played_gw1": 0,
    })

    without_gw1 = calculate_xmins(row_without_gw1)
    with_gw1 = calculate_xmins(row_with_gw1)

    assert with_gw1 < without_gw1


def test_gw1_starter_uses_gw1_minutes_when_last5_history_is_missing():
    df = pd.DataFrame([{
        "player_id": 1,
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 90,
        "minutes_gw1": 90,
        "started_gw1": 1,
        "played_gw1": 1,
    }])

    result = build_xmins_columns(df)

    assert result.loc[0, "xmins"] >= 75
    assert result.loc[0, "start_probability"] >= 0.83


def test_gw1_substitute_gets_lower_xmins():
    df = pd.DataFrame([{
        "player_id": 1,
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 9,
        "minutes_gw1": 9,
        "started_gw1": 0,
        "played_gw1": 1,
    }])

    result = build_xmins_columns(df)

    assert result.loc[0, "xmins"] < 45


def test_unavailable_player_has_zero_xmins():
    df = pd.DataFrame([{
        "player_id": 1,
        "status": "i",
        "chance_of_playing_next_round": 0,
        "minutes": 90,
        "minutes_gw1": 90,
        "started_gw1": 1,
        "played_gw1": 1,
    }])

    result = build_xmins_columns(df)

    assert result.loc[0, "xmins"] == 0
    assert result.loc[0, "start_probability"] == 0


def test_fifty_percent_availability_reduces_xmins():
    df = pd.DataFrame([{
        "player_id": 1,
        "status": "a",
        "chance_of_playing_next_round": 50,
        "minutes": 90,
        "minutes_gw1": 90,
        "started_gw1": 1,
        "played_gw1": 1,
    }])

    result = build_xmins_columns(df)

    assert 0 < result.loc[0, "xmins"] < 75


def test_five_gameweek_history_is_preferred_when_available():
    df = pd.DataFrame([{
        "player_id": 1,
        "status": "a",
        "chance_of_playing_next_round": 100,
        "minutes": 450,
        "minutes_gw1": 10,
        "started_gw1": 0,
        "played_gw1": 1,
        "minutes_last_5": 450,
        "starts_last_5": 5,
    }])

    result = build_xmins_columns(df)

    assert result.loc[0, "xmins"] >= 75
    assert result.loc[0, "start_probability"] >= 0.83
