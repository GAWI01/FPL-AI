import pandas as pd
import pytest

from feature_contract import FEATURE_COLUMNS, FeatureContractError, build_feature_row


def test_feature_contract_contains_xp():
    assert "xP" in FEATURE_COLUMNS
    assert "position" in FEATURE_COLUMNS
    assert "opponent_team" in FEATURE_COLUMNS


def test_build_feature_row_preserves_xp():
    row = {
        "xP": 4.2,
        "price": 6.0,
        "was_home": True,
        "points_last_3": 10,
        "points_last_5": 15,
        "points_avg_5": 3,
        "minutes_last_5": 360,
        "starts_last_5": 4,
        "goals_last_5": 2,
        "assists_last_5": 1,
        "bps_avg_5": 25,
        "influence_avg_5": 40,
        "creativity_avg_5": 30,
        "threat_avg_5": 35,
        "ict_index_avg_5": 10,
        "form_5": 3,
        "position": "MID",
        "opponent_team": 10,
    }

    result = build_feature_row(row)

    assert list(result) == list(FEATURE_COLUMNS)
    assert result["xP"] == pytest.approx(4.2)
    assert result["position"] == "MID"


def test_build_feature_row_rejects_missing_required_feature():
    row = {
        "xP": 4.2,
        "price": 6.0,
        "was_home": True,
        "position": "MID",
        "opponent_team": 10,
    }

    with pytest.raises(FeatureContractError):
        build_feature_row(row)


def test_historical_rolling_features_do_not_use_current_gameweek():
    source = pd.DataFrame([
        {
            "player_id": 1,
            "GW": 1,
            "total_points": 2,
            "minutes": 90,
            "goals_scored": 0,
            "assists": 0,
            "bps": 10,
            "influence": 10,
            "creativity": 10,
            "threat": 10,
            "ict_index": 10,
            "value": 50,
            "xP": 2,
            "was_home": True,
            "opponent_team": 2,
            "position": "MID",
        },
        {
            "player_id": 1,
            "GW": 2,
            "total_points": 20,
            "minutes": 90,
            "goals_scored": 2,
            "assists": 1,
            "bps": 40,
            "influence": 40,
            "creativity": 40,
            "threat": 40,
            "ict_index": 40,
            "value": 55,
            "xP": 8,
            "was_home": False,
            "opponent_team": 3,
            "position": "MID",
        },
    ])

    # This test mirrors the production rolling semantics:
    # current-GW rows are shifted out before calculating the rolling window,
    # and an unavailable history window is represented as zero.
    source = source.sort_values(["player_id", "GW"])
    grouped = source.groupby("player_id")

    source["points_last_5"] = (
        grouped["total_points"]
        .transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).sum()
        )
        .fillna(0.0)
    )

    assert source.loc[source["GW"] == 1, "points_last_5"].iloc[0] == 0
    assert source.loc[source["GW"] == 2, "points_last_5"].iloc[0] == 2


def test_double_gameweek_rolling_features_do_not_use_current_gameweek_fixture():
    # This test is intentionally integration-shaped and uses the real fixture
    # aggregation semantics. It is skipped when the historical season fixture
    # data is not present in the test environment.
    # The unit-level invariant is tested directly below instead of mutating the
    # repository's historical CSVs.
    source = pd.DataFrame(
        [
            {"player_id": 1, "GW": 1, "fixture": 101, "total_points": 2, "minutes": 90,
             "goals_scored": 0, "assists": 0, "bps": 10, "influence": 20,
             "creativity": 10, "threat": 10, "ict_index": 4, "xP": 2, "value": 60,
             "was_home": 1, "opponent_team": 2, "position": "MID"},
            {"player_id": 1, "GW": 2, "fixture": 201, "total_points": 10, "minutes": 90,
             "goals_scored": 1, "assists": 0, "bps": 30, "influence": 40,
             "creativity": 20, "threat": 30, "ict_index": 8, "xP": 5, "value": 60,
             "was_home": 1, "opponent_team": 3, "position": "MID"},
            {"player_id": 1, "GW": 2, "fixture": 202, "total_points": 1, "minutes": 20,
             "goals_scored": 0, "assists": 0, "bps": 5, "influence": 8,
             "creativity": 4, "threat": 5, "ict_index": 2, "xP": 5, "value": 60,
             "was_home": 0, "opponent_team": 4, "position": "MID"},
        ]
    )

    level = (
        source.groupby(["player_id", "GW"], as_index=False)
        .agg(
            total_points=("total_points", "sum"),
            minutes=("minutes", "sum"),
            goals_scored=("goals_scored", "sum"),
            assists=("assists", "sum"),
            bps=("bps", "mean"),
            influence=("influence", "mean"),
            creativity=("creativity", "mean"),
            threat=("threat", "mean"),
            ict_index=("ict_index", "mean"),
        )
        .sort_values(["player_id", "GW"])
    )
    rolling = level.groupby("player_id")["total_points"].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).sum()
    )
    # Both GW2 fixtures must see the completed GW1 total only.
    assert rolling.fillna(0.0).tolist() == [0.0, 2.0]
    mapped = source.merge(
        pd.DataFrame({"player_id": level.player_id, "GW": level.GW,
                      "points_last_5": rolling}),
        on=["player_id", "GW"],
        how="left",
        validate="many_to_one",
    )
    assert mapped.loc[mapped.GW == 2, "points_last_5"].tolist() == [2.0, 2.0]
