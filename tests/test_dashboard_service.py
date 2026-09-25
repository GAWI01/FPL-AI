from backend.dashboard_service import DashboardDependencies, build_dashboard


def _base_dependencies(**overrides):
    values = {
        "team": lambda team_id: {
            "team_id": team_id,
            "name": "Test XI",
            "event": 2,
            "picks": [],
        },
        "live": lambda team_id: {
            "current_event": 2,
            "status": "LIVE",
            "picks": [],
        },
        "history": lambda team_id: {"history": []},
        "fixtures": lambda team_id: {"fixtures": []},
        "players": lambda: {"players": []},
        "decision": lambda team_id: {"transfers": {"net_gain": 0}},
    }
    values.update(overrides)
    return DashboardDependencies(**values)


def test_dashboard_preserves_official_data_when_decision_fails():
    def decision_failure(team_id):
        raise RuntimeError("model offline")

    payload = build_dashboard(
        44,
        _base_dependencies(decision=decision_failure),
    )

    assert payload["data"]["team"]["name"] == "Test XI"
    assert payload["data"]["decision"] is None
    assert payload["meta"]["degraded"] is True
    assert payload["errors"] == [
        {"area": "decision", "message": "Decision data is unavailable"}
    ]


def test_dashboard_keeps_each_successful_domain_in_one_envelope():
    payload = build_dashboard(44, _base_dependencies())

    assert payload["data"]["live"]["status"] == "LIVE"
    assert payload["data"]["fixtures"] == {"fixtures": []}
    assert payload["data"]["players"] == {"players": []}
    assert payload["meta"]["event"] == 2
    assert payload["meta"]["degraded"] is False
    assert payload["errors"] == []
