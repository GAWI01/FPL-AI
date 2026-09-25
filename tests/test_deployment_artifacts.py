from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backend_container_runs_as_non_root_with_healthcheck():
    content = (ROOT / "Dockerfile.backend").read_text(encoding="utf-8")

    assert "USER app" in content
    assert "HEALTHCHECK" in content
    assert "uvicorn" in content
    assert "backend.main:app" in content


def test_frontend_container_builds_and_runs_the_next_application():
    content = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    assert "pnpm build" in content
    assert 'CMD ["node", "server.js"]' in content
    assert "USER nextjs" in content
    assert "NEXT_PUBLIC_API_URL" in content
    assert "/app/.next/standalone" in content
    dockerignore = (ROOT / "frontend" / ".dockerignore").read_text(encoding="utf-8")
    assert "node_modules" in dockerignore
    assert ".next" in dockerignore
    assert ".env.*" in dockerignore


def test_frontend_production_sources_do_not_fall_back_to_localhost():
    sources = [
        ROOT / "frontend" / "lib" / "api.ts",
        ROOT / "frontend" / "app" / "[module]" / "page.tsx",
        ROOT / "frontend" / "app" / "page_backup.tsx",
    ]

    for source in sources:
        content = source.read_text(encoding="utf-8")
        assert "http://127.0.0.1:8000" not in content
        assert "http://localhost:8000" not in content


def test_local_production_stack_and_render_blueprint_are_declared():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    deployment = (ROOT / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8")

    assert "backend:" in compose and "frontend:" in compose
    assert "Dockerfile.backend" in compose
    assert "healthcheck:" in compose
    assert "fpl-ai-api" in blueprint and "fpl-ai-web" in blueprint
    assert "Hosted smoke test" in deployment
