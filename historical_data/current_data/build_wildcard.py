import os
import joblib
import pandas as pd
from itertools import combinations

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(BASE, "historical_data", "current_data")
MODEL_PATH = os.path.join(BASE, "models", "fpl_model_v1.pkl")

BUDGET = 100.0
SQUAD_SIZE = 15
MAX_PER_TEAM = 3

POSITION_LIMITS = {
    "GKP": (2, 2),
    "DEF": (5, 5),
    "MID": (5, 5),
    "FWD": (3, 3),
}


def load_data():
    print("Laster data...")

    players = pd.read_csv(os.path.join(DATA, "players_current.csv"))
    predictions = pd.read_csv(
        os.path.join(DATA, "gw2_predictions_v4.csv")
    )

    teams = pd.read_csv(os.path.join(DATA, "teams_current.csv"))

    print(f"✓ Spillere: {len(players)}")
    print(f"✓ Prediksjoner: {len(predictions)}")

    return players, predictions, teams


def prepare_players(players, predictions):
    df = players.merge(
        predictions[["player_id", "predicted_points"]],
        on="player_id",
        how="left",
    )

    df["predicted_points"] = pd.to_numeric(
        df["predicted_points"], errors="coerce"
    ).fillna(0)

    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    ).fillna(0)

    df["value"] = df["predicted_points"] / df["price"].replace(0, 999)

    # Spillere som ikke kan spille bør ikke være kandidater
    if "status" in df.columns:
        df = df[
            ~df["status"].isin(
                ["u", "s", "i", "d"]
            )
        ].copy()

    if "chance_of_playing_next_round" in df.columns:
        chance = pd.to_numeric(
            df["chance_of_playing_next_round"],
            errors="coerce"
        )

        df = df[
            chance.isna() | (chance >= 75)
        ].copy()

    return df


def choose_candidates(df):
    """
    Begrens kandidatlisten slik at optimizer-en ikke må teste
    alle mulige kombinasjoner av 616 spillere.
    """

    candidates = []

    for position in POSITION_LIMITS:
        pos = df[df["position"] == position].copy()

        # Ta de beste på forventede poeng + value
        top_points = pos.nlargest(35, "predicted_points")
        top_value = pos.nlargest(20, "value")

        combined = pd.concat(
            [top_points, top_value]
        ).drop_duplicates("player_id")

        candidates.append(combined)

    result = pd.concat(candidates).drop_duplicates("player_id")

    print(f"✓ Kandidater til optimizer: {len(result)}")

    return result


def valid_position_counts(squad):
    counts = squad["position"].value_counts()

    for position, (minimum, maximum) in POSITION_LIMITS.items():
        count = counts.get(position, 0)

        if count < minimum or count > maximum:
            return False

    return True


def valid_team_limit(squad):
    counts = squad["team"].value_counts()

    return counts.max() <= MAX_PER_TEAM


def find_best_squad(df):
    """
    Søker etter den beste lovlige 15-mannstroppen.

    Objektivet er primært forventede poeng,
    men vi gir en liten bonus til verdi.
    """

    groups = {}

    for position in POSITION_LIMITS:
        groups[position] = list(
            df[df["position"] == position].itertuples()
        )

    best = None
    best_score = -999999

    print("\nSøker etter beste Wildcard...")

    # 2 keepere
    for gks in combinations(groups["GKP"], 2):

        gk_cost = sum(p.price for p in gks)

        if gk_cost >= BUDGET:
            continue

        # 5 forsvarere
        for defs in combinations(groups["DEF"], 5):

            current = list(gks) + list(defs)

            if sum(p.price for p in current) >= BUDGET:
                continue

            # 5 midtbanespillere
            for mids in combinations(groups["MID"], 5):

                current2 = current + list(mids)

                cost2 = sum(p.price for p in current2)

                if cost2 >= BUDGET:
                    continue

                # 3 spisser
                for fwds in combinations(groups["FWD"], 3):

                    squad = current2 + list(fwds)

                    cost = sum(p.price for p in squad)

                    if cost > BUDGET:
                        continue

                    squad_df = pd.DataFrame(
                        [p._asdict() for p in squad]
                    )

                    if not valid_team_limit(squad_df):
                        continue

                    points = squad_df[
                        "predicted_points"
                    ].sum()

                    value_bonus = squad_df[
                        "value"
                    ].sum() * 0.05

                    score = points + value_bonus

                    if score > best_score:
                        best_score = score
                        best = squad_df.copy()

    return best, best_score


def optimize_starting_xi(squad):
    """
    Velger en sannsynlig optimal startellever.

    FPL-formasjon:
    1 GK
    minst 3 DEF
    minst 2 MID
    minst 1 FWD
    """

    gk = squad[squad["position"] == "GKP"].nlargest(
        1, "predicted_points"
    )

    defs = squad[squad["position"] == "DEF"].nlargest(
        5, "predicted_points"
    )

    mids = squad[squad["position"] == "MID"].nlargest(
        5, "predicted_points"
    )

    fwds = squad[squad["position"] == "FWD"].nlargest(
        3, "predicted_points"
    )

    starters = []

    starters.extend(gk.to_dict("records"))

    # Start med minimumsformasjon
    starters.extend(
        defs.nlargest(3, "predicted_points").to_dict("records")
    )

    starters.extend(
        mids.nlargest(2, "predicted_points").to_dict("records")
    )

    starters.extend(
        fwds.nlargest(1, "predicted_points").to_dict("records")
    )

    remaining = squad[
        ~squad["player_id"].isin(
            [p["player_id"] for p in starters]
        )
    ].copy()

    # Fyll de resterende 4 plassene med høyest prediksjon
    remaining = remaining.nlargest(
        4, "predicted_points"
    )

    starters.extend(
        remaining.to_dict("records")
    )

    return pd.DataFrame(starters)


def main():

    print("=" * 70)
    print("FPL AI — WILDCARD OPTIMIZER V1")
    print("=" * 70)

    players, predictions, teams = load_data()

    df = prepare_players(players, predictions)

    print(f"✓ Aktive kandidater: {len(df)}")

    candidates = choose_candidates(df)

    squad, score = find_best_squad(candidates)

    if squad is None:
        print("\n✗ Fant ikke gyldig lag.")
        return

    squad = squad.sort_values(
        ["position", "predicted_points"],
        ascending=[True, False]
    )

    starters = optimize_starting_xi(squad)

    bench = squad[
        ~squad["player_id"].isin(
            starters["player_id"]
        )
    ].copy()

    starters = starters.sort_values(
        "predicted_points",
        ascending=False
    )

    bench = bench.sort_values(
        "predicted_points",
        ascending=False
    )

    total_cost = squad["price"].sum()
    total_points = squad["predicted_points"].sum()

    print("\n" + "=" * 70)
    print("BESTE WILDCARD-LAG")
    print("=" * 70)

    print(f"\nBudsjett: £{BUDGET:.1f}m")
    print(f"Kostnad:  £{total_cost:.1f}m")
    print(f"IGJEN:     £{BUDGET - total_cost:.1f}m")
    print(f"Forventet GW2: {total_points:.2f}")

    print("\nSTART XI")
    print("-" * 70)

    for _, p in starters.iterrows():
        print(
            f"{p['position']:3} "
            f"{p['name']:<25} "
            f"{p['team']:<18} "
            f"£{p['price']:.1f}m  "
            f"→ {p['predicted_points']:.2f}"
        )

    print("\nBENK")
    print("-" * 70)

    for _, p in bench.iterrows():
        print(
            f"{p['position']:3} "
            f"{p['name']:<25} "
            f"{p['team']:<18} "
            f"£{p['price']:.1f}m  "
            f"→ {p['predicted_points']:.2f}"
        )

    print("\n" + "=" * 70)

    output = squad.copy()

    output["starting_xi"] = output["player_id"].isin(
        starters["player_id"]
    )

    output["bench"] = ~output["starting_xi"]

    output = output[
        [
            "player_id",
            "name",
            "position",
            "team",
            "price",
            "predicted_points",
            "value",
            "starting_xi",
            "bench",
        ]
    ]

    output_path = os.path.join(
        DATA,
        "wildcard_team_v1.csv"
    )

    output.to_csv(
        output_path,
        index=False
    )

    print(f"\n✓ Lagret: {output_path}")
    print("✓ Wildcard optimizer ferdig")


if __name__ == "__main__":
    main()