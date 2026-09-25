from backend.main import app


def test_v1_openapi_declares_runtime_response_schemas():
    schema = app.openapi()
    expected_models = {
        "/api/v1/status": "StatusEnvelopeModel",
        "/api/v1/dashboard/{team_id}": "DashboardEnvelopeModel",
        "/api/v1/plan/{team_id}": "PlanEnvelopeModel",
        "/api/v1/players": "PlayerEnvelopeModel",
        "/api/v1/fixtures": "FixtureEnvelopeModel",
        "/api/v1/fixture-matrix": "FixtureMatrixEnvelopeModel",
        "/api/v1/review/{team_id}": "ReviewEnvelopeModel",
    }

    for path, model_name in expected_models.items():
        response_schema = schema["paths"][path]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert response_schema["$ref"].endswith(f"/{model_name}")
