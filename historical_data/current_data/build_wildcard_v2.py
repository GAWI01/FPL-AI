import pandas as pd
import numpy as np
from itertools import combinations
from pathlib import Path
import json
import math
import time


# ======================================================================
# FPL AI — WILDCARD OPTIMIZER V5
# Smart / fast optimizer
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent

PLAYERS_FILE = BASE_DIR / "players_current.csv"
FEATURES_FILE = BASE_DIR / "players_features_current_v2.csv"
PREDICTIONS_FILE = BASE_DIR / "gw2_predictions_v4.csv"

OUTPUT_FILE = BASE_DIR / "wildcard_gw2_v5.csv"
JSON_FILE = BASE_DIR / "wildcard_gw2_v5.json"

BUDGET = 100.0
MAX_PER_TEAM = 3

POSITION_COUNTS = {
    "GKP": 2,
    "DEF": 5,
    "MID": 5,
    "FWD": 3,
}

# Hvor mange kandidater vi beholder etter scoring.
# Dette gjør søket ekstremt mye mindre enn V4,
# samtidig som vi beholder mange sterke alternativer.
TOP_PER_POSITION = {
    "GKP": 12,
    "DEF": 30,
    "MID": 35,
    "FWD": 20,
}


# ======================================================================
# HJELPEFUNKSJONER
# ======================================================================

def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def normalize_position(value):
    value = str(value).upper().strip()

    mapping = {
        "GK": "GKP",
        "GKP": "GKP",
        "DEF": "DEF",
        "MID": "MID",
        "FWD": "FWD",
        "ATT": "FWD",
    }

    return mapping.get(value, value)


def get_predicted_points(row):
    """
    Finn prediksjonskolonnen uavhengig av nøyaktig navn.
    """
    possible = [
        "predicted_points",
        "prediction",
        "predicted",
        "expected_points",
        "gw_prediction",
        "predicted_gw_points",
    ]

    for col in possible:
        if col in row.index:
            return safe_float(row[col])

    raise ValueError(
        "Fant ingen prediksjonskolonne i predictions-filen. "
        f"Kolonner: {list(row.index)}"
    )


def get_feature(row, names, default=0.0):
    for name in names:
        if name in row.index:
            return safe_float(row[name], default)
    return default


def availability_multiplier(row):
    availability = str(
        row.get("availability", row.get("status", "AVAILABLE"))
    ).upper()

    if availability == "UNAVAILABLE":
        return 0.0

    if availability == "RISK":
        return 0.55

    if availability == "MINOR_RISK":
        return 0.80

    return 1.0


def rotation_multiplier(row):
    risk = str(row.get("rotation_risk", "MEDIUM")).upper()

    multipliers = {
        "LOW": 1.00,
        "MEDIUM": 0.93,
        "HIGH": 0.82,
        "VERY_HIGH": 0.68,
        "OUT": 0.00,
    }

    return multipliers.get(risk, 0.90)


def calculate_player_score(row):
    """
    V5-score.

    Vi bruker ML-prediksjonen som hovedsignal,
    men korrigerer den for:
      - availability
      - xMins
      - start probability
      - rotation risk
      - value

    Dette er IKKE ment å overstyre ML-modellen fullstendig.
    Det skal bare hindre at usikre spillere blir overvurdert.
    """

    prediction = get_predicted_points(row)

    availability = availability_multiplier(row)
    rotation = rotation_multiplier(row)

    xmins = get_feature(
        row,
        ["xmins", "expected_minutes", "expected_mins"],
        80.0,
    )

    start_probability = get_feature(
        row,
        ["start_probability", "probability_start"],
        0.80,
    )

    # Begrens verdiene så én dårlig datakolonne ikke ødelegger modellen.
    xmins_factor = np.clip(xmins / 90.0, 0.0, 1.0)
    start_factor = np.clip(start_probability, 0.0, 1.0)

    # Kombinerer sannsynlighet for tilgjengelighet,
    # spilletid og start.
    minutes_factor = (
        0.55 * xmins_factor +
        0.45 * start_factor
    )

    score = (
        prediction
        * availability
        * rotation
        * minutes_factor
    )

    return float(score)


def make_candidate_dataframe(players, features, predictions):
    """
    Slår sammen alle datakilder.
    """

    df = players.copy()

    # --------------------------------------------------------------
    # Features
    # --------------------------------------------------------------

    feature_cols = [
        c for c in features.columns
        if c not in df.columns or c == "player_id"
    ]

    if "player_id" in features.columns:
        df = df.merge(
            features[feature_cols],
            on="player_id",
            how="left",
            suffixes=("", "_feature"),
        )

    # --------------------------------------------------------------
    # Predictions
    # --------------------------------------------------------------

    if "player_id" not in predictions.columns:
        raise ValueError(
            "Predictions-filen mangler player_id."
        )

    prediction_columns = [
        c for c in predictions.columns
        if c != "player_id"
    ]

    df = df.merge(
        predictions[
            ["player_id"] + prediction_columns
        ],
        on="player_id",
        how="left",
        suffixes=("", "_prediction"),
    )

    return df


# ======================================================================
# KANDIDATER
# ======================================================================

def prepare_candidates(df):

    df = df.copy()

    df["position"] = df["position"].apply(normalize_position)

    # Fjern spillere uten gyldig posisjon.
    df = df[
        df["position"].isin(
            POSITION_COUNTS.keys()
        )
    ].copy()

    # --------------------------------------------------------------
    # Score
    # --------------------------------------------------------------

    df["base_score"] = df.apply(
        calculate_player_score,
        axis=1,
    )

    df["prediction_points"] = df.apply(
        get_predicted_points,
        axis=1,
    )

    # --------------------------------------------------------------
    # Value
    # --------------------------------------------------------------

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce",
    ).fillna(0)

    df["value_score"] = (
        df["base_score"] /
        df["price"].clip(lower=0.1)
    )

    # --------------------------------------------------------------
    # Availability
    # --------------------------------------------------------------

    df["availability_mult"] = df.apply(
        availability_multiplier,
        axis=1,
    )

    df["rotation_mult"] = df.apply(
        rotation_multiplier,
        axis=1,
    )

    # Bare tilgjengelige spillere.
    df = df[
        df["availability_mult"] > 0
    ].copy()

    # --------------------------------------------------------------
    # Smart candidate selection
    # --------------------------------------------------------------

    selected = []

    for position, limit in TOP_PER_POSITION.items():

        group = df[
            df["position"] == position
        ].copy()

        if group.empty:
            continue

        # Litt mer enn ren predicted points:
        # base score + en liten value-komponent.
        group["optimizer_score"] = (
            group["base_score"]
            + 0.10 * group["value_score"]
        )

        group = group.sort_values(
            "optimizer_score",
            ascending=False,
        )

        selected.append(
            group.head(limit)
        )

    if not selected:
        raise RuntimeError(
            "Ingen gyldige kandidater."
        )

    candidates = pd.concat(
        selected,
        ignore_index=True,
    )

    return candidates


# ======================================================================
# KOMBINASJONER
# ======================================================================

def build_position_combinations(
    group,
    count,
    max_combinations=None,
):
    """
    Lager kombinasjoner for én posisjon.

    I motsetning til V4 lager vi IKKE enorme
    DataFrames for hver kombinasjon.
    Vi bruker tuples/dicts direkte.
    """

    players = group.to_dict("records")

    combos = []

    for combo in combinations(players, count):

        teams = [
            str(p["team"])
            for p in combo
        ]

        team_counts = {}

        for team in teams:
            team_counts[team] = (
                team_counts.get(team, 0) + 1
            )

        # Kan aldri ha mer enn 3 fra samme lag.
        if any(
            count_team > MAX_PER_TEAM
            for count_team in team_counts.values()
        ):
            continue

        cost = sum(
            safe_float(p["price"])
            for p in combo
        )

        score = sum(
            safe_float(p["base_score"])
            for p in combo
        )

        combos.append({
            "players": combo,
            "cost": cost,
            "score": score,
            "teams": team_counts,
        })

    combos.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    if max_combinations:
        combos = combos[:max_combinations]

    return combos


# ======================================================================
# KOMBINER POSISJONER
# ======================================================================

def can_combine(a, b):

    if a["cost"] + b["cost"] > BUDGET:
        return False

    teams = dict(a["teams"])

    for team, count in b["teams"].items():
        teams[team] = (
            teams.get(team, 0) + count
        )

        if teams[team] > MAX_PER_TEAM:
            return False

    return True


def merge_groups(a, b):

    teams = dict(a["teams"])

    for team, count in b["teams"].items():
        teams[team] = (
            teams.get(team, 0) + count
        )

    return {
        "players": a["players"] + b["players"],
        "cost": a["cost"] + b["cost"],
        "score": a["score"] + b["score"],
        "teams": teams,
    }


def combine_position_groups(groups):

    """
    Smart beam-search.

    Dette er nøkkelen til V5.

    I stedet for:

        45 × 5000 × 5000 × 816

    holder vi bare de beste del-løsningene
    underveis.

    Dermed får vi svært mye lavere kjøretid.
    """

    states = [
        {
            "players": tuple(),
            "cost": 0.0,
            "score": 0.0,
            "teams": {},
        }
    ]

    # Hvor mange del-løsninger vi beholder.
    BEAM_WIDTH = 15000

    position_order = [
        "GKP",
        "DEF",
        "MID",
        "FWD",
    ]

    for position in position_order:

        combos = groups[position]

        next_states = []

        for state in states:

            for combo in combos:

                cost = (
                    state["cost"]
                    + combo["cost"]
                )

                if cost > BUDGET:
                    continue

                teams = dict(state["teams"])

                valid = True

                for team, count in combo["teams"].items():

                    new_count = (
                        teams.get(team, 0)
                        + count
                    )

                    if new_count > MAX_PER_TEAM:
                        valid = False
                        break

                    teams[team] = new_count

                if not valid:
                    continue

                next_states.append({
                    "players": (
                        state["players"]
                        + combo["players"]
                    ),
                    "cost": cost,
                    "score": (
                        state["score"]
                        + combo["score"]
                    ),
                    "teams": teams,
                })

        if not next_states:
            raise RuntimeError(
                f"Ingen gyldige løsninger etter {position}."
            )

        # ----------------------------------------------------------
        # Beam pruning
        # ----------------------------------------------------------

        next_states.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        states = next_states[:BEAM_WIDTH]

        print(
            f"  {position}: "
            f"{len(next_states):,} mulige → "
            f"{len(states):,} beholdt"
        )

    states.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return states[0]


# ======================================================================
# STARTELLEVER / KAPTEIN
# ======================================================================

def calculate_starting_xi(squad):

    """
    FPL 15-mannslag.

    Vi velger den beste lovlige XI-en
    basert på optimizer score.
    """

    goalkeepers = [
        p for p in squad
        if normalize_position(p["position"]) == "GKP"
    ]

    defenders = [
        p for p in squad
        if normalize_position(p["position"]) == "DEF"
    ]

    midfielders = [
        p for p in squad
        if normalize_position(p["position"]) == "MID"
    ]

    forwards = [
        p for p in squad
        if normalize_position(p["position"]) == "FWD"
    ]

    # Minimum:
    # 1 GKP
    # 3 DEF
    # 2 MID
    # 1 FWD
    #
    # Deretter fyller vi opp de beste spillerne.

    goalkeeper = max(
        goalkeepers,
        key=lambda p: p["base_score"],
    )

    defenders_sorted = sorted(
        defenders,
        key=lambda p: p["base_score"],
        reverse=True,
    )

    midfielders_sorted = sorted(
        midfielders,
        key=lambda p: p["base_score"],
        reverse=True,
    )

    forwards_sorted = sorted(
        forwards,
        key=lambda p: p["base_score"],
        reverse=True,
    )

    starting = [
        goalkeeper,
        *defenders_sorted[:3],
        *midfielders_sorted[:2],
        forwards_sorted[0],
    ]

    remaining = [
        p for p in squad
        if p not in starting
    ]

    # Fyll de resterende plassene.
    while len(starting) < 11 and remaining:

        best = None

        for p in remaining:

            pos = normalize_position(
                p["position"]
            )

            current_def = sum(
                normalize_position(x["position"]) == "DEF"
                for x in starting
            )

            current_mid = sum(
                normalize_position(x["position"]) == "MID"
                for x in starting
            )

            current_fwd = sum(
                normalize_position(x["position"]) == "FWD"
                for x in starting
            )

            if pos == "DEF":
                if current_def >= 5:
                    continue

            elif pos == "MID":
                if current_mid >= 5:
                    continue

            elif pos == "FWD":
                if current_fwd >= 3:
                    continue

            else:
                continue

            if (
                best is None
                or p["base_score"] > best["base_score"]
            ):
                best = p

        if best is None:
            break

        starting.append(best)
        remaining.remove(best)

    bench = [
        p for p in squad
        if p not in starting
    ]

    bench.sort(
        key=lambda p: p["base_score"],
        reverse=True,
    )

    return starting, bench


def captain_choices(starting):

    outfield = [
        p for p in starting
        if normalize_position(p["position"]) != "GKP"
    ]

    outfield.sort(
        key=lambda p: p["base_score"],
        reverse=True,
    )

    if not outfield:
        return None, None

    captain = outfield[0]

    vice = (
        outfield[1]
        if len(outfield) > 1
        else None
    )

    return captain, vice


# ======================================================================
# OUTPUT
# ======================================================================

def save_results(
    squad,
    starting,
    bench,
    captain,
    vice,
    score,
):

    rows = []

    starting_ids = {
        p["player_id"]
        for p in starting
    }

    bench_ids = {
        p["player_id"]
        for p in bench
    }

    for p in squad:

        if p["player_id"] in starting_ids:
            role = "STARTER"

        elif p["player_id"] in bench_ids:
            role = "BENCH"

        else:
            role = "SQUAD"

        rows.append({
            "player_id": p["player_id"],
            "name": p["name"],
            "position": p["position"],
            "team": p["team"],
            "price": p["price"],
            "predicted_points": p["prediction_points"],
            "optimizer_score": p["base_score"],
            "xmins": get_feature(
                p,
                ["xmins", "expected_minutes"],
                0,
            ),
            "availability": p.get(
                "availability",
                p.get("status", ""),
            ),
            "rotation_risk": p.get(
                "rotation_risk",
                "",
            ),
            "role": role,
            "captain": (
                p["player_id"] == captain["player_id"]
                if captain
                else False
            ),
            "vice_captain": (
                p["player_id"] == vice["player_id"]
                if vice
                else False
            ),
        })

    result_df = pd.DataFrame(rows)

    result_df = result_df.sort_values(
        ["role", "optimizer_score"],
        ascending=[True, False],
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # JSON for future AI integration
    # --------------------------------------------------------------

    output = {
        "gameweek": 2,
        "optimizer_version": "V5",
        "budget": BUDGET,
        "total_cost": round(
            sum(
                safe_float(p["price"])
                for p in squad
            ),
            2,
        ),
        "expected_points_score": round(
            score,
            3,
        ),
        "squad": [],
        "starting_xi": [
            p["name"]
            for p in starting
        ],
        "bench": [
            p["name"]
            for p in bench
        ],
        "captain": (
            captain["name"]
            if captain
            else None
        ),
        "vice_captain": (
            vice["name"]
            if vice
            else None
        ),
    }

    for p in squad:

        output["squad"].append({
            "player_id": int(p["player_id"]),
            "name": p["name"],
            "position": p["position"],
            "team": p["team"],
            "price": safe_float(p["price"]),
            "predicted_points": safe_float(
                p["prediction_points"]
            ),
            "optimizer_score": safe_float(
                p["base_score"]
            ),
            "xmins": get_feature(
                p,
                ["xmins", "expected_minutes"],
                0,
            ),
            "availability": str(
                p.get(
                    "availability",
                    p.get("status", ""),
                )
            ),
            "rotation_risk": str(
                p.get(
                    "rotation_risk",
                    "",
                )
            ),
        })

    with open(
        JSON_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return result_df


# ======================================================================
# MAIN
# ======================================================================

def main():

    start_time = time.perf_counter()

    print("=" * 70)
    print("FPL AI — WILDCARD OPTIMIZER V5")
    print("=" * 70)

    print("Laster data...")

    players = pd.read_csv(
        PLAYERS_FILE
    )

    features = pd.read_csv(
        FEATURES_FILE
    )

    predictions = pd.read_csv(
        PREDICTIONS_FILE
    )

    print(
        f"✓ Spillere: {len(players)}"
    )

    print(
        f"✓ Features: {len(features)}"
    )

    print(
        f"✓ Prediksjoner: {len(predictions)}"
    )

    print()
    print("Forbereder spillere...")

    df = make_candidate_dataframe(
        players,
        features,
        predictions,
    )

    candidates = prepare_candidates(
        df
    )

    print(
        f"✓ Aktive kandidater: {len(candidates)}"
    )

    print()
    print("Kandidater per posisjon:")

    for position in POSITION_COUNTS:

        count = len(
            candidates[
                candidates["position"] == position
            ]
        )

        print(
            f"  {position}: "
            f"{count} spillere"
        )

    # --------------------------------------------------------------
    # Position combinations
    # --------------------------------------------------------------

    print()
    print("Bygger posisjonskombinasjoner...")

    groups = {}

    combination_limits = {
        "GKP": 100,
        "DEF": 8000,
        "MID": 8000,
        "FWD": 3000,
    }

    for position, count in POSITION_COUNTS.items():

        group = candidates[
            candidates["position"] == position
        ].copy()

        combos = build_position_combinations(
            group,
            count,
            max_combinations=combination_limits[
                position
            ],
        )

        groups[position] = combos

        print(
            f"  ✓ {position}: "
            f"{len(combos):,} kombinasjoner"
        )

    # --------------------------------------------------------------
    # Optimize
    # --------------------------------------------------------------

    print()
    print("Søker etter beste Wildcard...")
    print()
    print("Kombinerer posisjoner...")

    best = combine_position_groups(
        groups
    )

    squad = list(
        best["players"]
    )

    squad.sort(
        key=lambda p: (
            POSITION_COUNTS.get(
                normalize_position(
                    p["position"]
                ),
                99,
            ),
            -safe_float(
                p["base_score"]
            ),
        )
    )

    starting, bench = calculate_starting_xi(
        squad
    )

    captain, vice = captain_choices(
        starting
    )

    # --------------------------------------------------------------
    # Display
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("BESTE WILDCARD V5")
    print("=" * 70)

    print()

    total_cost = sum(
        safe_float(p["price"])
        for p in squad
    )

    print(
        f"Total cost: £{total_cost:.1f}m"
    )

    print(
        f"Optimizer score: "
        f"{best['score']:.2f}"
    )

    print()

    for position in [
        "GKP",
        "DEF",
        "MID",
        "FWD",
    ]:

        print(position)

        players_position = [
            p for p in squad
            if normalize_position(
                p["position"]
            ) == position
        ]

        for p in players_position:

            role = (
                "START"
                if p in starting
                else "BENCH"
            )

            print(
                f"  {role:5} "
                f"{p['name']:<22} "
                f"{p['team']:<18} "
                f"£{safe_float(p['price']):.1f}m  "
                f"→ {safe_float(p['prediction_points']):.2f}"
            )

    print()

    if captain:
        print(
            f"CAPTAIN:       {captain['name']}"
        )

    if vice:
        print(
            f"VICE CAPTAIN:  {vice['name']}"
        )

    print()
    print("BENK")

    for p in bench:
        print(
            f"  {p['name']:<22} "
            f"{p['team']:<18} "
            f"→ {safe_float(p['prediction_points']):.2f}"
        )

    # --------------------------------------------------------------
    # Save
    # --------------------------------------------------------------

    result_df = save_results(
        squad,
        starting,
        bench,
        captain,
        vice,
        best["score"],
    )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print("=" * 70)
    print("V5 FERDIG")
    print("=" * 70)

    print(
        f"✓ Lagret: {OUTPUT_FILE}"
    )

    print(
        f"✓ AI JSON: {JSON_FILE}"
    )

    print(
        f"✓ Kjøretid: {elapsed:.2f} sekunder"
    )

    print()


if __name__ == "__main__":
    main()