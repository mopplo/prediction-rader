# Prediction Radar

A prediction market intelligence engine for discovering emerging signals.

Prediction Radar monitors Polymarket and highlights meaningful changes in probability, volume, and attention. It is a signal discovery product, not a betting tool.

## Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Scheduler:** 15-minute sync job
- **Frontend:** Astro (SSR)
- **Data source:** Polymarket Gamma API + CLOB price history

## Quick Start

1. Copy environment variables:

```bash
cp .env.example .env
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
npm run dev
```

Set `API_BASE_URL=http://localhost:8000` when running Astro locally.

## API Endpoints

- `GET /health`
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
    pages/        Home and market detail pages
docker-compose.yml
PRD.md
```

## Success Criteria

Within 30 seconds, a user should be able to answer:

1. What changed today? (Top Movers)
2. What is emerging? (Emerging Signals + attention score)
3. What should I read? (Daily Radar briefing)
4. What story is forming? (Narrative Trends)
5. Why it moved? (Detail page Why It Moved panel)

The homepage surfaces differentiated sections with cross-section deduplication.
