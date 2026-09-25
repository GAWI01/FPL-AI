# Premium dashboard foundation

FPL AI is a public-Team-ID decision product. It reads public Fantasy Premier League data, combines it with versioned local predictions, and never performs actions on the official FPL account.

## Product surfaces

- **Overview:** live/official/model/derived KPIs, current XI, fixtures and a single primary decision.
- **My Team:** all 15 players on an interactive pitch, live/projected toggle, current-versus-model XI and formation-safe local swaps.
- **Plan:** transfer or HOLD, hit-aware net gain, captain/vice-captain, chip state, five-GW what-if paths and meaningful local plan-change history.
- **Explore:** public live player market, actual GW points, model projections, four-player comparison, shareable URL state and all-team fixture matrix.
- **Team History:** evidence-based projected-versus-actual review after a finished Gameweek.
- **Settings:** locally stored Team ID, runtime provenance, privacy boundary and commercial-release disclaimer.

Overview and Plan suppress actionable transfer advice when the current Gameweek is `LIVE` or `FINISHED`. In those states the application shifts to live monitoring.

## Data contract

The frontend uses `/api/v1/dashboard/{team_id}` as its resilient aggregate. A required team failure stops the request; optional live, history, fixtures, players or decision failures return a degraded response with area-specific errors.

Every surface labels its data class:

- `Live`: current event/player output.
- `Official`: official FPL manager, squad and fixture state.
- `Model`: versioned prediction or optimizer output.
- `Derived`: calculations made from the above.

The prediction manifest is `historical_data/current_data/manifest.json`. Publishers replace it atomically only after the full prediction artifact exists.

## Local development

Backend, from the repository root:

```powershell
python -m pip install -r requirements.txt -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
Copy-Item ..\.env.example .env.local
pnpm install
pnpm dev
```

Open `http://localhost:3000` and enter the numeric Team ID visible in the official FPL URL. Without `NEXT_PUBLIC_API_URL`, the frontend deliberately uses a deployment-safe same-origin API path; the local `.env.local` points it to `http://127.0.0.1:8000`.

## Production configuration

Set `NEXT_PUBLIC_API_URL` to the HTTPS API origin during the frontend build. Set `FPL_AI_CORS_ORIGINS` to a comma-separated list of exact HTTPS frontend origins. Wildcard CORS is rejected.

Recommended process commands:

```text
API:      python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
Frontend: pnpm build && pnpm start
```

Use `/health` for liveness and `/api/v1/status` for official/model readiness. Application instances are stateless apart from their in-process upstream cache; add a shared cache only when multiple replicas make it necessary.

## Verification

```powershell
python -m pytest tests backend/tests -q
cd frontend
pnpm test
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

No deployment should be described as ready until these commands and a real public Team-ID smoke test have passed in that environment.
