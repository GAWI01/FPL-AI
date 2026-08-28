import pandas as pd
from pathlib import Path

SEASONS = [
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
]

BASE_DIR = Path("historical_data")


def build_features(season):

    season_dir = BASE_DIR / season

    gw_file = season_dir / "merged_gw.csv"
    mapping_file = (
        season_dir
        / "understat"
        / "player_mapping.csv"
    )

    print()
    print("=" * 65)
    print(f"--- FEATURES {season} ---")
    print("=" * 65)

    if not gw_file.exists():
        print("✗ merged_gw.csv mangler")
        return

    print("Leser Gameweek-data...")
    gw = pd.read_csv(gw_file)

    print(f"Gameweek-rader: {len(gw)}")

    # ---------------------------------------------------------
    # Finn spiller-ID
    # ---------------------------------------------------------

    if "element" in gw.columns:
        gw["player_id"] = gw["element"]
    elif "id" in gw.columns:
        gw["player_id"] = gw["id"]
    else:
        print("✗ Fant ingen spiller-ID")
        print("Kolonner:", list(gw.columns))
        return

    # ---------------------------------------------------------
    # Numeriske kolonner
    # ---------------------------------------------------------

    numeric_columns = [
        "minutes",
        "goals_scored",
        "assists",
        "clean_sheets",
        "goals_conceded",
        "own_goals",
        "penalties_saved",
        "penalties_missed",
        "yellow_cards",
        "red_cards",
        "saves",
        "bonus",
        "bps",
        "influence",
        "creativity",
        "threat",
        "ict_index",
        "total_points",
        "value",
    ]

    for col in numeric_columns:
        if col in gw.columns:
            gw[col] = pd.to_numeric(
                gw[col],
                errors="coerce"
            ).fillna(0)

    # ---------------------------------------------------------
    # Sorter kronologisk
    # ---------------------------------------------------------

    if "GW" in gw.columns:
        gw = gw.sort_values(
            ["player_id", "GW"]
        )

    elif "round" in gw.columns:
        gw = gw.sort_values(
            ["player_id", "round"]
        )

    # ---------------------------------------------------------
    # Rolling features
    # ---------------------------------------------------------

    print("Bygger rolling features...")

    grouped = gw.groupby("player_id", group_keys=False)

    # Poeng siste 3 GW
    gw["points_last_3"] = (
        grouped["total_points"]
        .transform(
            lambda x: x.shift(1)
            .rolling(3, min_periods=1)
            .sum()
        )
    )

    # Poeng siste 5 GW
    gw["points_last_5"] = (
        grouped["total_points"]
        .transform(
            lambda x: x.shift(1)
            .rolling(5, min_periods=1)
            .sum()
        )
    )

    # Gjennomsnitt siste 5
    gw["points_avg_5"] = (
        grouped["total_points"]
        .transform(
            lambda x: x.shift(1)
            .rolling(5, min_periods=1)
            .mean()
        )
    )

    # Minutter siste 5
    gw["minutes_last_5"] = (
        grouped["minutes"]
        .transform(
            lambda x: x.shift(1)
            .rolling(5, min_periods=1)
            .sum()
        )
    )

    # Starter sannsynlighet / tilgjengelighet
    gw["starts_last_5"] = (
        grouped["minutes"]
        .transform(
            lambda x: x.shift(1)
            .rolling(5, min_periods=1)
            .apply(
                lambda y: (y >= 60).sum(),
                raw=True
            )
        )
    )

    # ---------------------------------------------------------
    # Offensive features
    # ---------------------------------------------------------

    if "goals_scored" in gw.columns:

        gw["goals_last_5"] = (
            grouped["goals_scored"]
            .transform(
                lambda x: x.shift(1)
                .rolling(5, min_periods=1)
                .sum()
            )
        )

    if "assists" in gw.columns:

        gw["assists_last_5"] = (
            grouped["assists"]
            .transform(
                lambda x: x.shift(1)
                .rolling(5, min_periods=1)
                .sum()
            )
        )

    # ---------------------------------------------------------
    # BPS / ICT
    # ---------------------------------------------------------

    for col in [
        "bps",
        "influence",
        "creativity",
        "threat",
        "ict_index"
    ]:

        if col in gw.columns:

            gw[f"{col}_avg_5"] = (
                grouped[col]
                .transform(
                    lambda x: x.shift(1)
                    .rolling(5, min_periods=1)
                    .mean()
                )
            )

    # ---------------------------------------------------------
    # Form
    # ---------------------------------------------------------

    gw["form_5"] = (
        gw["points_avg_5"]
        .fillna(0)
    )

    # ---------------------------------------------------------
    # Pris
    # ---------------------------------------------------------

    if "value" in gw.columns:

        gw["price"] = (
            gw["value"] / 10
        )

    # ---------------------------------------------------------
    # Lagre
    # ---------------------------------------------------------

    output_file = (
        season_dir
        / "features.csv"
    )

    gw.to_csv(
        output_file,
        index=False
    )

    print()
    print(f"✓ Lagret: {output_file}")
    print(f"✓ Features: {len(gw.columns)}")
    print(f"✓ Rader: {len(gw)}")


def main():

    print("=" * 65)
    print("FPL AI — FEATURE ENGINEERING V1")
    print("=" * 65)

    for season in SEASONS:
        build_features(season)

    print()
    print("=" * 65)
    print("FEATURE ENGINEERING FERDIG")
    print("=" * 65)


if __name__ == "__main__":
    main()