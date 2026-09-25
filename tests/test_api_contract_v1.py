from datetime import datetime, timezone

import pytest

from backend.api_contract import api_envelope, source_meta


def test_source_meta_serializes_utc_and_source_class():
    meta = source_meta(
        "official",
        datetime(2026, 8, 31, 18, tzinfo=timezone.utc),
    )

    assert meta == {
        "source": "official",
        "fetched_at": "2026-08-31T18:00:00+00:00",
        "stale": False,
        "version": None,
    }


def test_source_meta_rejects_unsupported_sources():
    with pytest.raises(ValueError, match="Unsupported source class"):
        source_meta(
            "guess",
            datetime(2026, 8, 31, 18, tzinfo=timezone.utc),
        )


def test_api_envelope_keeps_partial_errors():
    payload = api_envelope(
        {"team": {"team_id": 7}},
        {"event": 2},
        [{"area": "prediction", "message": "Prediction unavailable"}],
    )

    assert payload["data"]["team"]["team_id"] == 7
    assert payload["meta"]["event"] == 2
    assert payload["errors"][0]["area"] == "prediction"
