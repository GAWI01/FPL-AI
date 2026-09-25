from pathlib import Path

import pandas as pd
import pytest

from backend import data_loader


def _write_csv(base: Path, filename: str, data: dict) -> None:
    pd.DataFrame(data).to_csv(base / filename, index=False)


def _build_valid_dataset(tmp_path: Path) -> None:
    _write_csv(
        tmp_path,
        "players_current.csv",
        {
            "player_id": [1, 2],
            "name": ["Player One", "Player Two"],
            "position": ["MID", "DEF"],
            "team": ["Arsenal", "Chelsea"],
            "price": [10.0, 5.0],
            "status": ["a", "a"],
        },
    )

    _write_csv(
        tmp_path,
        "players_raw.csv",
        {
            "id": [1, 2],
            "web_name": ["Player One", "Player Two"],
            "team": [1, 2],
            "element_type": [3, 2],
            "now_cost": [100, 50],
            "expected_goals": [1.0, 0.2],
            "expected_assists": [0.5, 0.1],
            "defensive_contribution": [10, 20],
        },
    )

    _write_csv(
        tmp_path,
        "teams_current.csv",
        {
            "id": [1, 2],
            "name": ["Arsenal", "Chelsea"],
            "short_name": ["ARS", "CHE"],
        },
    )

    _write_csv(
        tmp_path,
        "fixtures_current.csv",
        {
            "id": [100],
            "event": [1],
            "team_h": [1],
            "team_a": [2],
        },
    )

    _write_csv(
        tmp_path,
        "gameweeks_current.csv",
        {
            "id": [1],
            "name": ["Gameweek 1"],
            "deadline_time": ["2026-08-01T10:00:00Z"],
            "is_current": [True],
            "is_next": [False],
        },
    )


def test_valid_current_data(tmp_path, monkeypatch):
    _build_valid_dataset(tmp_path)
    monkeypatch.setattr(data_loader, "CURRENT_DATA_DIR", tmp_path)

    data_loader.validate_current_data()


def test_duplicate_player_ids_are_rejected(tmp_path, monkeypatch):
    _build_valid_dataset(tmp_path)

    players = pd.read_csv(tmp_path / "players_current.csv")
    players.loc[1, "player_id"] = players.loc[0, "player_id"]
    players.to_csv(tmp_path / "players_current.csv", index=False)

    monkeypatch.setattr(data_loader, "CURRENT_DATA_DIR", tmp_path)

    with pytest.raises(
        data_loader.DataLoaderError,
        match="duplicate player IDs",
    ):
        data_loader.load_players()


def test_unknown_player_team_is_rejected(tmp_path, monkeypatch):
    _build_valid_dataset(tmp_path)

    players = pd.read_csv(tmp_path / "players_current.csv")
    players.loc[0, "team"] = "Unknown FC"
    players.to_csv(tmp_path / "players_current.csv", index=False)

    monkeypatch.setattr(data_loader, "CURRENT_DATA_DIR", tmp_path)

    with pytest.raises(
        data_loader.DataLoaderError,
        match="unknown team names",
    ):
        data_loader.validate_current_data()


def test_unknown_fixture_team_is_rejected(tmp_path, monkeypatch):
    _build_valid_dataset(tmp_path)

    fixtures = pd.read_csv(tmp_path / "fixtures_current.csv")
    fixtures.loc[0, "team_h"] = 999
    fixtures.to_csv(tmp_path / "fixtures_current.csv", index=False)

    monkeypatch.setattr(data_loader, "CURRENT_DATA_DIR", tmp_path)

    with pytest.raises(
        data_loader.DataLoaderError,
        match="unknown team IDs",
    ):
        data_loader.validate_current_data()


def test_unknown_fixture_gameweek_is_rejected(tmp_path, monkeypatch):
    _build_valid_dataset(tmp_path)

    fixtures = pd.read_csv(tmp_path / "fixtures_current.csv")
    fixtures.loc[0, "event"] = 999
    fixtures.to_csv(tmp_path / "fixtures_current.csv", index=False)

    monkeypatch.setattr(data_loader, "CURRENT_DATA_DIR", tmp_path)

    with pytest.raises(
        data_loader.DataLoaderError,
        match="unknown gameweeks",
    ):
        data_loader.validate_current_data()


def test_missing_required_player_column_is_rejected(tmp_path, monkeypatch):
    _build_valid_dataset(tmp_path)

    players = pd.read_csv(tmp_path / "players_current.csv")
    players = players.drop(columns=["price"])
    players.to_csv(tmp_path / "players_current.csv", index=False)

    monkeypatch.setattr(data_loader, "CURRENT_DATA_DIR", tmp_path)

    with pytest.raises(
        data_loader.DataLoaderError,
        match="missing required columns",
    ):
        data_loader.load_players()