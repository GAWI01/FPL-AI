
from backend import fixture_service


def test_get_team_fixtures_uses_next_gameweek_only(monkeypatch):
    bootstrap = {
        "events": [
            {"id": 2, "is_current": True, "is_next": False, "finished": False},
            {"id": 3, "is_current": False, "is_next": True, "finished": False},
        ],
        "teams": [
            {"id": 1, "name": "Chelsea", "short_name": "CHE"},
            {"id": 2, "name": "Brighton", "short_name": "BHA"},
            {"id": 3, "name": "Arsenal", "short_name": "ARS"},
        ],
        "elements": [
            {"id": 101, "web_name": "Player", "first_name": "Player", "team": 1, "element_type": 3},
        ],
    }

    picks = {"picks": [{"element": 101}]}
    fixtures = [
        {
            "id": 201,
            "event": 2,
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2,
            "team_a_difficulty": 4,
            "kickoff_time": "2026-08-30T10:00:00Z",
            "started": False,
            "finished": False,
        },
        {
            "id": 301,
            "event": 3,
            "team_h": 1,
            "team_a": 3,
            "team_h_difficulty": 4,
            "team_a_difficulty": 3,
            "kickoff_time": "2026-09-05T10:00:00Z",
            "started": False,
            "finished": False,
        },
    ]

    def fake_get_json(path, params=None):
        if path == "bootstrap-static/":
            return bootstrap
        if path == "entry/123/event/2/picks/":
            return picks
        if path == "fixtures/":
            return fixtures
        raise AssertionError(path)

    monkeypatch.setattr(fixture_service, "_get_json", fake_get_json)

    result = fixture_service.get_team_fixtures(123, limit=5)

    assert result["current_event"] == 2
    assert result["next_event"] == 3
    assert [fixture["event"] for fixture in result["fixtures"]] == [3]
    assert result["fixtures"][0]["opponent_short"] == "ARS"
