import json

import pytest

from datetime import datetime, timezone

from backend.data_manifest import (
    load_current_manifest,
    publish_prediction_manifest,
    season_for_date,
)


def _manifest(prediction_file="gw3_predictions_v11.csv"):
    return {
        "season": "2026-27",
        "prediction_event": 3,
        "prediction_file": prediction_file,
        "generated_at": "2026-08-31T18:00:00+00:00",
        "player_count": 623,
        "schema_version": 1,
    }


def test_manifest_requires_existing_prediction_file(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest()), encoding="utf-8")

    with pytest.raises(ValueError, match="prediction file does not exist"):
        load_current_manifest(path)


def test_manifest_resolves_valid_artifact_inside_its_directory(tmp_path):
    artifact = tmp_path / "gw3_predictions_v11.csv"
    artifact.write_text("player_id,predicted_points\n1,5.2\n", encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest()), encoding="utf-8")

    manifest = load_current_manifest(path)

    assert manifest.season == "2026-27"
    assert manifest.prediction_event == 3
    assert manifest.prediction_path == artifact.resolve()


def test_manifest_rejects_artifacts_outside_manifest_directory(tmp_path):
    outside = tmp_path.parent / "outside.csv"
    outside.write_text("player_id,predicted_points\n", encoding="utf-8")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest("../outside.csv")), encoding="utf-8")

    with pytest.raises(ValueError, match="must stay inside"):
        load_current_manifest(path)


def test_publish_prediction_manifest_writes_loadable_metadata(tmp_path):
    artifact = tmp_path / "gw3_predictions_v11.csv"
    artifact.write_text("player_id,predicted_points\n1,5.2\n", encoding="utf-8")

    manifest_path = publish_prediction_manifest(
        artifact,
        season="2026-27",
        prediction_event=3,
        player_count=1,
    )

    manifest = load_current_manifest(manifest_path)
    assert manifest.prediction_file == artifact.name
    assert manifest.player_count == 1
    assert manifest.generated_at.tzinfo is not None
    sidecar = artifact.with_suffix(artifact.suffix + ".manifest.json")
    assert sidecar.is_file()
    assert json.loads(sidecar.read_text(encoding="utf-8"))["prediction_file"] == artifact.name


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 8, 31, tzinfo=timezone.utc), "2026-27"),
        (datetime(2027, 2, 1, tzinfo=timezone.utc), "2026-27"),
    ],
)
def test_season_for_date_spans_summer_rollover(moment, expected):
    assert season_for_date(moment) == expected
