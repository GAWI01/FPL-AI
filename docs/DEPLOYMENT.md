# FPL AI deployment runbook

## Local production stack

Set `NEXT_PUBLIC_API_URL` to the browser-reachable backend URL when it differs from `http://localhost:8000`, then run:

```powershell
docker compose up --build
```

The web app is exposed on port 3000 and the API on port 8000. Both containers run as non-root users and declare health checks.

## Managed deployment

`render.yaml` declares separate `fpl-ai-api` and `fpl-ai-web` services. Before creating the blueprint:

1. Set backend `FPL_AI_CORS_ORIGINS` to the final HTTPS frontend origin.
2. Set frontend build variable `NEXT_PUBLIC_API_URL` to the final HTTPS API origin.
3. Deploy the API first so its public origin is known, then build the frontend.

The frontend public API URL is compiled into the browser bundle. Changing it requires a frontend rebuild.

If `NEXT_PUBLIC_API_URL` is omitted, the browser uses same-origin `/api` paths. This is safe for a reverse-proxy deployment, but a split frontend/API deployment must set the explicit HTTPS API origin at build time.

Deployment artifacts are for private staging until the [data-use release gate](DATA_USE_RELEASE_GATE.md) is cleared. Do not treat a technically successful deploy as approval for public or commercial use.

## Hosted smoke test

After deployment, verify:

```powershell
Invoke-RestMethod https://YOUR-API/health
Invoke-RestMethod https://YOUR-API/api/v1/status
Invoke-RestMethod https://YOUR-API/api/v1/dashboard/YOUR_PUBLIC_TEAM_ID
Invoke-RestMethod https://YOUR-API/api/v1/fixture-matrix?horizon=5
Invoke-WebRequest https://YOUR-WEB/
```

Confirm that API responses contain `X-Request-ID`, `/api/v1/status` reports official and model sources, and the browser uses HTTPS without CORS errors. A hosted smoke remains an external release gate until real service URLs are provisioned.
