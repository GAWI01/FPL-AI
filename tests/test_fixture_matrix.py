import pytest

import backend.fixture_service as fixture_service


def _bootstrap():
    return {
        "events": [
            {"id": 2, "is_current": True, "finished": False},
            {"id": 3, "is_next": True, "finished": False},
            {"id": 4, "finished": False},
            {"id": 5, "finished": False},
        ],
        "teams": [
            {"id": 1, "name": "Arsenal", "short_name": "ARS"},
            {"id": 2, "name": "Chelsea", "short_name": "CHE"},
            {"id": 3, "name": "Liverpool", "short_name": "LIV"},
        ],
    }


def _fixtures():
    return [
        {
            "id": 301,
            "event": 3,
            "team_h": 1,
            "team_a": 2,
            "team_h_difficulty": 2,
            "team_a_difficulty": 4,
        },
        {
            "id": 302,
            "event": 3,
            "team_h": 3,
            "team_a": 1,
            "team_h_difficulty": 3,
            "team_a_difficulty": 5,
        },
        {
            "id": 401,
            "event": 4,
            "team_h": 2,
            "team_a": 3,
            "team_h_difficulty": 2,
            "team_a_difficulty": 4,
        },
    ]


def test_build_fixture_matrix_covers_double_and_blank_gameweeks():
    result = fixture_service.build_fixture_matrix(
        _bootstrap(),
        _fixtures(),
        start_event=3,
        horizon=3,
    )

    assert result["gameweeks"] == [3, 4, 5]
    arsenal = next(team for team in result["teams"] if team["team_short"] == "ARS")
    assert arsenal["fixtures"][0] == {
        "event": 3,
        "opponents": ["CHE (H)", "LIV (A)"],
        "difficulty": 3.5,
        "fixture_count": 2,
    }
    assert arsenal["fixtures"][1] == {
        "event": 4,
        "opponents": [],
        "difficulty": None,
        "fixture_count": 0,
    }
    chelsea = next(team for team in result["teams"] if team["team_short"] == "CHE")
    assert chelsea["fixtures"][0]["opponents"] == ["ARS (A)"]
    assert chelsea["fixtures"][0]["difficulty"] == 4.0


def test_get_fixture_matrix_defaults_to_next_gameweek_and_official_paths(monkeypatch):
    requested = []

    def fake_get_json(path, params=None):
        requested.append(path)
        return {"bootstrap-static/": _bootstrap(), "fixtures/": _fixtures()}[path]

    monkeypatch.setattr(fixture_service, "_get_json", fake_get_json)

    result = fixture_service.get_fixture_matrix(horizon=2)

    assert result["start_event"] == 3
    assert result["gameweeks"] == [3, 4]
    assert requested == ["bootstrap-static/", "fixtures/"]


@pytest.mark.parametrize("horizon", [0, 9])
def test_fixture_matrix_rejects_horizon_outside_one_to_eight(horizon):
    with pytest.raises(ValueError, match="between 1 and 8"):
        fixture_service.build_fixture_matrix(
            _bootstrap(), _fixtures(), start_event=3, horizon=horizon
        )


def test_fixture_matrix_rejects_start_beyond_the_season():
    with pytest.raises(ValueError, match="start_event"):
        fixture_service.build_fixture_matrix(
            _bootstrap(), _fixtures(), start_event=39, horizon=3
        )
