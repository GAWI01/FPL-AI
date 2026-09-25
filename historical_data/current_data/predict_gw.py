"""
Generate current Gameweek predictions using the persisted FPL-AI model.

The model input is always built through feature_contract.build_feature_row().
Current players are filtered against the current FPL team universe before
fixtures are matched or predictions are generated.
"""

from __future__ import annotations

from datetime import datetime, timezone
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feature_contract import (
    FEATURE_COLUMNS,
    build_feature_row,
    validate_model_feature_names,
)
from player_validation import filter_current_fpl_players
from backend.data_manifest import publish_prediction_manifest, season_for_date


CURRENT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "fpl_model_v1.pkl"

PLAYERS_PATH = CURRENT_DIR / "players_features_current.csv"
TEAMS_PATH = CURRENT_DIR / "teams_current.csv"
FIXTURES_PATH = CURRENT_DIR / "fixtures_current.csv"
GAMEWEEKS_PATH = CURRENT_DIR / "gameweeks_current.csv"


def num(value, default: float = 0.0) -> float:
    value = pd.to_numeric(value, errors="coerce")
    return default if pd.isna(value) else float(value)


def calculate_xp(
    form: float,
    points_per_game: float,
    minutes: float,
    expected_goals: float,
    expected_assists: float,
) -> float:
    base = max(points_per_game, form, 0.0)
    minutes_factor = np.clip(minutes / 90.0, 0.0, 1.0)

    attacking_bonus = (
        max(expected_goals, 0.0) * 4.0
        + max(expected_assists, 0.0) * 3.0
    )

    xp = base * 0.55 + attacking_bonus * 0.45
    availability_factor = 0.35 + 0.65 * minutes_factor

    return float(np.clip(xp * availability_factor, 0.0, 15.0))


def main() -> None:
    print("=" * 70)
    print("FPL AI — CURRENT GAMEWEEK PREDICTIONS V1.2")
    print("=" * 70)

    model = joblib.load(MODEL_PATH)

    model_features = list(model.feature_names_in_)
    validate_model_feature_names(model_features)

    players = pd.read_csv(PLAYERS_PATH)
    teams = pd.read_csv(TEAMS_PATH)
    fixtures = pd.read_csv(FIXTURES_PATH)
    gameweeks = pd.read_csv(GAMEWEEKS_PATH)

    # Hard eligibility gate: historical/obsolete players must not enter the
    # live prediction universe merely because they exist in source data.
    before_count = len(players)
    players = filter_current_fpl_players(players, teams)
    after_count = len(players)

    print(
        f"Current FPL player validation: {after_count}/{before_count} players retained"
    )

    if players.empty:
        raise RuntimeError("No current FPL players remain after validation.")

    next_gw = gameweeks[gameweeks["is_next"].astype(bool)]

    if next_gw.empty:
        raise RuntimeError("No next Gameweek found.")

    gw = int(next_gw.iloc[0]["id"])

    gw_fixtures = fixtures[fixtures["event"] == gw].copy()

    if gw_fixtures.empty:
        raise RuntimeError(f"No fixtures found for GW{gw}.")

    team_id_to_name = dict(
        zip(teams["id"].astype(int), teams["name"])
    )

    team_name_to_id = {
        name: team_id
        for team_id, name in team_id_to_name.items()
    }

    team_data = {}

    for _, team in teams.iterrows():
        team_id = int(team["id"])

        team_data[team_id] = {
            "strength": num(team.get("strength", 0)),
            "strength_overall_home": num(
                team.get("strength_overall_home", 0)
            ),
            "strength_overall_away": num(
                team.get("strength_overall_away", 0)
            ),
            "strength_attack_home": num(
                team.get("strength_attack_home", 0)
            ),
            "strength_attack_away": num(
                team.get("strength_attack_away", 0)
            ),
            "strength_defence_home": num(
                team.get("strength_defence_home", 0)
            ),
            "strength_defence_away": num(
                team.get("strength_defence_away", 0)
            ),
        }

    fixture_lookup: dict[int, dict] = {}

    for _, fixture in gw_fixtures.iterrows():
        home_id = int(fixture["team_h"])
        away_id = int(fixture["team_a"])

        fixture_lookup[home_id] = {
            "opponent_id": away_id,
            "opponent_name": team_id_to_name.get(
                away_id,
                f"Team {away_id}",
            ),
            "was_home": True,
            "difficulty": num(fixture.get("team_h_difficulty", 0)),
        }

        fixture_lookup[away_id] = {
            "opponent_id": home_id,
            "opponent_name": team_id_to_name.get(
                home_id,
                f"Team {home_id}",
            ),
            "was_home": False,
            "difficulty": num(fixture.get("team_a_difficulty", 0)),
        }

    rows = []

    for _, player in players.iterrows():
        team_name = str(player.get("team", ""))

        if team_name not in team_name_to_id:
            continue

        team_id = team_name_to_id[team_name]

        if team_id not in fixture_lookup:
            continue

        fixture = fixture_lookup[team_id]
        opponent_id = fixture["opponent_id"]

        own = team_data.get(team_id, {})
        opponent = team_data.get(opponent_id, {})

        was_home = fixture["was_home"]

        if was_home:
            own_attack = own.get(
                "strength_attack_home",
                own.get("strength", 0),
            )
            own_defence = own.get(
                "strength_defence_home",
                own.get("strength", 0),
            )
            own_overall = own.get(
                "strength_overall_home",
                own.get("strength", 0),
            )

            opponent_attack = opponent.get(
                "strength_attack_away",
                opponent.get("strength", 0),
            )
            opponent_defence = opponent.get(
                "strength_defence_away",
                opponent.get("strength", 0),
            )
            opponent_overall = opponent.get(
                "strength_overall_away",
                opponent.get("strength", 0),
            )
        else:
            own_attack = own.get(
                "strength_attack_away",
                own.get("strength", 0),
            )
            own_defence = own.get(
                "strength_defence_away",
                own.get("strength", 0),
            )
            own_overall = own.get(
                "strength_overall_away",
                own.get("strength", 0),
            )

            opponent_attack = opponent.get(
                "strength_attack_home",
                opponent.get("strength", 0),
            )
            opponent_defence = opponent.get(
                "strength_defence_home",
                opponent.get("strength", 0),
            )
            opponent_overall = opponent.get(
                "strength_overall_home",
                opponent.get("strength", 0),
            )

        form = num(player.get("form", 0))
        ppg = num(player.get("points_per_game", 0))
        minutes = num(player.get("minutes", 0))

        expected_goals = num(player.get("expected_goals", 0))
        expected_assists = num(player.get("expected_assists", 0))

        xmins = num(player.get("xmins", minutes))
        start_probability = num(
            player.get(
                "start_probability",
                np.clip(xmins / 90.0, 0.0, 1.0),
            )
        )

        xp = calculate_xp(
            form=form,
            points_per_game=ppg,
            minutes=xmins,
            expected_goals=expected_goals,
            expected_assists=expected_assists,
        )

        model_row = build_feature_row({
            "xP": xp,
            "price": num(player.get("price", 0)),
            "was_home": was_home,
            "points_last_3": num(player.get("points_last_3", 0)),
            "points_last_5": num(player.get("points_last_5", 0)),
            "points_avg_5": num(player.get("points_avg_5", 0)),
            "minutes_last_5": num(player.get("minutes_last_5", 0)),
            "starts_last_5": num(
                player.get("starts_last_5", start_probability)
            ),
            "goals_last_5": num(player.get("goals_last_5", 0)),
            "assists_last_5": num(player.get("assists_last_5", 0)),
            "bps_avg_5": num(player.get("bps_avg_5", 0)),
            "influence_avg_5": num(player.get("influence_avg_5", 0)),
            "creativity_avg_5": num(player.get("creativity_avg_5", 0)),
            "threat_avg_5": num(player.get("threat_avg_5", 0)),
            "ict_index_avg_5": num(player.get("ict_index_avg_5", 0)),
            "form_5": num(player.get("form_5", 0)),
            "position": str(player.get("position", "")).upper().replace(
                "GKP",
                "GK",
            ),
            "opponent_team": opponent_id,
        })

        rows.append({
            "player_id": int(player["player_id"]),
            "name": player["name"],
            "position": player["position"],
            "team": team_name,
            "price": num(player.get("price", 0)),
            "opponent": fixture["opponent_name"],
            "home": was_home,
            "difficulty": fixture["difficulty"],
            "form": form,
            "minutes": minutes,
            "xP": xp,
            "xmins": xmins,
            "start_probability": start_probability,
            "model": model_row,
        })

    if not rows:
        raise RuntimeError("No players matched the current Gameweek fixtures.")

    X = pd.DataFrame(
        [row["model"] for row in rows],
        columns=FEATURE_COLUMNS,
    )

    predictions = model.predict(X)

    results = []

    for row, ml_prediction in zip(rows, predictions):
        prediction = max(0.0, float(ml_prediction))

        attack_advantage = 0.015 * (
            num(
                team_data.get(
                    team_name_to_id[row["team"]],
                    {},
                ).get(
                    "strength_attack_home"
                    if row["home"]
                    else "strength_attack_away",
                    0,
                )
            )
            - num(
                team_data.get(
                    fixture_lookup[
                        team_name_to_id[row["team"]]
                    ]["opponent_id"],
                    {},
                ).get(
                    "strength_defence_away"
                    if row["home"]
                    else "strength_defence_home",
                    0,
                )
            )
        )

        difficulty_factor = np.clip(
            1.0 - ((row["difficulty"] - 1.0) / 10.0),
            0.70,
            1.10,
        )

        prediction *= np.clip(
            (1.0 + attack_advantage) * difficulty_factor,
            0.75,
            1.25,
        )

        availability = np.clip(
            row["start_probability"],
            0.0,
            1.0,
        )

        prediction *= 0.75 + 0.25 * availability

        value = (
            prediction / row["price"]
            if row["price"] > 0
            else 0.0
        )

        results.append({
            "player_id": row["player_id"],
            "name": row["name"],
            "position": row["position"],
            "team": row["team"],
            "price": row["price"],
            "opponent": row["opponent"],
            "home": row["home"],
            "difficulty": row["difficulty"],
            "form": row["form"],
            "minutes": row["minutes"],
            "xP": round(row["xP"], 3),
            "xmins": round(row["xmins"], 1),
            "start_probability": round(
                row["start_probability"],
                3,
            ),
            "ml_prediction": round(
                float(ml_prediction),
                3,
            ),
            "predicted_points": round(
                float(np.clip(prediction, 0.0, 15.0)),
                3,
            ),
            "value": round(value, 3),
        })

    result_df = pd.DataFrame(results).sort_values(
        "predicted_points",
        ascending=False,
    )

    output_path = CURRENT_DIR / f"gw{gw}_predictions_v11.csv"
    result_df.to_csv(output_path, index=False)
    manifest_path = publish_prediction_manifest(
        output_path,
        season=season_for_date(datetime.now(timezone.utc)),
        prediction_event=gw,
        player_count=len(result_df),
    )

    print(f"\nGW{gw}")
    print(f"Players predicted: {len(result_df)}")
    print(f"Saved: {output_path}")
    print(f"Manifest: {manifest_path}")

    print("\nTOP 30")
    print(result_df.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
