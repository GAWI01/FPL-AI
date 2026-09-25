"""
Build current-season player features for the next Gameweek.

Early-season handling:
- If explicit GW1 history is available, it is treated as 1 completed match,
  not as a 1/5 rolling sample.
- Once broader rolling history is supplied, the canonical xMins engine can
  use the rolling minute/start features normally.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from feature_contract import FEATURE_COLUMNS
from historical_data.current_data.xmins import (
    availability_multiplier,
    availability_label,
    calculate_xmins,
)


BASE = Path(__file__).resolve().parent

PLAYERS_FILE = BASE / "players_current.csv"
GW1_FILE = BASE / "gw1_history.csv"
OUTPUT_FILE = BASE / "players_features_current.csv"


def rotation_risk(xmins: float, minutes_gw1: float) -> str:
    if xmins <= 0:
        return "OUT"
    if minutes_gw1 >= 75 and xmins >= 70:
        return "LOW"
    if minutes_gw1 >= 60 and xmins >= 60:
        return "MEDIUM"
    if minutes_gw1 >= 30:
        return "HIGH"
    return "VERY_HIGH"


def _build_early_season_xmins(row: pd.Series) -> float:
    """
    GW1-only xMins semantics.

    One completed GW means:
      - starter with 60-90 minutes -> strong starter expectation
      - substitute/partial appearance -> reduced expectation
      - no appearance -> 0
    Availability is applied afterwards.
    """
    availability = availability_multiplier(row)

    if availability <= 0:
        return 0.0

    minutes = float(
        np.clip(
            pd.to_numeric(
                row.get("minutes_gw1", 0.0),
                errors="coerce",
            ),
            0.0,
            90.0,
        )
    )

    started = float(
        np.clip(
            pd.to_numeric(
                row.get("started_gw1", 0.0),
                errors="coerce",
            ),
            0.0,
            1.0,
        )
    )

    played = float(
        np.clip(
            pd.to_numeric(
                row.get("played_gw1", 0.0),
                errors="coerce",
            ),
            0.0,
            1.0,
        )
    )

    if started >= 1.0:
        base = max(minutes, 90.0 if minutes >= 75 else minutes)
    elif played >= 1.0 and minutes > 0:
        base = minutes * 0.75
    else:
        base = 0.0

    return round(
        float(np.clip(base * availability, 0.0, 90.0)),
        1,
    )


def main() -> None:
    print("=" * 70)
    print("FPL AI - CURRENT PLAYER FEATURES V2.2")
    print("=" * 70)

    print("\nLoading current player data...")
    players = pd.read_csv(PLAYERS_FILE)
    print(f"Players: {len(players)}")

    print("Loading GW1 history...")
    gw1 = pd.read_csv(GW1_FILE)
    print(f"GW1 rows: {len(gw1)}")

    history_columns = [
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

    history_columns = [
        column for column in history_columns
        if column in gw1.columns
    ]

    gw1_small = (
        gw1[history_columns]
        .drop_duplicates("player_id")
    )

    df = players.merge(
        gw1_small,
        on="player_id",
        how="left",
    )

    numeric_columns = [
        column for column in history_columns
        if column != "player_id"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        ).fillna(0.0)

    # GW1 is the previous completed Gameweek and is safe for next-GW input.
    df["points_last_3"] = df["total_points_gw1"]
    df["points_last_5"] = df["total_points_gw1"]
    df["points_avg_5"] = df["total_points_gw1"]

    df["minutes_last_5"] = df["minutes_gw1"]
    df["starts_last_5"] = df["started_gw1"].clip(
        lower=0,
        upper=1,
    )

    df["goals_last_5"] = df["goals_gw1"]
    df["assists_last_5"] = df["assists_gw1"]

    for feature, source in [
        ("bps_avg_5", "bps_gw1"),
        ("influence_avg_5", "influence_gw1"),
        ("creativity_avg_5", "creativity_gw1"),
        ("threat_avg_5", "threat_gw1"),
        ("ict_index_avg_5", "ict_index_gw1"),
    ]:
        if source in df.columns:
            df[feature] = pd.to_numeric(
                df[source],
                errors="coerce",
            ).fillna(0.0)
        else:
            df[feature] = 0.0

    df["form_5"] = df["points_avg_5"]

    if "xP" in df.columns:
        df["xP"] = pd.to_numeric(
            df["xP"],
            errors="coerce",
        ).fillna(0.0)
    else:
        df["xP"] = 0.0

    # Canonical availability labels and multiplier.
    df["availability"] = df.apply(
        availability_label,
        axis=1,
    )

    df["availability_multiplier"] = df.apply(
        availability_multiplier,
        axis=1,
    )

    # GW1-only data needs one-match semantics. Using minutes_last_5 as
    # though it were five completed matches would divide a single GW1 start
    # by five and produce artificially low xMins.
    has_gw1_history = (
        df["minutes_gw1"].notna()
        | df["started_gw1"].notna()
        | df["played_gw1"].notna()
    )

    df["xmins"] = 0.0

    df.loc[has_gw1_history, "xmins"] = df.loc[
        has_gw1_history
    ].apply(
        _build_early_season_xmins,
        axis=1,
    )

    # For rows without GW1 history, retain the canonical engine's fallback.
    no_gw1_history = ~has_gw1_history

    if no_gw1_history.any():
        df.loc[no_gw1_history, "xmins"] = df.loc[
            no_gw1_history
        ].apply(
            calculate_xmins,
            axis=1,
        )

    df["start_probability"] = np.clip(
        df["xmins"] / 90.0,
        0.0,
        1.0,
    ).round(3)

    df["rotation_risk"] = df.apply(
        lambda row: rotation_risk(
            float(row["xmins"]),
            float(row["minutes_gw1"]),
        ),
        axis=1,
    )

    df["reliable_starter"] = (
        (df["minutes_gw1"] >= 60)
        & (df["xmins"] >= 60)
        & (df["availability_multiplier"] >= 0.75)
    ).astype(int)

    for column in FEATURE_COLUMNS:
        if column not in df.columns:
            if column == "opponent_team":
                continue
            df[column] = 0.0

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n" + "=" * 70)
    print("AVAILABILITY")
    print("=" * 70)
    print(df["availability"].value_counts().to_string())

    print("\n" + "=" * 70)
    print("ROTATION RISK")
    print("=" * 70)
    print(df["rotation_risk"].value_counts().to_string())

    print("\n" + "=" * 70)
    print("XMINS SUMMARY")
    print("=" * 70)
    print(df["xmins"].describe().to_string())

    print("\n" + "=" * 70)
    print("CURRENT PLAYER FEATURES V2.2 COMPLETE")
    print("=" * 70)

    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Players processed: {len(df)}")


if __name__ == "__main__":
    main()
