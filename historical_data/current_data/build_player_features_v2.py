import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent

PLAYERS_FILE = BASE / "players_current.csv"
GW1_FILE = BASE / "gw1_history.csv"
OUTPUT_FILE = BASE / "players_features_current_v2.csv"


def availability_multiplier(row):
    status = str(row.get("status", "a")).lower()
    chance = row.get("chance_of_playing_next_round", np.nan)

    # FPL status:
    # a = available
    # i = injured
    # s = suspended
    # u = unavailable
    if status in {"i", "s", "u"}:
        return 0.0

    if pd.notna(chance):
        chance = float(chance)
        return max(0.0, min(1.0, chance / 100.0))

    return 1.0


def calculate_xmins(row):
    """
    Estimate expected minutes for GW2.

    GW1 is our strongest early-season signal.
    Availability information is then used to reduce xMins
    when FPL reports an injury/availability concern.
    """

    minutes = float(row.get("minutes_gw1", 0) or 0)
    multiplier = availability_multiplier(row)

    # Played 60+ in GW1:
    # strong indication that the player is a starter.
    if minutes >= 75:
        base_xmins = 82.0

    elif minutes >= 60:
        base_xmins = 75.0

    # Played 30-59:
    # could be rotation, tactical substitution, or late sub.
    elif minutes >= 30:
        base_xmins = 45.0

    # Played 1-29:
    # likely substitute / limited role.
    elif minutes > 0:
        base_xmins = 20.0

    # Did not play GW1.
    else:
        base_xmins = 10.0

    return round(base_xmins * multiplier, 1)


def rotation_risk(xmins, minutes_gw1):
    """
    Classify expected rotation/start risk.
    """

    if xmins <= 0:
        return "OUT"

    if minutes_gw1 >= 75 and xmins >= 70:
        return "LOW"

    if minutes_gw1 >= 60 and xmins >= 60:
        return "MEDIUM"

    if minutes_gw1 >= 30:
        return "HIGH"

    return "VERY_HIGH"


def availability_label(row):
    status = str(row.get("status", "a")).lower()
    chance = row.get("chance_of_playing_next_round", np.nan)
    news = str(row.get("news", "")).strip()

    if status in {"i", "s", "u"}:
        return "UNAVAILABLE"

    if pd.notna(chance):
        chance = float(chance)

        if chance == 0:
            return "UNAVAILABLE"
        elif chance <= 25:
            return "MAJOR_RISK"
        elif chance <= 50:
            return "RISK"
        elif chance <= 75:
            return "MINOR_RISK"

    if news and news.lower() not in {"nan", "none"}:
        return "NEWS"

    return "AVAILABLE"


def main():

    print("=" * 70)
    print("FPL AI — PLAYER FEATURES V2")
    print("=" * 70)

    print("\nLeser current player-data...")
    players = pd.read_csv(PLAYERS_FILE)
    print(f"✓ Spillere: {len(players)}")

    print("\nLeser GW1 history...")
    gw1 = pd.read_csv(GW1_FILE)
    print(f"✓ GW1 records: {len(gw1)}")

    # Only take the GW1-specific columns we need.
    history_cols = [
        "player_id",
        "minutes_gw1",
        "goals_gw1",
        "assists_gw1",
        "clean_sheets_gw1",
        "bonus_gw1",
        "bps_gw1",
        "total_points_gw1",
        "started_gw1",
        "played_gw1",
    ]

    history_cols = [
        c for c in history_cols
        if c in gw1.columns
    ]

    gw1_small = gw1[history_cols].drop_duplicates("player_id")

    # Merge current data with GW1.
    df = players.merge(
        gw1_small,
        on="player_id",
        how="left"
    )

    # Fill missing GW1 data.
    numeric_cols = [
        "minutes_gw1",
        "goals_gw1",
        "assists_gw1",
        "clean_sheets_gw1",
        "bonus_gw1",
        "bps_gw1",
        "total_points_gw1",
        "started_gw1",
        "played_gw1",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    # Calculate availability.
    df["availability"] = df.apply(
        availability_label,
        axis=1
    )

    df["availability_multiplier"] = df.apply(
        availability_multiplier,
        axis=1
    )

    # Calculate xMins.
    df["xmins"] = df.apply(
        calculate_xmins,
        axis=1
    )

    # Start probability.
    df["start_probability"] = np.clip(
        df["xmins"] / 90.0,
        0,
        1
    )

    # Rotation risk.
    df["rotation_risk"] = df.apply(
        lambda r: rotation_risk(
            r["xmins"],
            r["minutes_gw1"]
        ),
        axis=1
    )

    # Useful flag for the optimizer.
    df["reliable_starter"] = (
        (df["minutes_gw1"] >= 60) &
        (df["xmins"] >= 60) &
        (df["availability_multiplier"] >= 0.75)
    ).astype(int)

    # Save.
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nXMINS / AVAILABILITY-SJEKK")
    print("-" * 70)

    print(
        df["availability"]
        .value_counts()
        .to_string()
    )

    print("\nROTASJONSRISIKO")
    print("-" * 70)

    print(
        df["rotation_risk"]
        .value_counts()
        .to_string()
    )

    print("\nTOPP 25 ETTER XMINS")
    print("-" * 70)

    cols = [
        "name",
        "position",
        "team",
        "price",
        "minutes_gw1",
        "total_points_gw1",
        "status",
        "chance_of_playing_next_round",
        "xmins",
        "start_probability",
        "availability",
        "rotation_risk",
    ]

    cols = [
        c for c in cols
        if c in df.columns
    ]

    print(
        df.sort_values(
            ["xmins", "total_points_gw1"],
            ascending=[False, False]
        )[cols]
        .head(25)
        .to_string(index=False)
    )

    print("\nTOPP 20 GW1-STARTERE")
    print("-" * 70)

    print(
        df[
            (df["minutes_gw1"] >= 60) &
            (df["xmins"] > 0)
        ]
        .sort_values(
            "xmins",
            ascending=False
        )[cols]
        .head(20)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)
    print("PLAYER FEATURES V2 FERDIG")
    print("=" * 70)

    print(f"\n✓ Lagret: {OUTPUT_FILE}")
    print(f"✓ {len(df)} spillere behandlet")


if __name__ == "__main__":
    main()