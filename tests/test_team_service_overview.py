from backend.team_service import normalize_team_response


def test_normalize_team_response_includes_entry_summary_stats():
    payload = {
        "id": 6658075, "name": "laget mitt", "bank": 12, "event": 2,
        "transfers": 1, "summary_overall_rank": 245671,
        "summary_event_points": 58, "summary_event_rank": 12342,
        "summary_total_points": 142, "value": 1001,
    }
    picks_payload = {"picks": [{"element": 109, "position": 1, "multiplier": 1}]}
    result = normalize_team_response(6658075, payload, picks_payload=picks_payload)
    assert result["overall_rank"] == 245671
    assert result["event_points"] == 58
    assert result["event_rank"] == 12342
    assert result["total_points"] == 142
    assert result["value"] == 100.1
