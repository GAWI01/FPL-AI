import pandas as pd
from pathlib import Path
import re
import unicodedata

SEASONS = [
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
]

BASE_DIR = Path("historical_data")


def normalize_name(name):
    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    # Fjern aksenter
    name = unicodedata.normalize("NFKD", name)
    name = "".join(
        c for c in name
        if not unicodedata.combining(c)
    )

    # Fjern spesialtegn
    name = re.sub(r"[^a-z0-9\s]", "", name)

    # Fjern ekstra mellomrom
    name = " ".join(name.split())

    return name


def build_mapping(season):

    season_dir = BASE_DIR / season

    fpl_file = season_dir / "players_raw.csv"
    understat_file = season_dir / "understat" / "understat_player.csv"

    print()
    print(f"--- {season} ---")

    if not fpl_file.exists():
        print("✗ FPL-data mangler")
        return

    if not understat_file.exists():
        print("✗ Understat-data mangler")
        return

    print("Leser FPL-data...")
    fpl = pd.read_csv(fpl_file)

    print("Leser Understat-data...")
    understat = pd.read_csv(understat_file)

    # ---------------------------------------------------------
    # FPL
    # ---------------------------------------------------------

    fpl["full_name"] = (
        fpl["first_name"].fillna("")
        + " "
        + fpl["second_name"].fillna("")
    ).str.strip()

    fpl["match_name"] = (
        fpl["full_name"]
        .apply(normalize_name)
    )

    # Gi FPL-ID et un unikt navn FØR merge
    fpl_for_merge = fpl[
        [
            "id",
            "full_name",
            "match_name"
        ]
    ].copy()

    fpl_for_merge = fpl_for_merge.rename(
        columns={
            "id": "fpl_id",
            "full_name": "fpl_name"
        }
    )

    # ---------------------------------------------------------
    # UNDERSTAT
    # ---------------------------------------------------------

    understat["match_name"] = (
        understat["player_name"]
        .apply(normalize_name)
    )

    print(f"FPL-spillere:       {len(fpl)}")
    print(f"Understat-spillere: {len(understat)}")
    print("Matcher spillere...")

    # ---------------------------------------------------------
    # MERGE
    # ---------------------------------------------------------

    merged = understat.merge(
        fpl_for_merge,
        on="match_name",
        how="left"
    )

    # ---------------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------------

    output = merged[
        [
            "fpl_id",
            "fpl_name",
            "player_name",
            "id",
            "match_name"
        ]
    ].copy()

    output = output.rename(
        columns={
            "player_name": "understat_name",
            "id": "understat_id",
            "match_name": "normalized_name"
        }
    )

    output_file = (
        season_dir
        / "understat"
        / "player_mapping.csv"
    )

    output.to_csv(
        output_file,
        index=False
    )

    # ---------------------------------------------------------
    # STATISTIKK
    # ---------------------------------------------------------

    matched = output["fpl_id"].notna().sum()
    total = len(output)
    unmatched = total - matched

    print()
    print(f"Understat-spillere: {total}")
    print(f"Matchet:            {matched}")
    print(f"Ikke matchet:       {unmatched}")
    print(f"✓ Lagret: {output_file}")

    if unmatched > 0:

        print()
        print("FØRSTE 20 IKKE-MATCHER:")

        unmatched_players = output[
            output["fpl_id"].isna()
        ]

        for name in unmatched_players[
            "understat_name"
        ].head(20):

            print(f"  - {name}")


def main():

    print("=" * 65)
    print("FPL AI — PLAYER ID MAPPING")
    print("=" * 65)

    for season in SEASONS:
        build_mapping(season)

    print()
    print("=" * 65)
    print("MAPPING FERDIG")
    print("=" * 65)


if __name__ == "__main__":
    main()