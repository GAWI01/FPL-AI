import pandas as pd

from historical_data.current_data.xmins import (
    availability_label,
    build_xmins_columns,
    calculate_xmins,
)


def row(**kwargs):
    defaults = {
        "status": "a",
        "chance_of_playing_next_round": float("nan"),
        "minutes": 0,
        "position": "MID",
        "news": "",
    }
    defaults.update(kwargs)
    return pd.Series(defaults)


def test_unavailable_player_has_zero_xmins():
    assert calculate_xmins(
        row(status="i", minutes=180, minutes_last_5=450, starts_last_5=5)
    ) == 0.0


def test_nailed_starter_is_not_forced_to_30():
    result = calculate_xmins(
        row(minutes=450, minutes_last_5=440, starts_last_5=5)
    )
    assert 75.0 <= result <= 90.0


def test_recent_starts_drive_early_season_xmins():
    result = calculate_xmins(
        row(minutes=180, minutes_last_5=175, starts_last_5=2)
    )
    assert result > 30.0


def test_chance_of_playing_reduces_xmins():
    healthy = calculate_xmins(
        row(minutes=450, minutes_last_5=440, starts_last_5=5)
    )
    doubtful = calculate_xmins(
        row(
            minutes=450,
            minutes_last_5=440,
            starts_last_5=5,
            chance_of_playing_next_round=50,
        )
    )
    assert doubtful == round(healthy * 0.5, 1)


def test_no_history_has_no_artificial_30_minute_floor():
    assert calculate_xmins(row(minutes=0)) == 0.0


def test_availability_labels():
    assert availability_label(
        row(status="a", chance_of_playing_next_round=50)
    ) == "RISK"
    assert availability_label(
        row(status="a", chance_of_playing_next_round=75)
    ) == "MINOR_RISK"


def test_build_columns():
    players = pd.DataFrame([
        {
            "name": "Starter",
            "position": "MID",
            "team": "Arsenal",
            "status": "a",
            "chance_of_playing_next_round": float("nan"),
            "minutes": 450,
            "minutes_last_5": 440,
            "starts_last_5": 5,
            "news": "",
        },
        {
            "name": "Out",
            "position": "MID",
            "team": "Liverpool",
            "status": "s",
            "chance_of_playing_next_round": 0,
            "minutes": 450,
            "minutes_last_5": 400,
            "starts_last_5": 5,
            "news": "Suspended",
        },
    ])

    result = build_xmins_columns(players)

    assert {
        "xmins",
        "availability",
        "start_probability",
        "rotation_risk",
        "availability_multiplier",
    }.issubset(result.columns)

    assert result.loc[result["name"] == "Out", "xmins"].iloc[0] == 0.0
    assert result.loc[result["name"] == "Starter", "xmins"].iloc[0] >= 75.0
