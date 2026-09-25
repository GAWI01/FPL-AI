from backend.settings import parse_cors_origins


def test_parse_cors_origins_uses_safe_local_defaults():
    assert parse_cors_origins(None) == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_parse_cors_origins_accepts_comma_separated_https_origins():
    assert parse_cors_origins("https://fpl.example, https://app.fpl.example") == [
        "https://fpl.example",
        "https://app.fpl.example",
    ]


def test_parse_cors_origins_rejects_wildcard():
    try:
        parse_cors_origins("*")
    except ValueError as exc:
        assert "wildcard" in str(exc).lower()
    else:
        raise AssertionError("wildcard should not be accepted")
