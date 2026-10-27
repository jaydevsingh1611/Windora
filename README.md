# Wind Position Monitor

A web app for a UK utility's **day-ahead power procurement team**. It shows the national wind generation forecast that was *actually available* when day-ahead purchases had to be made. It compares that forecast with outturn and puts a number on the error, so the team can size how much extra power to buy.

**Live app:** _<add Vercel URL here after deploy>_

Scope: national wind only, using Elexon BMRS data, for **purchase decisions made in January 2026**. Those decisions cover **delivery days 2 Jan – 1 Feb 2026**.

---

## What it does

| Question the trader asks | Where it is answered |
|---|---|
| What did the forecast say when I had to buy? | Main chart: actual (30 min) vs the *decision-time* forecast (hourly), with a P10–P90 band |
| How wrong is that forecast, typically and at worst? | KPI tiles: MAE, RMSE, bias, P90 shortfall cover, lead time |
| How much extra should I buy to be safe? | **P90 shortfall cover**: the MW buffer that covered the wind shortfall in 90% of hours |
| Would a later gate or forecast help? | *Error by lead time* chart (every forecast run, 0–48 h) |
| Which hours and days are risky? | *Error by hour of day* chart and the *Day by day* table |

### Key definitions
- **Decision-time forecast (gate mode, default).** For every hour of delivery day *D*, the app uses the latest WINDFOR run published at or before the gate time (default **09:20 UK**) on *D-1*. This is when GB day-ahead auctions close. The gate is adjustable in the UI. The calculation is DST-aware (`Europe/London`).
- **Fixed lead time mode.** For each target hour, the app uses the latest run published at least *H* hours earlier (0–48 h slider).
- **Error = forecast − actual.** A positive error means wind came in *below* forecast, so the shortfall had to be bought.
- WINDFOR targets are hourly. Each one is scored against the FUELHH actual for the matching half-hour (`startTime`).

### Headline findings (January 2026, 09:20 gate)
- MAE is **2.02 GW**, which is **18 %** of mean wind output. RMSE is 2.50 GW.
- The forecast has a **systematic over-forecast bias of +1.75 GW**: actual wind came in below forecast in **85 % of hours**. A likely factor is that FUELHH records metered output *after* wind is curtailed for grid constraints. A team trusting the raw forecast would have been short most of the time.
- To cover the shortfall in 90 % of hours, the team would have needed **≈4.15 GW** above the forecast.
- Error grows steadily with lead time, from 1.66 GW at 0–4 h to 2.34 GW at 44–48 h. A later gate improves accuracy but does not remove the bias.

---

## Repository layout

```
.
├── backend/                     Python 3.12 · FastAPI
│   ├── app/
│   │   ├── config.py            Pilot scope (delivery dates), default gate, snapshot path
│   │   ├── elexon.py            HTTP client for the Elexon FUELHH / WINDFOR stream endpoints
│   │   ├── repository.py        Loads the bundled snapshot (falls back to live Elexon) → in-memory Dataset
│   │   ├── forecast.py          Pure logic: ForecastIndex + "latest run before cutoff" selection (gate / horizon)
│   │   ├── metrics.py           Pure logic: MAE, RMSE, bias, percentiles, by-hour/horizon/day, histogram
│   │   ├── service.py           Combines data + selection + metrics into API responses
│   │   ├── models.py            Validated query parameters (Pydantic)
│   │   └── main.py              FastAPI routes under /api
│   ├── data/snapshot_jan2026.json   Cached Elexon pull (1.1 MB), so the demo is fast and independent of Elexon uptime
│   ├── scripts/refresh_snapshot.py  Re-downloads the snapshot from Elexon
│   ├── tests/                   pytest: forecast selection, metrics, API
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    React 19 · TypeScript · Vite · Recharts
│   ├── src/
│   │   ├── App.tsx              Page layout, query state, data loading
│   │   ├── api.ts               Typed API client and response types
│   │   ├── format.ts            GW / date formatting (UK time)
│   │   └── components/          Controls, Insight, KpiTiles, ForecastChart, ErrorCharts, DailyTable
│   ├── nginx.conf               Serves the SPA and proxies /api → backend (Docker)
│   └── Dockerfile               Multi-stage: node build → nginx
├── api/index.py                 Vercel serverless entry point (wraps the FastAPI app)
├── vercel.json                  Vercel build + /api rewrite config
├── requirements.txt             Python deps for the Vercel function
├── docker-compose.yml           backend :8000 + frontend :8080
├── docs/ARCHITECTURE.md         Plain-English guide: architecture, components, how to run
├── docs/DEPLOYMENT.md           Step-by-step Vercel deployment, checks and troubleshooting
├── docs/ASSIGNMENT_STATUS.md    What the assignment asked, what is done, what is left
└── docs/VIDEO_SCRIPT.md         Script for the demo video (client pitch + tech review)
```

### API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Liveness |
| `GET /api/meta` | Pilot date range, defaults, number of forecast runs, data source |
| `GET /api/series` | Half-hourly actuals + selected hourly forecasts (with publish time and lead time) |
| `GET /api/analysis` | Summary metrics, by-hour, by-day, error histogram |
| `GET /api/horizon-accuracy` | Error of **all** runs bucketed by lead time |

Common query params: `start`, `end` (delivery days, `YYYY-MM-DD`), `mode=gate|horizon`, `gate=HH:MM`, `horizon` (hours). Interactive docs are at `/docs` when running the backend locally.

---

## Running it

### Option 1: Docker (recommended)
```bash
docker compose up --build
# app: http://localhost:8080   api: http://localhost:8000/docs
```

### Option 2: Local dev
```bash
# backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cd backend && uvicorn app.main:app --reload --port 8000

# frontend (new terminal) - Vite proxies /api to :8000
cd frontend && npm install && npm run dev
# http://localhost:5173
```

### Tests
```bash
cd backend && pytest        # 18 tests
cd frontend && npm run build  # type-check + production build
```

### Refreshing the data
```bash
cd backend && python -m scripts.refresh_snapshot
```
If the snapshot file is deleted, the API downloads the same window live from Elexon on first request.

### Deploying to Vercel
The repo root is a Vercel project. The React app is built to static files (`frontend/dist`), and `api/index.py` runs the FastAPI app as a Python serverless function. `/api/*` is rewritten to it.
```bash
npx vercel login
npx vercel --prod
```
Or import the GitHub repo on vercel.com. No settings or env vars are needed, because `vercel.json` covers them.
See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for the full step-by-step guide.

---

## Design notes
- **Pure core, thin edges.** All selection and statistics logic lives in `forecast.py` and `metrics.py`. They are pure functions with no I/O, which makes them easy to unit test. `service.py` composes them, and `main.py` is only routing.
- **Fast selection.** Forecast runs are indexed per target time and sorted by publish time. "Latest run before the cutoff" is then a binary search (`bisect`).
- **Snapshot-first data.** The pilot window is historical and fixed, so it is bundled (about 22k rows). This keeps serverless cold starts fast and the demo deterministic. A live-fetch fallback and a refresh script cover the rest.
- **No heavy dependencies.** The backend needs only FastAPI and httpx (no pandas or numpy), which keeps the serverless bundle small.
- **Charts.** They use a colour-blind-validated palette (blue = actual, orange = forecast; red/blue diverging for shortfall/surplus), support light and dark mode, show hover tooltips on every chart, and work on mobile.

### Possible next steps
- Add solar (and other renewables) and net demand, to show the full residual position.
- Add a bias-corrected forecast and probabilistic (quantile) buy recommendations per hour.
- Add a scheduled data refresh and persistent storage for rolling, live operation.
- Add alerts when the latest forecast run differs sharply from the previous one.

---

## Use of AI tools
This project was built with the help of **Claude Code (Anthropic)**, an AI coding assistant. It was used to explore the Elexon API, scaffold the backend and frontend, write tests, draft the documentation and the video script, and review the UI. All code and the analysis were reviewed and run locally, and the results were checked against the raw Elexon data.
