from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import backend.main as main


app = main.app


def test_status_v1_reports_official_and_model_freshness(monkeypatch):
    gateway_result = SimpleNamespace(
        data={
            "events": [
                {"id": 2, "is_current": True, "is_next": False},
                {"id": 3, "is_current": False, "is_next": True},
            ],
            "elements": [{"id": 1}, {"id": 2}],
            "teams": [{"id": index} for index in range(1, 21)],
        },
        fetched_at=datetime(2026, 8, 31, 18, tzinfo=timezone.utc),
        stale=False,
    )
    monkeypatch.setattr(
        main,
        "default_gateway",
        SimpleNamespace(get_json=lambda path, ttl_seconds: gateway_result),
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "load_current_manifest",
        lambda path: SimpleNamespace(
            season="2026-27",
            prediction_event=3,
            prediction_file="gw3_predictions_v11.csv",
            prediction_path=Path("gw3_predictions_v11.csv"),
            generated_at=datetime(2026, 8, 31, 17, tzinfo=timezone.utc),
            player_count=623,
            schema_version=1,
        ),
        raising=False,
    )

    response = TestClient(app).get("/api/v1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["official"]["current_event"] == 2
    assert body["data"]["official"]["next_event"] == 3
    assert body["data"]["official"]["player_count"] == 2
    assert body["data"]["model"]["prediction_event"] == 3
    assert body["data"]["service_state"] == "ready"
    assert body["meta"]["official"]["source"] == "official"
    assert body["meta"]["model"]["source"] == "model"
