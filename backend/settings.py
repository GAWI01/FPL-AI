from __future__ import annotations


LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def parse_cors_origins(value: str | None) -> list[str]:
    if value is None or not value.strip():
        return LOCAL_CORS_ORIGINS.copy()

    origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("CORS wildcard origins are not allowed")
    if not origins:
        raise ValueError("At least one CORS origin is required")
    return origins
