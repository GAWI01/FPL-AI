import pandas as pd
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parent

PLAYERS_FILE = BASE / "players_current.csv"
OUTPUT_FILE = BASE / "gw1_history.csv"

API_URL = "https://fantasy.premierleague.com/api/event/1/live/"


def main():
    print("=" * 70)
    print("FPL AI — GW1 PLAYER HISTORY")
    print("=" * 70)

    print("\nLeser current player-data...")
    players = pd.read_csv(PLAYERS_FILE)
    print(f"✓ Spillere: {len(players)}")

    print("\nHenter GW1 live-data fra FPL API...")
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()

    data = response.json()
    elements = data.get("elements", [])

    print(f"✓ GW1 records: {len(elements)}")

    if not elements:
        print("\n✗ Ingen GW1-data mottatt")
        return

    history = []

    for element in elements:
        stats = element.get("stats", {})

        history.append({
            "player_id": element.get("id"),
            "minutes_gw1": stats.get("minutes", 0),
            "goals_gw1": stats.get("goals_scored", 0),
            "assists_gw1": stats.get("assists", 0),
            "clean_sheets_gw1": stats.get("clean_sheets", 0),
            "goals_conceded_gw1": stats.get("goals_conceded", 0),
            "saves_gw1": stats.get("saves", 0),
            "bonus_gw1": stats.get("bonus", 0),
            "bps_gw1": stats.get("bps", 0),
            "total_points_gw1": stats.get("total_points", 0),
        })

    gw1 = pd.DataFrame(history)

    # Merge with current player information
    df = players.merge(
        gw1,
        on="player_id",
        how="left"
    )

    # Missing players get zero minutes/points
    numeric_columns = [
        "minutes_gw1",
        "goals_gw1",
        "assists_gw1",
        "clean_sheets_gw1",
        "goals_conceded_gw1",
        "saves_gw1",
        "bonus_gw1",
        "bps_gw1",
        "total_points_gw1",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Did the player start GW1?
    df["started_gw1"] = (df["minutes_gw1"] >= 60).astype(int)

    # Played at all
    df["played_gw1"] = (df["minutes_gw1"] > 0).astype(int)

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nGW1 DATA-SJEKK")
    print("-" * 70)

    print(f"Spillere totalt:       {len(df)}")
    print(f"Spillere med minutter: {(df['minutes_gw1'] > 0).sum()}")
    print(f"Spillere med 60+ min:  {(df['minutes_gw1'] >= 60).sum()}")
    print(f"Spillere med 90 min:   {(df['minutes_gw1'] >= 90).sum()}")

    print("\nTOPP 20 — GW1 MINUTTER")
    print("-" * 70)

    cols = [
        "name",
        "position",
        "team",
        "price",
        "minutes_gw1",
        "started_gw1",
        "total_points_gw1",
    ]

    print(
        df.sort_values(
            ["minutes_gw1", "total_points_gw1"],
            ascending=[False, False]
        )[cols]
        .head(20)
        .to_string(index=False)
    )

    print("\nTOPP 20 — GW1 POENG")
    print("-" * 70)

    print(
        df.sort_values(
            "total_points_gw1",
            ascending=False
        )[cols]
        .head(20)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)
    print("GW1 HISTORY FERDIG")
    print("=" * 70)

    print(f"\n✓ Lagret: {OUTPUT_FILE}")
    print(f"✓ {len(df)} spillere behandlet")


if __name__ == "__main__":
    main()