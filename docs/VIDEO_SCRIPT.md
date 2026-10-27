# Demo video script (max 10 min)

Record your screen with the live app (Vercel URL) and VS Code. Times are targets, so keep each part under 5 minutes. Speak to *outcomes* in Part 1 and to *decisions and trade-offs* in Part 2.

---

## Part 1: Client pitch (≈4:30)

**Audience:** the day-ahead trading team. **Goal:** show them they now understand their wind risk in MW.

**0:00 – 0:30 · The problem**
> "Every morning your team buys tomorrow's power in the day-ahead auction. Wind covers a large, weather-dependent share of demand, so how much you buy depends on a forecast. The question we set out to answer in this pilot is: *how far can you trust the forecast you have at the moment you buy, and what does that error mean in megawatts?*"

**0:30 – 1:15 · What the portal shows (top of page)**
- Point at the controls: delivery days 2 Jan to 1 Feb, which are exactly the days you bought for during January.
- "By default we show the forecast you *actually had* at the 09:20 gate the day before. It isn't a later, better forecast you couldn't have used."
- Read out the insight banner: the forecast missed by about **2 GW an hour on average, 18% of wind output**, and it **over-estimated wind by 1.75 GW**.

**1:15 – 2:15 · The main chart**
- Hover over a few points. The tooltip shows actual, forecast, the error, and *which forecast run* was used (published 07:30 the day before, 16–40 hours ahead).
- Point to an obvious miss, such as 11–12 Jan or 28 Jan: "the forecast said ~19 GW, wind delivered ~14. That's 5 GW you had to buy at short notice."
- Turn on the P10–P90 band: "this is the range actual output fell in, 8 times out of 10."

**2:15 – 3:15 · Turning error into a buying decision**
- KPI tile **P90 shortfall cover ≈ 4.15 GW**: "if you had bought this much on top of what the forecast implied, you'd have been covered in 9 hours out of 10."
- Histogram: "the red side is much bigger than the blue side. Misses are skewed towards wind under-delivering, so the risk isn't symmetric."
- Hour-of-day chart: "early morning hours (03:00–07:00) are the hardest to forecast."

**3:15 – 4:00 · What-if: timing**
- Change the gate to 11:00, then switch to *Fixed lead time* and drag the slider from 48h to 4h. The numbers update live.
- Lead-time chart: "a forecast 4 hours out is ~1.7 GW off, while 2 days out is ~2.3 GW. Waiting helps a bit, but the over-forecast bias stays, so a systematic correction is worth more than a later gate."

**4:00 – 4:30 · Close**
> "In one screen you can see the forecast you'll trade on, how wrong it typically is, and the MW buffer that matches your risk appetite. Next phase: add solar and demand to show your full net position, add live daily updates, and add a bias-corrected forecast with hourly buy recommendations."

---

## Part 2: Tech lead review (≈4:45)

**0:00 – 0:40 · Architecture (show README diagram or file tree)**
- React 19 + TypeScript + Vite + Recharts on the frontend, FastAPI on the backend.
- Deployment is one Vercel project: the SPA is served as static files, and `api/index.py` runs FastAPI as a Python serverless function, with `/api/*` rewritten to it.
- Docker: `docker compose up` runs the backend (uvicorn) and the frontend (nginx, which also proxies `/api`).

**0:40 – 1:30 · Data**
- `elexon.py` calls two public stream endpoints, FUELHH (`fuelType=WIND`, half-hourly) and WINDFOR (hourly targets, 8 runs a day, lead times up to ~66h).
- Scope reasoning: decisions made in January means **delivery days 2 Jan – 1 Feb**. Forecast runs are pulled from 29 Dec, so a 48h lead time still has data.
- `repository.py` loads a bundled snapshot first (fast cold starts, deterministic demo) and falls back to a live fetch. There's also a refresh script.

**1:30 – 2:45 · Core logic (open `forecast.py`, `metrics.py`)**
- `ForecastIndex`: runs grouped by target time and sorted by publish time, so "latest run with publish ≤ cutoff" is a `bisect`.
- `gate_cutoff`: the delivery day is computed in `Europe/London` and the gate is converted back to UTC, so it is DST-safe (point to the summer test).
- The cutoff is also capped at the target time, so a forecast published after the event is never used.
- `metrics.py` sets the sign convention (error = forecast − actual) and computes MAE/RMSE/bias, linear-interpolated percentiles, and P90 shortfall cover. There's no pandas or numpy, which keeps the lambda small.
- `service.py` composes these, and `main.py` is just routing plus validated params (`models.py` rejects out-of-scope dates with a 422).

**2:45 – 3:30 · Frontend**
- `App.tsx` holds one `Query` state. A change triggers three parallel API calls with a 150 ms debounce and cancels stale responses.
- Components are presentational. Chart colours come from CSS tokens validated for colour-blind separation, with dark mode and mobile layout.
- The P10–P90 band is derived as `[forecast − p90, forecast − p10]`.

**3:30 – 4:15 · Quality and practices**
- Run `pytest`: 18 tests, covering forecast selection edge cases (gate boundaries, DST, no available run), hand-computed metrics, and API contract and validation.
- `npm run build` type-checks with strict TS.
- The pure core and thin edges make it easy to add new sources (solar, demand) as another repository plus the same metrics.
- AI tools (Claude Code) were used, as disclosed in the README.

**4:15 – 4:45 · Trade-offs and next steps**
- Snapshot vs live: a database plus a scheduled ingest would be the next step for production.
- Forecast resolution is hourly while actuals are half-hourly. Forecasts are scored on matching timestamps; an alternative is averaging the two half-hours.
- Next: CI (GitHub Actions), caching headers, more datasets, quantile forecasts.
