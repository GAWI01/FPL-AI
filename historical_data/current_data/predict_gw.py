import os
import sys
import joblib
import pandas as pd
import numpy as np

# Add project root to Python import path.
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from feature_contract import build_feature_row, validate_model_feature_names


# ================================================================
# FPL AI — CURRENT GAMEWEEK PREDICTIONS V5
# ================================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "fpl_model_v1.pkl",
)

PLAYERS_PATH = os.path.join(CURRENT_DIR, "players_current.csv")
TEAMS_PATH = os.path.join(CURRENT_DIR, "teams_current.csv")
FIXTURES_PATH = os.path.join(CURRENT_DIR, "fixtures_current.csv")
GAMEWEEKS_PATH = os.path.join(CURRENT_DIR, "gameweeks_current.csv")


def header(text):
    print("=" * 70)
    print(text)
    print("=" * 70)


def num(value, default=0.0):
    value = pd.to_numeric(value, errors="coerce")

    if pd.isna(value):
        return default

    return float(value)


def calculate_xp(
    player,
    form,
    points_per_game,
    minutes,
    starts_last_5,
    expected_goals,
    expected_assists,
):
    """
    Estimate expected points (xP) for the upcoming gameweek.

    The persisted model explicitly expects xP, so this value is created
    from currently available player signals before prediction.
    """

    # Base historical scoring signal.
    base = max(
        points_per_game,
        form,
        0.0,
    )

    # Minutes / expected-start adjustment.
    minutes_factor = min(max(minutes / 90.0, 0.0), 1.0)

    start_factor = min(max(starts_last_5, 0.0), 1.0)

    # Attacking upside.
    attacking_bonus = (
        max(expected_goals, 0.0) * 4.0
        + max(expected_assists, 0.0) * 3.0
    )

    # Conservative blend.
    xp = (
        base * 0.55
        + attacking_bonus * 0.45
    )

    # Do not allow a player with no recent minutes/starts to receive
    # a full historical expectation.
    availability_factor = (
        0.35
        + 0.40 * minutes_factor
        + 0.25 * start_factor
    )

    xp *= availability_factor

    # Keep the model input sane.
    return max(0.0, min(float(xp), 15.0))


def main():

    header("FPL AI — CURRENT GAMEWEEK PREDICTIONS V5")

    # ============================================================
    # LOAD MODEL
    # ============================================================

    print("Laster ML-modell...")

    model = joblib.load(MODEL_PATH)

    validate_model_feature_names(
        list(model.feature_names_in_)
    )

    print("✓ Modell lastet")
    print("✓ Modell feature contract: OK")

    # ============================================================
    # LOAD CURRENT DATA
    # ============================================================

    print("\nLeser 2026/27-data...")

    players = pd.read_csv(PLAYERS_PATH)
    teams = pd.read_csv(TEAMS_PATH)
    fixtures = pd.read_csv(FIXTURES_PATH)
    gameweeks = pd.read_csv(GAMEWEEKS_PATH)

    print(f"Spillere:  {len(players)}")
    print(f"Fixtures:  {len(fixtures)}")

    # ============================================================
    # TEAM LOOKUPS
    # ============================================================

    team_id_to_name = dict(
        zip(
            teams["id"].astype(int),
            teams["name"],
        )
    )

    team_name_to_id = {
        name: int(team_id)
        for team_id, name in team_id_to_name.items()
    }

    team_data = {}

    for _, team in teams.iterrows():

        team_id = int(team["id"])

        team_data[team_id] = {
            "name": team["name"],
            "form": num(team.get("form", 0)),
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

    # ============================================================
    # FIND NEXT GAMEWEEK
    # ============================================================

    next_gw = gameweeks[
        gameweeks["is_next"] == True
    ]

    if next_gw.empty:

        print("\n✗ Fant ingen neste gameweek.")
        return

    gw = int(next_gw.iloc[0]["id"])

    print(f"\nNeste gameweek: GW{gw}")

    # ============================================================
    # GW FIXTURES
    # ============================================================

    gw_fixtures = fixtures[
        fixtures["event"] == gw
    ].copy()

    print(f"Fixtures i GW{gw}: {len(gw_fixtures)}")

    if gw_fixtures.empty:

        print("\n✗ Ingen fixtures funnet.")
        return

    # ============================================================
    # BUILD FIXTURE LOOKUP
    # ============================================================

    fixture_lookup = {}

    for _, fixture in gw_fixtures.iterrows():

        home_id = int(fixture["team_h"])
        away_id = int(fixture["team_a"])

        difficulty_home = num(
            fixture.get("team_h_difficulty", 0)
        )

        difficulty_away = num(
            fixture.get("team_a_difficulty", 0)
        )

        fixture_lookup[home_id] = {
            "opponent_id": away_id,
            "opponent_name": team_id_to_name.get(
                away_id,
                f"Team {away_id}",
            ),
            "was_home": True,
            "difficulty": difficulty_home,
            "fixture_id": int(fixture["id"]),
        }

        fixture_lookup[away_id] = {
            "opponent_id": home_id,
            "opponent_name": team_id_to_name.get(
                home_id,
                f"Team {home_id}",
            ),
            "was_home": False,
            "difficulty": difficulty_away,
            "fixture_id": int(fixture["id"]),
        }

    # ============================================================
    # SHOW FIXTURES
    # ============================================================

    print("\nGW FIXTURES")
    print("-" * 70)

    for _, fixture in gw_fixtures.iterrows():

        home = team_id_to_name.get(
            int(fixture["team_h"]),
            "Unknown",
        )

        away = team_id_to_name.get(
            int(fixture["team_a"]),
            "Unknown",
        )

        print(
            f"{home:<22} vs {away:<22}"
        )

    # ============================================================
    # BUILD PLAYER ROWS
    # ============================================================

    rows = []

    for _, player in players.iterrows():

        player_id = int(player["player_id"])
        player_name = player["name"]
        team_name = player["team"]

        if team_name not in team_name_to_id:
            continue

        team_id = team_name_to_id[team_name]

        if team_id not in fixture_lookup:
            continue

        fixture = fixture_lookup[team_id]

        opponent_id = fixture["opponent_id"]

        own_team = team_data.get(
            team_id,
            {},
        )

        opponent_team = team_data.get(
            opponent_id,
            {},
        )

        # ========================================================
        # PLAYER CURRENT DATA
        # ========================================================

        price = num(player.get("price", 0))
        form = num(player.get("form", 0))

        points_per_game = num(
            player.get("points_per_game", 0)
        )

        minutes = num(
            player.get("minutes", 0)
        )

        goals = num(
            player.get("goals_scored", 0)
        )

        assists = num(
            player.get("assists", 0)
        )

        bps = num(
            player.get("bps", 0)
        )

        influence = num(
            player.get("influence", 0)
        )

        creativity = num(
            player.get("creativity", 0)
        )

        threat = num(
            player.get("threat", 0)
        )

        ict_index = num(
            player.get("ict_index", 0)
        )

        expected_goals = num(
            player.get("expected_goals", 0)
        )

        expected_assists = num(
            player.get("expected_assists", 0)
        )

        # ========================================================
        # ROLLING FEATURES
        # ========================================================

        minutes_last_5 = minutes

        starts_last_5 = min(
            minutes / 90.0,
            1.0,
        )

        points_last_3 = points_per_game
        points_last_5 = points_per_game
        points_avg_5 = points_per_game

        goals_last_5 = goals
        assists_last_5 = assists

        bps_avg_5 = bps
        influence_avg_5 = influence
        creativity_avg_5 = creativity
        threat_avg_5 = threat
        ict_index_avg_5 = ict_index

        form_5 = form

        # ========================================================
        # EXPECTED POINTS
        # ========================================================

        xP = calculate_xp(
            player=player,
            form=form,
            points_per_game=points_per_game,
            minutes=minutes,
            starts_last_5=starts_last_5,
            expected_goals=expected_goals,
            expected_assists=expected_assists,
        )

        # ========================================================
        # AVAILABILITY
        # ========================================================

        chance_playing = num(
            player.get(
                "chance_of_playing_next_round",
                100,
            ),
            100,
        )

        status = str(
            player.get("status", "a")
        ).strip().lower()

        availability_multiplier = (
            max(
                0,
                min(chance_playing, 100),
            )
            / 100.0
        )

        if status in ["i", "s", "u"]:
            availability_multiplier *= 0.5

        # ========================================================
        # TEAM STRENGTH
        # ========================================================

        if fixture["was_home"]:

            own_attack = own_team.get(
                "strength_attack_home",
                own_team.get("strength", 0),
            )

            own_defence = own_team.get(
                "strength_defence_home",
                own_team.get("strength", 0),
            )

            own_overall = own_team.get(
                "strength_overall_home",
                own_team.get("strength", 0),
            )

            opponent_attack = opponent_team.get(
                "strength_attack_away",
                opponent_team.get("strength", 0),
            )

            opponent_defence = opponent_team.get(
                "strength_defence_away",
                opponent_team.get("strength", 0),
            )

            opponent_overall = opponent_team.get(
                "strength_overall_away",
                opponent_team.get("strength", 0),
            )

        else:

            own_attack = own_team.get(
                "strength_attack_away",
                own_team.get("strength", 0),
            )

            own_defence = own_team.get(
                "strength_defence_away",
                own_team.get("strength", 0),
            )

            own_overall = own_team.get(
                "strength_overall_away",
                own_team.get("strength", 0),
            )

            opponent_attack = opponent_team.get(
                "strength_attack_home",
                opponent_team.get("strength", 0),
            )

            opponent_defence = opponent_team.get(
                "strength_defence_home",
                opponent_team.get("strength", 0),
            )

            opponent_overall = opponent_team.get(
                "strength_overall_home",
                opponent_team.get("strength", 0),
            )

        # ========================================================
        # FIXTURE SCORE
        # ========================================================

        attack_advantage = (
            own_attack - opponent_defence
        )

        defence_advantage = (
            own_defence - opponent_attack
        )

        overall_advantage = (
            own_overall - opponent_overall
        )

        difficulty = fixture["difficulty"]

        difficulty_factor = (
            1.0
            - ((difficulty - 1.0) / 10.0)
        )

        difficulty_factor = max(
            0.70,
            min(difficulty_factor, 1.10),
        )

        # ========================================================
        # MODEL INPUT
        # ========================================================

        model_row = build_feature_row({

            "xP": xP,

            "price": price,
            "was_home": fixture["was_home"],

            "points_last_3": points_last_3,
            "points_last_5": points_last_5,
            "points_avg_5": points_avg_5,

            "minutes_last_5": minutes_last_5,
            "starts_last_5": starts_last_5,

            "goals_last_5": goals_last_5,
            "assists_last_5": assists_last_5,

            "bps_avg_5": bps_avg_5,
            "influence_avg_5": influence_avg_5,
            "creativity_avg_5": creativity_avg_5,
            "threat_avg_5": threat_avg_5,
            "ict_index_avg_5": ict_index_avg_5,

            "form_5": form_5,

            "position": player["position"],
            "opponent_team": opponent_id,
        })

        rows.append({

            "player_id": player_id,
            "name": player_name,
            "position": player["position"],
            "team": team_name,
            "price": price,

            "opponent": fixture["opponent_name"],
            "was_home": fixture["was_home"],
            "difficulty": difficulty,

            "form": form,
            "minutes": minutes,

            "xP": xP,

            "availability": availability_multiplier,

            "attack_advantage": attack_advantage,
            "defence_advantage": defence_advantage,
            "overall_advantage": overall_advantage,

            "difficulty_factor": difficulty_factor,

            "model": model_row,
        })

    # ============================================================
    # CHECK
    # ============================================================

    print(
        f"\nSpillere matchet mot GW{gw}: {len(rows)}"
    )

    if not rows:

        print(
            "\n✗ Ingen spillere kunne matches mot fixtures."
        )

        return

    # ============================================================
    # MODEL INPUT
    # ============================================================

    model_rows = [
        row["model"]
        for row in rows
    ]

    X = pd.DataFrame(model_rows)

    expected_features = list(
        model.feature_names_in_
    )

    X = X[expected_features]

    # ============================================================
    # VERIFY MODEL INPUT
    # ============================================================

    print("\nMODEL INPUT")
    print("-" * 70)
    print(f"Features: {len(expected_features)}")
    print("✓ xP inkludert")
    print("✓ Feature order matches persisted model")

    # ============================================================
    # ML PREDICTION
    # ============================================================

    print("\nKjører ML-prediksjon...")
    print("-" * 70)

    ml_predictions = model.predict(X)

    # ============================================================
    # FINAL CONTEXT ADJUSTMENT
    # ============================================================

    results = []

    for row, ml_prediction in zip(
        rows,
        ml_predictions,
    ):

        prediction = float(
            max(0, ml_prediction)
        )

        # Fixture adjustment

        fixture_adjustment = (
            1.0
            + row["attack_advantage"] * 0.015
            + row["overall_advantage"] * 0.008
        )

        fixture_adjustment *= (
            row["difficulty_factor"]
        )

        fixture_adjustment = max(
            0.75,
            min(fixture_adjustment, 1.25),
        )

        prediction *= fixture_adjustment

        # Availability

        prediction *= (
            0.75
            + 0.25 * row["availability"]
        )

        # Form

        form_bonus = min(
            max(row["form"], 0),
            10,
        ) * 0.025

        prediction *= (
            1.0 + form_bonus
        )

        # Prediction limits

        prediction = max(
            0.0,
            min(prediction, 15.0),
        )

        # Value

        value = (
            prediction / row["price"]
            if row["price"] > 0
            else 0
        )

        results.append({

            "player_id": row["player_id"],
            "name": row["name"],
            "position": row["position"],
            "team": row["team"],
            "price": row["price"],

            "opponent": row["opponent"],
            "home": row["was_home"],
            "difficulty": row["difficulty"],

            "form": row["form"],
            "minutes": row["minutes"],

            "xP": round(
                row["xP"],
                3,
            ),

            "availability": round(
                row["availability"] * 100,
                1,
            ),

            "ml_prediction": round(
                float(ml_prediction),
                3,
            ),

            "predicted_points": round(
                prediction,
                3,
            ),

            "value": round(
                value,
                3,
            ),
        })

    result_df = pd.DataFrame(results)

    result_df = result_df.sort_values(
        "predicted_points",
        ascending=False,
    )

    # ============================================================
    # SAVE
    # ============================================================

    output_path = os.path.join(
        CURRENT_DIR,
        f"gw{gw}_predictions_v5.csv",
    )

    result_df.to_csv(
        output_path,
        index=False,
    )

    # ============================================================
    # TOP 30
    # ============================================================

    print("\nTOP 30 GW-PREDIKSJONER V5")
    print("-" * 70)

    for i, (_, row) in enumerate(
        result_df.head(30).iterrows(),
        start=1,
    ):

        home_away = (
            "H"
            if row["home"]
            else "A"
        )

        print(
            f"{i:2}. "
            f"{row['name']:<24} "
            f"{row['position']:<3} "
            f"{row['team']:<18} "
            f"vs {row['opponent']:<18} "
            f"{home_away}  "
            f"£{row['price']:.1f}m  "
            f"xP {row['xP']:.2f}  "
            f"→ {row['predicted_points']:.2f}"
        )

    # ============================================================
    # TOP VALUE
    # ============================================================

    print("\nTOP 15 VALUE")
    print("-" * 70)

    value_df = result_df[
        result_df["price"] <= 7.0
    ].sort_values(
        "value",
        ascending=False,
    )

    for i, (_, row) in enumerate(
        value_df.head(15).iterrows(),
        start=1,
    ):

        print(
            f"{i:2}. "
            f"{row['name']:<24} "
            f"{row['position']:<3} "
            f"£{row['price']:.1f}m  "
            f"xP {row['xP']:.2f}  "
            f"→ {row['predicted_points']:.2f} "
            f"({row['value']:.2f} pts/£m)"
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    print("\n" + "=" * 70)
    print("V5 PREDIKSJON FERDIG")
    print("=" * 70)

    print(
        f"\n✓ {len(result_df)} spillere predikert"
    )

    print(
        f"✓ GW{gw}"
    )

    print(
        f"✓ xP inkludert i modellinput"
    )

    print(
        f"✓ Lagret: {output_path}"
    )


if __name__ == "__main__":
    main()