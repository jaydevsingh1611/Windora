# Assignment Status

This document lists **what the assignment asked for**, **what has been done**, and **what is still left to do**. It uses simple language.

Status keys: ✅ Done · ⏳ Ready, but needs a person to finish it · ❌ Not started

---

## 1. What the assignment asked for (summary)

**The setting.** We act as a product developer building software for a client. The client is a UK energy company. Their team buys electricity in the **day-ahead market**, which means they buy one day before the power is used. Wind power changes with the weather, so the team depends on **wind forecasts** to decide how much extra power to buy.

**The app must help the team to:**
1. Clearly see the **latest wind forecast available at the time they make their buying decision**.
2. Measure **how accurate the forecasts are**, in numbers, so they can include the error in their decisions.

**Rules and limits:**
- Use only Elexon data, at national level:
  - Actuals: **FUELHH** with `fuelType = WIND` (fields: `startTime`, `generation`)
  - Forecasts: **WINDFOR** (fields: `startTime`, `publishTime`, `generation`)
- Only data for **buying decisions made in January 2026**.
- **React** for the frontend, **Python** for the backend.
- AI tools are allowed, but this must be **said in the README**.
- Use **Docker**.
- Deploy a sample of the app on **Vercel or Heroku**.
- Spend no more than **16 hours**.

**Deliverables (things to hand in):**
1. **Video** (unlisted YouTube, max 10 minutes):
   - Part 1: pitch the product to the client (max 5 minutes).
   - Part 2: explain the architecture, design, analysis, code and practices to a tech lead (max 5 minutes).
2. **Public GitHub repo** with an anonymous random name (for example `kjhwr`). The README must have:
   - details of the files and folders
   - how to start the app
   - the link to the deployed app
3. **Submission form** with all the links. Each link must be opened in **incognito mode** first to check that others can access it.

---

## 2. What has been done

### Product requirements

| Requirement | Status | How it was done / where to find it |
|---|---|---|
| Understand the domain | ✅ | Explored both Elexon datasets. Found that forecasts come 8 times a day and are hourly, actuals are every 30 minutes, and the day-ahead market closes around 09:20 UK time. |
| Show the latest forecast available at decision time | ✅ | "Decision gate" mode: for each delivery day, the app uses the newest forecast published before 09:20 the day before. The gate time can be changed. A "Fixed lead time" mode is also available. Code: `backend/app/forecast.py` |
| Measure forecast accuracy in numbers | ✅ | MAE, RMSE, bias, P10/P50/P90 error, worst error, and "P90 shortfall cover" (how many extra MW to buy to be safe 9 times out of 10). Also broken down by hour of day, by delivery day and by lead time. Code: `backend/app/metrics.py` |
| Use only FUELHH (WIND) and WINDFOR from Elexon | ✅ | `backend/app/elexon.py`. A saved copy is in `backend/data/snapshot_jan2026.json` |
| Only decisions made in January 2026 | ✅ | Decisions on 1–31 Jan buy power for **2 Jan – 1 Feb 2026**, so this is the date range used. `backend/app/config.py` |
| React frontend | ✅ | React 19 + TypeScript + Vite + Recharts, in `frontend/` |
| Python backend | ✅ | FastAPI, in `backend/` |
| AI tools mentioned in README | ✅ | Section "Use of AI tools" in `README.md` |
| Docker | ✅ | `backend/Dockerfile`, `frontend/Dockerfile` and `docker-compose.yml`. Tested: both containers run and the backend reports healthy. |
| Deploy on Vercel or Heroku | ⏳ | All the configuration is ready (`vercel.json`, `api/index.py`, root `requirements.txt`) and the guide is written. **It is not deployed yet**, because that needs a Vercel login. |

### Deliverables

| Deliverable | Status | Notes |
|---|---|---|
| Video script, Part 1 (client pitch) | ✅ | `docs/VIDEO_SCRIPT.md`, with timings |
| Video script, Part 2 (tech lead review) | ✅ | `docs/VIDEO_SCRIPT.md`, with timings |
| Video recording on YouTube (unlisted) | ❌ | Must be recorded by you |
| README: details of files and folders | ✅ | "Repository layout" section |
| README: how to start the app | ✅ | "Running it" section (Docker and local) |
| README: link to the deployed app | ⏳ | Placeholder `<add Vercel URL here after deploy>` for now |
| Public GitHub repo with a random name | ❌ | Not created yet. The local git repo exists and all files are staged, but **not committed yet**, because a git name and email are not set on this computer. |
| Submission form | ❌ | Fill it in at the end |
| Check all links in incognito mode | ❌ | Do this after deploying and uploading |

### Extra work (not asked for, but helps the review)

| Item | Where |
|---|---|
| 18 automatic backend tests (forecast choice, maths, API) | `backend/tests/` |
| Plain-English architecture guide | `docs/ARCHITECTURE.md` |
| Step-by-step deployment guide | `docs/DEPLOYMENT.md` |
| Full end-to-end check of everything in the docs (API, browser test of every control, Docker, local run, data refresh) | Done. Two problems were found and fixed: the chart tooltip and the slow chart updates. |
| Works on mobile, and supports dark mode | `frontend/src/index.css` |
| Colour-blind-friendly chart colours | `frontend/src/index.css` |
| Plain-English summary of the results at the top of the page | `frontend/src/components/Insight.tsx` |

### Main findings (useful for the video)
- On average, the forecast available at 09:20 the day before was **2.02 GW** off each hour, which is **18%** of wind output.
- The forecast was **too high by 1.75 GW on average**: wind came in below forecast in **85% of hours**.
- Buying about **4.15 GW** more than the forecast suggested would have covered the shortfall in **9 out of 10 hours**.
- Forecasts get worse the further ahead they look: about **1.66 GW** error at 0–4 hours vs **2.34 GW** at 44–48 hours.

---

## 3. What is still left to do

### Must do (needed to submit). Do them in this order.

| # | Task | Who | How |
|---|---|---|---|
| 1 | Set your git name and email | You | `git config user.name "Your Name"` and `git config user.email "you@example.com"` |
| 2 | Make the first commit | You / Claude | `git commit -m "Initial version of Wind Position Monitor"` |
| 3 | Create a **public** GitHub repo with a random name (for example `kjhwr`) and push | You | See `docs/DEPLOYMENT.md`, section 5 |
| 4 | Deploy to Vercel | You (login) + Claude | `npx vercel login`, then `npx vercel --prod`. See `docs/DEPLOYMENT.md`, section 3 |
| 5 | Turn off Vercel **Deployment Protection** for production | You | See `docs/DEPLOYMENT.md`, section 6 |
| 6 | Put the Vercel link in `README.md`, commit and push | You / Claude | Replace `<add Vercel URL here after deploy>` |
| 7 | Record the video (Part 1 + Part 2, max 10 minutes in total) | You | Follow `docs/VIDEO_SCRIPT.md`, using the live Vercel app |
| 8 | Upload to YouTube as **Unlisted** | You | YouTube Studio → Upload → Visibility: **Unlisted** |
| 9 | Open the GitHub repo, the Vercel app and the YouTube video in **incognito mode** | You | Each one must open without logging in |
| 10 | Fill in and submit the form | You | "Full Stack SWE challenge submission v4" |

### Nice to have (optional improvements)

| Item | Why |
|---|---|
| Move `.venv` into `backend/` | Cleaner layout, since only the backend uses Python (the docs would need a small update) |
| GitHub Actions to run tests on every push | Shows good engineering practice to the reviewer |
| Frontend tests (for example Vitest) | Right now only the backend has automatic tests |
| Split the frontend bundle | The build warns that the JS file is a bit large (about 640 KB, 188 KB gzipped). It works fine, but it could load faster. |
| Bias-corrected forecast and hourly buy recommendations | A natural "next phase" to pitch to the client |
| Add solar and electricity demand | Shows the full position, not only wind (outside this assignment's scope) |
