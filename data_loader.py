from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
CURRENT_DATA_DIR = PROJECT_ROOT / "historical_data" / "current_data"


class DataLoaderError(RuntimeError):
    """Raised when current FPL data is missing or structurally invalid."""


PLAYER_REQUIRED_COLUMNS = {
    "player_id",
    "name",
    "position",
    "team",
    "price",
    "status",
}

RAW_PLAYER_REQUIRED_COLUMNS = {
    "id",
    "web_name",
    "team",
    "element_type",
    "now_cost",
    "expected_goals",
    "expected_assists",
    "defensive_contribution",
}

TEAM_REQUIRED_COLUMNS = {
    "id",
    "name",
    "short_name",
}

FIXTURE_REQUIRED_COLUMNS = {
    "id",
    "event",
    "team_h",
    "team_a",
}

GAMEWEEK_REQUIRED_COLUMNS = {
    "id",
    "name",
    "deadline_time",
    "is_current",
    "is_next",
}


def _read_csv(filename: str) -> pd.DataFrame:
    path = CURRENT_DATA_DIR / filename

    if not path.exists():
        raise DataLoaderError(f"Missing current-data file: {path}")

    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise DataLoaderError(
            f"Could not read current-data file: {path}"
        ) from exc


def _require_columns(
    dataframe: pd.DataFrame,
    required: set[str],
    filename: str,
) -> None:
    missing = sorted(required - set(dataframe.columns))

    if missing:
        raise DataLoaderError(
            f"{filename} is missing required columns: "
            f"{', '.join(missing)}"
        )


def load_players() -> pd.DataFrame:
    """Load the canonical current player table."""
    df = _read_csv("players_current.csv")

    _require_columns(
        df,
        PLAYER_REQUIRED_COLUMNS,
        "players_current.csv",
    )

    if df["player_id"].isna().any():
        raise DataLoaderError(
            "players_current.csv contains missing player IDs."
        )

    if df["player_id"].duplicated().any():
        raise DataLoaderError(
            "players_current.csv contains duplicate player IDs."
        )

    return df


def load_players_raw() -> pd.DataFrame:
    """Load the richer raw FPL player snapshot."""
    df = _read_csv("players_raw.csv")

    _require_columns(
        df,
        RAW_PLAYER_REQUIRED_COLUMNS,
        "players_raw.csv",
    )

    if df["id"].isna().any():
        raise DataLoaderError(
            "players_raw.csv contains missing player IDs."
        )

    if df["id"].duplicated().any():
        raise DataLoaderError(
            "players_raw.csv contains duplicate player IDs."
        )

    return df


def load_teams() -> pd.DataFrame:
    """Load current FPL teams."""
    df = _read_csv("teams_current.csv")

    _require_columns(
        df,
        TEAM_REQUIRED_COLUMNS,
        "teams_current.csv",
    )

    if df["id"].isna().any():
        raise DataLoaderError(
            "teams_current.csv contains missing team IDs."
        )

    if df["id"].duplicated().any():
        raise DataLoaderError(
            "teams_current.csv contains duplicate team IDs."
        )

    return df


def load_fixtures() -> pd.DataFrame:
    """Load current FPL fixtures."""
    df = _read_csv("fixtures_current.csv")

    _require_columns(
        df,
        FIXTURE_REQUIRED_COLUMNS,
        "fixtures_current.csv",
    )

    if df["id"].isna().any():
        raise DataLoaderError(
            "fixtures_current.csv contains missing fixture IDs."
        )

    if df["id"].duplicated().any():
        raise DataLoaderError(
            "fixtures_current.csv contains duplicate fixture IDs."
        )

    return df


def load_gameweeks() -> pd.DataFrame:
    """Load current FPL gameweeks."""
    df = _read_csv("gameweeks_current.csv")

    _require_columns(
        df,
        GAMEWEEK_REQUIRED_COLUMNS,
        "gameweeks_current.csv",
    )

    if df["id"].isna().any():
        raise DataLoaderError(
            "gameweeks_current.csv contains missing gameweek IDs."
        )

    if df["id"].duplicated().any():
        raise DataLoaderError(
            "gameweeks_current.csv contains duplicate gameweek IDs."
        )

    return df


def validate_current_data() -> None:
    """
    Validate the structural relationships between current-data tables.

    This function is read-only and does not modify source files.
    """
    players = load_players()
    raw_players = load_players_raw()
    teams = load_teams()
    fixtures = load_fixtures()
    gameweeks = load_gameweeks()

    player_ids = set(players["player_id"])
    raw_player_ids = set(raw_players["id"])

    team_ids = set(teams["id"])
    team_names = set(teams["name"])

    gameweek_ids = set(gameweeks["id"])

    # Canonical and raw player tables must describe the same players.
    if player_ids != raw_player_ids:
        raise DataLoaderError(
            "players_current.csv and players_raw.csv "
            "contain different player IDs."
        )

    # players_current.csv stores team names, not team IDs.
    invalid_player_teams = (
        set(players["team"].dropna()) - team_names
    )

    if invalid_player_teams:
        raise DataLoaderError(
            "players_current.csv references unknown team names: "
            f"{sorted(invalid_player_teams)}"
        )

    # Fixtures use numeric FPL team IDs.
    fixture_team_ids = (
        set(fixtures["team_h"].dropna())
        | set(fixtures["team_a"].dropna())
    )

    invalid_fixture_teams = fixture_team_ids - team_ids

    if invalid_fixture_teams:
        raise DataLoaderError(
            "fixtures_current.csv references unknown team IDs: "
            f"{sorted(invalid_fixture_teams)}"
        )

    # Fixtures must reference existing gameweeks.
    fixture_events = set(fixtures["event"].dropna())

    invalid_fixture_events = fixture_events - gameweek_ids

    if invalid_fixture_events:
        raise DataLoaderError(
            "fixtures_current.csv references unknown gameweeks: "
            f"{sorted(invalid_fixture_events)}"
        )


if __name__ == "__main__":
    validate_current_data()
    print("Current FPL data validation: OK")