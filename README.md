# Prediction Radar

A prediction market intelligence engine for discovering emerging signals.

Prediction Radar monitors Polymarket and highlights meaningful changes in probability, volume, and attention. It is a signal discovery product, not a betting tool.

## Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL (local Docker or Supabase)
- **Scheduler:** 15-minute sync job
- **Frontend:** Astro static site (Cloudflare Pages in production)
- **Data source:** Polymarket Gamma API + CLOB price history

## Architecture

### Local development

```text
Browser → Astro (dev) → FastAPI → Docker Postgres
```

### Production

```text
Browser → Cloudflare Pages (static HTML)
                ↓ build-time fetch
           Render FastAPI
                ↓
           Supabase PostgreSQL
```

Static pages are snapshots generated at Cloudflare build time. New markets and updated scores appear after the next frontend rebuild.

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

Set `API_BASE_URL=http://localhost:8000` in `frontend/.env`.

Production-style static build:

```bash
cd frontend
API_BASE_URL=http://localhost:8000 npm run build
npm run preview
```

## Production Deployment

### Render (API + scheduler)

Environment variables:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
CORS_ORIGINS=https://radar.mopplo.com,https://YOUR_PROJECT.pages.dev
```

Suggested start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Run the scheduler as a separate Render Background Worker / Cron:

```bash
python -m app.jobs.sync_markets
```

### Cloudflare (frontend)

Keep the monorepo. Root Directory = `frontend`. Config lives in `frontend/wrangler.toml` (static assets from `dist`).

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Build command | `npm install && npm run build` |
| Deploy command | `npx wrangler deploy` |
| Build environment variable | `API_BASE_URL=https://YOUR_RENDER_API` (must be a **build-time** var, not only runtime) |
| Node version | `22` |

Recommended custom domain: `radar.mopplo.com`.

Because pages are static, trigger a Cloudflare rebuild when you want fresher homepage/detail snapshots. The backend can keep syncing every 15 minutes independently.

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
