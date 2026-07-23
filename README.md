# Prediction Radar

A prediction market intelligence engine for discovering emerging signals.

Prediction Radar monitors Polymarket and highlights meaningful changes in probability, volume, and attention. It is a signal discovery product, not a betting tool.

## Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL (local Docker or Supabase)
- **Scheduler:** GitHub Actions every 2 hours (`sync.yml`)
- **Frontend:** Astro SSR on Cloudflare Workers
- **Data source:** Polymarket Gamma API + CLOB price history

## Architecture

### Local development

```text
Browser → Astro (dev) → FastAPI → Docker Postgres
```

### Production

```text
Browser → Cloudflare Worker (Astro SSR)
                ↓ per-request fetch
           Render FastAPI
                ↓
           Supabase PostgreSQL
                ↑
           GitHub Actions sync (every 2 hours)
```

Pages render on each request. After the backend syncs, refreshing the site shows new data without redeploying the frontend.

## Quick Start

1. Copy environment variables:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

2. Start the full stack:

```bash
./scripts/dev.sh
```

Or manually:

```bash
docker compose up --build
```

3. Open the app:

- Frontend: [http://localhost:4321](http://localhost:4321)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

The bootstrap service runs database migrations and performs the first Polymarket sync before the API starts.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Run a one-time sync:

```bash
python -m app.jobs.sync_markets --once
```

Run tests:

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Set `API_BASE_URL=http://localhost:8000` in `frontend/.env` for `astro dev`.

SSR preview with Wrangler (production-like Worker):

```bash
cd frontend
cp .dev.vars.example .dev.vars
npm run preview
```

## Production Deployment

### Render (API)

Environment variables:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
CORS_ORIGINS=https://radar.mopplo.com,https://prediction-rader.<account>.workers.dev
```

Suggested start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

SSR page rendering fetches the API from the Cloudflare Worker, so browser CORS is not required for HTML. Keep `CORS_ORIGINS` set if you later add browser-side API calls.

### GitHub Actions (market sync)

Use a scheduled workflow instead of a paid Render Cron / Background Worker.

1. In the GitHub repo: **Settings → Secrets and variables → Actions**
2. Add a repository secret:
   - `DATABASE_URL` — same Supabase/Postgres URL used by Render (`postgresql+psycopg://...`)
3. Workflow: [`.github/workflows/sync.yml`](.github/workflows/sync.yml)
   - Schedule: every 2 hours (UTC); job timeout 90 minutes
   - Manual run: **Actions → Sync Polymarket markets → Run workflow**
   - Command: `python -m app.jobs.sync_markets --once`
4. Optional: add more `env` keys in the workflow if you need non-default sync limits.

Ensure the database allows connections from GitHub Actions (public Supabase connection usually works). After sync succeeds, refresh the frontend — no Cloudflare redeploy is required for data freshness.

Each sync also prunes `market_snapshots` older than `SNAPSHOT_RETENTION_DAYS` (default **7**), so Free Supabase storage does not grow unbounded. Detail charts already only read the last 7 days of history.

### Cloudflare Workers (frontend SSR)

Keep the monorepo. Config lives in [`frontend/wrangler.toml`](frontend/wrangler.toml).

#### Cloudflare Dashboard / Git deploy

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Build command | `npm ci && npm run build` |
| Deploy command | `npx wrangler deploy` |
| Node version | `22` |
| Runtime variable | `API_BASE_URL=https://YOUR_RENDER_API` (**Variables and Secrets**, plaintext) |

Steps:

1. Keep Worker project name `prediction-rader` (matches `wrangler.toml`).
2. Set Root Directory to `frontend`.
3. Build: `npm ci && npm run build`.
4. Deploy: `npx wrangler deploy`.
5. In **Settings → Variables and Secrets**, add runtime plaintext `API_BASE_URL` pointing at your Render API (for example `https://prediction-rader.onrender.com`). This is a **runtime** Worker var, not a build-only var.
6. Bind custom domain `radar.mopplo.com`.
7. After deploy, open the site and confirm homepage HTML includes live radar data. Sync the backend, refresh again, and confirm stats/markets update without redeploying Cloudflare.

#### Local CLI deploy

```bash
cd frontend
npm ci
npm run build
npx wrangler deploy
```

Set the production API URL once:

```bash
npx wrangler secret put API_BASE_URL
# or configure plaintext [vars] in the Cloudflare dashboard
```

Recommended custom domain: `radar.mopplo.com`.

## API Endpoints

- `GET /health`
- `GET /api/stats`
- `GET /api/markets`
- `GET /api/top-movers`
- `GET /api/emerging-signals`
- `GET /api/daily-radar`
- `GET /api/narrative-trends`
- `GET /api/market/{id}`

## Signal Logic (V1.1)

### Quality gates
- Probability between **5% and 95%**
- 24h volume ≥ **$10k**, liquidity ≥ **$5k**
- Market ends at least **7 days** out
- Valid 24h CLOB history required for eligibility
- Short-cycle sports/weather/intraday markets excluded

### Two scores
- **Signal score** (Daily Radar + detail): 45% probability + 25% volume + 15% liquidity + 15% persistence
- **Attention score** (Emerging only): 50% volume spike + 30% probability + 20% liquidity

### Sections
- **Top Movers:** largest |24h change|, then signal score, confidence, significance
- **Emerging Signals:** attention score with volume spike + minimum probability move
- **Daily Radar:** composite signal score with per-event/category diversity
- **Narrative Trends:** topic clusters (event → group → title family) with median move and direction coherence

### Why It Moved
Rule-based bullet explanations on every synced market detail page: probability change, volume baseline, liquidity, data confidence, and related narrative activity.

### Market significance
Proxy score from liquidity, volume, event linkage, and time to resolution — not an objective real-world importance measure.

## Project Structure

```text
backend/
  app/
    api/          FastAPI routes
    jobs/         Scheduler entrypoint
    models/       SQLAlchemy models
    services/     Polymarket client, sync, signal logic
frontend/
  src/
    components/   UI building blocks
    lib/          API client and formatters
    pages/        Home and market detail pages
docker-compose.yml
```

## Success Criteria

Within 30 seconds, a user should be able to answer:

1. What changed today? (Top Movers)
2. What is emerging? (Emerging Signals + attention score)
3. What should I read? (Daily Radar briefing)
4. What story is forming? (Narrative Trends)
5. Why it moved? (Detail page Why It Moved panel)

The homepage surfaces differentiated sections with cross-section deduplication.
