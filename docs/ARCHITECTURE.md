# Architecture Guide

This document explains how the Wind Position Monitor is built, what each part does, and how to run it. It uses simple language.

---

## 1. What the app does (in short)

The app helps a power buying team in the UK.

- Every day, the team buys electricity for the **next day** in the "day-ahead market".
- Part of the electricity comes from **wind**. Wind changes with the weather, so the team uses a **wind forecast** to decide how much extra power to buy.
- The app shows:
  1. **Which forecast** the team had at the moment they had to buy.
  2. **How wrong** that forecast usually was, in numbers (MW / GW).

All data comes from **Elexon** (the UK electricity data service). We only look at **January 2026**.

---

## 2. The big picture

The app has three main parts:

```
 ┌──────────────────────┐        ┌──────────────────────────┐        ┌───────────────────┐
 │   User's browser     │        │   Backend (Python)       │        │   Elexon API      │
 │                      │  HTTP  │                          │  HTTP  │   (public data)   │
 │   Frontend (React)   │ ─────► │   FastAPI  /api/...      │ ─────► │   FUELHH (actual) │
 │   charts + tables    │ ◄───── │   does all calculations  │ ◄───── │   WINDFOR (fcst)  │
 └──────────────────────┘  JSON  └────────────┬─────────────┘        └───────────────────┘
                                              │ reads first
                                              ▼
                                  ┌──────────────────────────┐
                                  │  Saved data file          │
                                  │  snapshot_jan2026.json    │
                                  └──────────────────────────┘
```

1. **Frontend**: the web page the user sees. It is built with **React**. It shows the charts and the controls.
2. **Backend**: a small server built with **Python (FastAPI)**. It loads the data, picks the right forecast, and calculates the errors.
3. **Data**: the wind numbers from Elexon. We save a copy in a file so the app is fast and still works if Elexon is down.

---

## 3. The data we use

| Dataset | What it has | Time step |
|---|---|---|
| **FUELHH** (fuelType = WIND) | How much wind power was **actually** produced | Every 30 minutes |
| **WINDFOR** | Wind power **forecasts** | Every 1 hour |

Important fields:
- `startTime`: the time the value is for.
- `publishTime` (forecasts only): when the forecast was made.
- `generation`: the amount of power in MW.

Forecasts are made about **8 times a day** (in UK time: 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30). Each one looks up to about 2–3 days ahead.

**Which days?** A decision made on a day in January buys power for the **next** day. So decisions from 1–31 January cover delivery days **2 January to 1 February 2026**.

---

## 4. The main idea: "which forecast did we have?"

There are many forecasts for the same hour, because new ones keep coming out. We must pick the one the team really had **when they bought**.

**Mode 1: Decision gate (default)**
- The day-ahead market closes at about **09:20 UK time** on the day before delivery.
- For each hour of the delivery day, we take the **newest forecast published before 09:20 the day before**.
- Example: for 10 January, we use the forecast published at 07:30 on 9 January.
- The user can change the 09:20 time.

**Mode 2: Fixed lead time**
- The user picks a number of hours, for example 24.
- For each hour, we take the newest forecast made **at least 24 hours before** that hour.

**Error**
- `error = forecast − actual`
- A **positive** error means there was **less wind than forecast**, so the team was short and had to buy more.
- A **negative** error means there was **more wind than forecast**.

---

## 5. Backend components (folder `backend/`)

| File | What it does |
|---|---|
| `app/config.py` | Settings: the date range, the default gate time (09:20) and the location of the data file. |
| `app/elexon.py` | Downloads data from the Elexon API. Tries again if a request fails. |
| `app/repository.py` | Loads the data once when the server starts. Reads the saved file first; if the file is missing, downloads from Elexon. |
| `app/forecast.py` | Picks the correct forecast for each hour (gate mode or lead-time mode). It is pure logic: no internet, no files. |
| `app/metrics.py` | Does the maths: average error (MAE), RMSE, bias, percentiles, and errors grouped by hour, by day and by lead time. Also pure logic. |
| `app/service.py` | Joins everything together: data → pick forecast → calculate errors → return results. |
| `app/models.py` | Checks the user's inputs (for example, dates must be inside the pilot range). |
| `app/main.py` | Defines the web addresses (API routes). |
| `data/snapshot_jan2026.json` | The saved copy of the Elexon data (about 1 MB). |
| `scripts/refresh_snapshot.py` | Downloads fresh data and saves a new snapshot file. |
| `tests/` | Automatic tests that check the logic and the API. |

### API routes

| Address | What it returns |
|---|---|
| `GET /api/health` | `{"status": "ok"}` if the server is running |
| `GET /api/meta` | Date range, default settings and data source |
| `GET /api/series` | Actual and forecast values over time (for the main chart) |
| `GET /api/analysis` | Error numbers, plus errors by hour and by day, and the error histogram |
| `GET /api/horizon-accuracy` | How error changes with lead time (0–48 hours) |

Inputs you can send: `start`, `end` (dates), `mode` (`gate` or `horizon`), `gate` (time, for example `09:20`) and `horizon` (hours).

Example:
```
/api/analysis?start=2026-01-02&end=2026-02-01&mode=gate&gate=09:20
```

### How a request flows through the backend

```
Browser asks /api/analysis
        │
        ▼
main.py ──► models.py (check inputs)
        │
        ▼
service.py
   ├─ repository.py  → gets the data (already in memory)
   ├─ forecast.py    → picks the right forecast for each hour
   └─ metrics.py     → calculates the errors
        │
        ▼
JSON answer sent back to the browser
```

---

## 6. Frontend components (folder `frontend/`)

| File | What it does |
|---|---|
| `src/App.tsx` | The main page. Keeps the user's settings and asks the backend for data when they change. The charts only redraw when new data arrives, so moving a control stays fast. |
| `src/api.ts` | Functions that call the backend, plus the data types. |
| `src/format.ts` | Helpers to show numbers (GW) and dates (UK time) nicely. |
| `components/Controls.tsx` | Date pickers, mode switch, gate time box and lead-time slider. |
| `components/Insight.tsx` | A short summary in plain English at the top. |
| `components/KpiTiles.tsx` | The five number boxes: MAE, bias, P90 cover, RMSE and lead time. |
| `components/ForecastChart.tsx` | The main line chart: actual vs forecast, with an uncertainty band. |
| `components/ErrorCharts.tsx` | Three smaller charts: error sizes, error by lead time and error by hour of day. |
| `components/DailyTable.tsx` | A table with one row for each delivery day. |
| `nginx.conf` | Used in Docker: serves the web page and sends `/api` calls to the backend. |

**What happens when the user changes a setting:**
1. `Controls` updates the settings in `App`.
2. `App` waits a moment (150 ms), then makes 3 API calls at the same time.
3. When the answers arrive, all charts and tables update together (the summary text, numbers and charts always match the same settings).

---

## 7. Deployment (how it runs online)

### Docker (on your own computer)
There are two containers:
- **backend**: Python + FastAPI, on port **8000**
- **frontend**: nginx serving the built React page, on port **8080**. It forwards `/api` calls to the backend.

`docker-compose.yml` starts both together.

### Vercel (on the internet)
Everything is one Vercel project:
- The React app is built into plain files and served as a website.
- `api/index.py` runs the FastAPI backend as a **serverless function**.
- `vercel.json` sends every `/api/...` request to that function.

For step-by-step instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

## 8. How to run it

### Option A: Docker (easiest)
You need: Docker Desktop.

```bash
docker compose up --build
```
Then open:
- App: http://localhost:8080
- API docs: http://localhost:8000/docs

To stop it:
```bash
docker compose down
```

### Option B: Run without Docker
You need: Python 3.12 or newer, and Node.js 22 or newer.

**Step 1: start the backend** (terminal 1)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

**Step 2: start the frontend** (terminal 2)
```bash
cd frontend
npm install
npm run dev
```
Then open http://localhost:5173

### Run the tests
```bash
cd backend
pytest
```

### Get fresh data from Elexon
```bash
cd backend
python -m scripts.refresh_snapshot
```

### Deploy to Vercel
```bash
npx vercel login
npx vercel --prod
```
Full guide (GitHub import, checks, common problems): **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

## 9. Why it is built this way

- **Logic is kept separate.** The forecast picking and the maths are in their own files, with no internet or file access. This makes them easy to test and easy to understand.
- **Saved data file.** January 2026 is in the past and will not change, so we save it once. The app starts fast and does not depend on Elexon being online.
- **Small backend.** It uses only FastAPI and httpx (no pandas), so it loads quickly on Vercel.
- **UK time everywhere.** Delivery days and the 09:20 gate use UK time, including summer time changes.
- **Never uses future forecasts.** A forecast published after the hour it predicts is never used.
