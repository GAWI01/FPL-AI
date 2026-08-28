"""Read-only integrity checks for the FPL-AI project data and runtime."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


CURRENT_DATA_FILES = (
    "players_current.csv",
    "players_features_current_v2.csv",
    "gw2_predictions_v4.csv",
)


def audit_project(project_root: str | Path) -> dict[str, Any]:
    """Return a machine-readable health report without modifying the project."""
    root = Path(project_root)
    findings: list[dict[str, str]] = []
    metrics: dict[str, Any] = {"current_data_rows": {}}

    if not root.is_dir():
        findings.append(
            {
                "severity": "error",
                "code": "project_directory_missing",
                "path": str(root),
                "message": "Project directory does not exist.",
            }
        )

        return {"status": "fail", "findings": findings, "metrics": metrics}

    current_data = root / "historical_data" / "current_data"
    player_ids_by_file: dict[str, set[str]] = {}

    for filename in CURRENT_DATA_FILES:
        relative_path = f"historical_data/current_data/{filename}"
        path = current_data / filename

        if not path.is_file():
            findings.append(
                {
                    "severity": "error",
                    "code": "missing_required_file",
                    "path": relative_path,
                    "message": "Required current-data file is missing.",
                }
            )
            continue

        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or "player_id" not in reader.fieldnames:
                findings.append(
                    {
                        "severity": "error",
                        "code": "missing_player_id_column",
                        "path": relative_path,
                        "message": "Current-data file must contain a player_id column.",
                    }
                )
                continue

            player_ids = [row["player_id"] for row in reader]

        if len(player_ids) != len(set(player_ids)):
            findings.append(
                {
                    "severity": "error",
                    "code": "duplicate_player_id",
                    "path": relative_path,
                    "message": "Current-data file contains duplicate player IDs.",
                }
            )

        player_ids_by_file[filename] = set(player_ids)
        metrics["current_data_rows"][filename] = len(player_ids)

    if len(player_ids_by_file) == len(CURRENT_DATA_FILES):
        player_id_sets = list(player_ids_by_file.values())
        if any(ids != player_id_sets[0] for ids in player_id_sets[1:]):
            findings.append(
                {
                    "severity": "error",
                    "code": "current_player_id_mismatch",
                    "path": "historical_data/current_data",
                    "message": "Current player, feature and prediction files do not contain the same player IDs.",
                }
            )

    return {
        "status": "fail" if findings else "pass",
        "findings": findings,
        "metrics": metrics,
    }
