import pandas as pd

from historical_data.current_data.xmins import build_xmins_columns


def test_no_universal_30_minute_xmins():
    players = pd.DataFrame([
        {
            "name": "Established Starter",
            "position": "MID",
            "status": "a",
            "chance_of_playing_next_round": float("nan"),
            "minutes": 450,
            "minutes_last_5": 440,
            "starts_last_5": 5,
            "news": "",
        },
        {
            "name": "Unused Player",
            "position": "MID",
            "status": "a",
            "chance_of_playing_next_round": float("nan"),
            "minutes": 0,
            "minutes_last_5": 0,
            "starts_last_5": 0,
            "news": "",
        },
    ])

    result = build_xmins_columns(players)

    starter = result.loc[
        result["name"] == "Established Starter", "xmins"
    ].iloc[0]
    unused = result.loc[
        result["name"] == "Unused Player", "xmins"
    ].iloc[0]

    assert starter >= 75.0
    assert unused == 0.0
    assert starter != 30.0
