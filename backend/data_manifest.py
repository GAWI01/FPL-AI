from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class PredictionManifest:
    season: str
    prediction_event: int
    prediction_file: str
    prediction_path: Path
    generated_at: datetime
    player_count: int
    schema_version: int


def season_for_date(moment: datetime) -> str:
    start_year = moment.year if moment.month >= 7 else moment.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def publish_prediction_manifest(
    prediction_path: Path,
    *,
    season: str,
    prediction_event: int,
    player_count: int,
) -> Path:
    artifact = prediction_path.resolve()
    if not artifact.is_file():
        raise ValueError(f"prediction file does not exist: {artifact.name}")

    payload = {
        "season": season,
        "prediction_event": prediction_event,
        "prediction_file": artifact.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "player_count": player_count,
        "schema_version": 1,
    }
    sidecar_path = artifact.with_suffix(artifact.suffix + ".manifest.json")
    if sidecar_path.exists():
        try:
            existing_sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read immutable artifact manifest: {exc}") from exc
        if existing_sidecar != payload:
            raise ValueError(f"Artifact manifest is immutable: {sidecar_path.name}")
    else:
        sidecar_temporary = artifact.parent / f".{sidecar_path.name}.tmp"
        sidecar_temporary.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        sidecar_temporary.replace(sidecar_path)
    manifest_path = artifact.parent / "manifest.json"
    temporary_path = artifact.parent / ".manifest.json.tmp"
    temporary_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(manifest_path)
    load_current_manifest(manifest_path)
    return manifest_path


def load_current_manifest(path: Path) -> PredictionManifest:
    manifest_path = path.resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read prediction manifest: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("prediction manifest must be a JSON object")

    try:
        season = str(payload["season"]).strip()
        prediction_event = int(payload["prediction_event"])
        prediction_file = str(payload["prediction_file"]).strip()
        generated_at = datetime.fromisoformat(str(payload["generated_at"]))
        player_count = int(payload["player_count"])
        schema_version = int(payload["schema_version"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"prediction manifest has invalid fields: {exc}") from exc

    if not season:
        raise ValueError("season cannot be empty")
    if prediction_event <= 0:
        raise ValueError("prediction_event must be positive")
    if not prediction_file:
        raise ValueError("prediction_file cannot be empty")
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    if player_count <= 0:
        raise ValueError("player_count must be positive")
    if schema_version != 1:
        raise ValueError("schema_version must be 1")

    artifact = (manifest_path.parent / prediction_file).resolve()
    try:
        artifact.relative_to(manifest_path.parent)
    except ValueError as exc:
        raise ValueError("prediction file must stay inside manifest directory") from exc

    if not artifact.is_file():
        raise ValueError(f"prediction file does not exist: {prediction_file}")

    return PredictionManifest(
        season=season,
        prediction_event=prediction_event,
        prediction_file=prediction_file,
        prediction_path=artifact,
        generated_at=generated_at,
        player_count=player_count,
        schema_version=schema_version,
    )
