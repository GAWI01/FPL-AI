import csv
import tempfile
import unittest
from pathlib import Path

from healthcheck import audit_project


class ProjectHealthcheckTests(unittest.TestCase):
    def test_missing_project_reports_failure(self) -> None:
        report = audit_project("missing-project")
        self.assertEqual("fail", report["status"])

    def test_reports_missing_required_current_files_as_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = audit_project(Path(temporary_directory))

        missing_paths = {
            finding["path"]
            for finding in report["findings"]
            if finding["code"] == "missing_required_file"
        }

        self.assertIn(
            "historical_data/current_data/players_current.csv",
            missing_paths,
        )
        self.assertEqual("fail", report["status"])

    def test_reports_misaligned_current_player_ids_as_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            current = root / "historical_data" / "current_data"

            for filename, player_id in (
                ("players_current.csv", 1),
                ("players_features_current_v2.csv", 2),
                ("gw2_predictions_v4.csv", 1),
            ):
                self._write_csv(current / filename, player_id)

            report = audit_project(root)

        mismatch = [
            finding
            for finding in report["findings"]
            if finding["code"] == "current_player_id_mismatch"
        ]

        self.assertEqual(1, len(mismatch))
        self.assertEqual("fail", report["status"])

    def test_records_current_data_row_counts_for_a_consistent_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            current = root / "historical_data" / "current_data"

            for filename in (
                "players_current.csv",
                "players_features_current_v2.csv",
                "gw2_predictions_v4.csv",
            ):
                self._write_csv(current / filename, 1)

            report = audit_project(root)

        self.assertEqual("pass", report["status"])
        self.assertEqual(
            {
                "players_current.csv": 1,
                "players_features_current_v2.csv": 1,
                "gw2_predictions_v4.csv": 1,
            },
            report["metrics"]["current_data_rows"],
        )

    @staticmethod
    def _write_csv(path: Path, player_id: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["player_id"])
            writer.writeheader()
            writer.writerow({"player_id": player_id})
