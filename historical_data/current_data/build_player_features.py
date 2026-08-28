import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent

PLAYERS_FILE = BASE / "players_current.csv"
OUTPUT_FILE = BASE / "players_features_current.csv"


def calculate_xmins(row):
    """
    Estimate expected minutes for the next gameweek.

    Uses FPL's current availability information first,
    then recent minutes as a fallback.
    """

    status = str(row.get("status", "a")).lower()
    chance = row.get("chance_of_playing_next_round", np.nan)
    minutes = float(row.get("minutes", 0) or 0)

    # Explicitly unavailable
    if status in {"i", "s", "u"}:
        return 0.0

    # Chance of playing supplied by FPL
    if pd.notna(chance):
        chance = float(chance)

        # FPL gives values such as 100, 75, 50, 25, 0
        if chance <= 0:
            return 0.0

        availability = chance / 100.0
    else:
        availability = 1.0

    # Estimate normal minutes from season minutes.
    # We cap this because 90 is the practical maximum.
    if minutes >= 900:
        base_minutes = 85.0
    elif minutes >= 600:
        base_minutes = 78.0
    elif minutes >= 300:
        base_minutes = 68.0
    elif minutes >= 100:
        base_minutes = 50.0
    else:
        base_minutes = 30.0

    return round(base_minutes * availability, 1)


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
    print("FPL AI — PLAYER AVAILABILITY / XMINS V1")
    print("=" * 70)

    print("\nLeser current player-data...")
    df = pd.read_csv(PLAYERS_FILE)

    print(f"✓ Spillere: {len(df)}")

    # Calculate expected minutes
    df["xmins"] = df.apply(calculate_xmins, axis=1)

    # Availability classification
    df["availability"] = df.apply(availability_label, axis=1)

    # Start probability
    df["start_probability"] = np.clip(df["xmins"] / 90.0, 0, 1)

    # Simple rotation-risk indicator.
    # Players with low expected minutes are more rotation-prone.
    df["rotation_risk"] = np.select(
        [
            df["xmins"] >= 75,
            df["xmins"] >= 60,
            df["xmins"] >= 45,
            df["xmins"] > 0,
        ],
        [
            "LOW",
            "MEDIUM",
            "HIGH",
            "VERY_HIGH",
        ],
        default="OUT",
    )

    # A numerical reliability multiplier.
    # This will later be used by the prediction model.
    df["availability_multiplier"] = np.clip(
        df["xmins"] / 90.0,
        0,
        1
    )

    # Save
    df.to_csv(OUTPUT_FILE, index=False)

    print("\nSTATUS-FORDELING")
    print("-" * 70)
    print(df["availability"].value_counts().to_string())

    print("\nROTASJONSRISIKO")
    print("-" * 70)
    print(df["rotation_risk"].value_counts().to_string())

    print("\nTOPP 20 ETTER XMINS")
    print("-" * 70)

    cols = [
        "name",
        "position",
        "team",
        "price",
        "status",
        "chance_of_playing_next_round",
        "xmins",
        "availability",
        "rotation_risk",
    ]

    available_cols = [c for c in cols if c in df.columns]

    print(
        df.sort_values("xmins", ascending=False)
        [available_cols]
        .head(20)
        .to_string(index=False)
    )

    print("\n" + "=" * 70)
    print("XMINS-DATA FERDIG")
    print("=" * 70)

    print(f"\n✓ Lagret: {OUTPUT_FILE}")
    print(f"✓ {len(df)} spillere behandlet")


if __name__ == "__main__":
    main()