import os

import pandas as pd
import pytest

from optimizer.squad_optimizer import (
    optimize_squad,
    optimize_from_predictions,
)


def make_players():
    rows = []

    players = {
        "GK": ["GK1", "GK2", "GK3", "GK4"],
        "DEF": [f"DEF{i}" for i in range(1, 9)],
        "MID": [f"MID{i}" for i in range(1, 9)],
        "FWD": [f"FWD{i}" for i in range(1, 6)],
    }

    points = {
        "GK": [6, 5, 4, 3],
        "DEF": [7, 6.8, 6.5, 6.2, 6, 5.8, 5.5, 5],
        "MID": [9, 8.5, 8, 7.5, 7, 6.5, 6, 5.5],
        "FWD": [9, 8, 7, 6, 5],
    }

    price = {
        "GK": [5.0, 4.5, 4.0, 4.0],
        "DEF": [
            6.0,
            5.5,
            5.0,
            4.5,
            4.5,
            4.0,
            4.0,
            4.0,
        ],
        "MID": [
            10.0,
            9.0,
            8.0,
            7.0,
            6.5,
            6.0,
            5.5,
            5.0,
        ],
        "FWD": [
            9.0,
            8.0,
            7.0,
            6.0,
            5.5,
        ],
    }

    for position, names in players.items():
        for i, name in enumerate(names):
            rows.append(
                {
                    "name": name,
                    "position": position,
                    "team": f"Team{(i % 6) + 1}",
                    "price": price[position][i],
                    "predicted_points": points[position][i],
                }
            )

    return pd.DataFrame(rows)


def test_optimizer_selects_valid_15_player_squad():
    squad = optimize_squad(
        make_players(),
        budget=100.0,
    )

    assert len(squad) == 15

    assert squad["position"].value_counts().to_dict() == {
        "GK": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3,
    }


def test_optimizer_respects_budget():
    squad = optimize_squad(
        make_players(),
        budget=85.0,
    )

    assert squad["price"].sum() <= 85.0


def test_optimizer_prefers_higher_predicted_points():
    squad = optimize_squad(
        make_players(),
        budget=100.0,
    )

    assert "MID1" in squad["name"].values
    assert "FWD1" in squad["name"].values


def test_optimizer_requires_enough_players():
    players = make_players()

    players = players[
        players["position"] != "FWD"
    ]

    with pytest.raises(
        ValueError,
        match="position FWD",
    ):
        optimize_squad(
            players,
            budget=100.0,
        )


def test_optimizer_maximum_three_players_per_club():
    players = make_players()

    players.loc[
        players["name"].isin(
            [
                "GK3",
                "DEF7",
                "MID7",
                "FWD5",
            ]
        ),
        "team",
    ] = "Arsenal"

    squad = optimize_squad(
        players,
        budget=100.0,
    )

    arsenal_count = (
        squad["team"] == "Arsenal"
    ).sum()

    assert arsenal_count <= 3


def test_optimizer_rejects_missing_team_column():
    players = make_players().drop(
        columns=["team"]
    )

    with pytest.raises(
        ValueError,
        match="team",
    ):
        optimize_squad(
            players,
            budget=100.0,
        )


def test_optimizer_rejects_invalid_budget():
    with pytest.raises(
        ValueError,
        match="budget",
    ):
        optimize_squad(
            make_players(),
            budget=0,
        )


def test_optimizer_from_predictions_reads_csv():
    players = make_players()

    path = (
        "tests/"
        "_optimizer_predictions_test.csv"
    )

    players.to_csv(
        path,
        index=False,
    )

    try:
        squad = optimize_from_predictions(
            path,
            budget=100.0,
        )

        assert len(squad) == 15
        assert "predicted_points" in squad.columns

    finally:
        if os.path.exists(path):
            os.remove(path)


def test_optimizer_from_real_predictions_file():
    path = (
        "historical_data/"
        "current_data/"
        "gw2_predictions_v5.csv"
    )

    if not os.path.exists(path):
        pytest.skip(
            "GW2 predictions file does not exist"
        )

    squad = optimize_from_predictions(
        path,
        budget=100.0,
    )

    assert len(squad) == 15

    assert squad["position"].value_counts().to_dict() == {
        "GK": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3,
    }

    assert squad["price"].sum() <= 100.0

    assert (
        squad["team"]
        .value_counts()
        .max()
        <= 3
    )

def test_optimizer_accepts_explicit_objective_config():
    from optimizer.objective import OptimizerObjectiveConfig
    players = make_players()
    players["risk"] = 0.0
    squad = optimize_squad(
        players,
        budget=100.0,
        objective_config=OptimizerObjectiveConfig(risk_weight=0.5),
    )
    assert len(squad) == 15
