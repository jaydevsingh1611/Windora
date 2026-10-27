# Deployment Guide

This guide explains how to put the Wind Position Monitor on the internet using **Vercel**, how to check that it works, and how to fix common problems. It uses simple language.

---

## 1. How the deployment works

The whole app runs as **one Vercel project** with **one web address**.

```
                    https://your-app.vercel.app
                               │
              ┌────────────────┴────────────────┐
              │                                 │
     /  (any normal page)                /api/...  (data requests)
              │                                 │
              ▼                                 ▼
   Static website files              Python serverless function
   (React app, built into            api/index.py → loads the
    frontend/dist)                    FastAPI app from backend/
```

- **Frontend:** Vercel builds the React app once into plain HTML, CSS and JS files and serves them very fast.
- **Backend:** Vercel runs `api/index.py` as a **serverless function**. It starts when a request comes in and loads the FastAPI app from the `backend/` folder.
- **Data:** the saved data file (`backend/data/snapshot_jan2026.json`) is packed together with the function, so no database is needed.

### The files Vercel uses

| File | Why it is needed |
|---|---|
| `vercel.json` | Tells Vercel how to build the frontend, where the built files are, and to send every `/api/...` request to the Python function. |
| `api/index.py` | The Python function entry point. Vercel only turns files in a top-level `api/` folder into functions. This file just loads `backend/app/main.py`. |
| `requirements.txt` (root) | The Python packages the function needs (FastAPI, httpx). Vercel looks for this file at the root. |
| `.vercelignore` | Files Vercel should **not** upload (local virtual env, node_modules, tests). |

What `vercel.json` says, in plain words:

| Setting | Meaning |
|---|---|
| `installCommand: cd frontend && npm ci` | Install the frontend packages |
| `buildCommand: cd frontend && npm run build` | Build the React app |
| `outputDirectory: frontend/dist` | The built website is in this folder |
| `functions → includeFiles: backend/**` | Pack the backend code and data file with the Python function |
| `rewrites: /api/(.*) → /api/index` | Send all API requests to the Python function |

**No environment variables or secrets are needed.** The Elexon API is public.

---

## 2. Before you start

You need:
- A free **Vercel account**: https://vercel.com/signup (signing up with GitHub is easiest).
- **Node.js 22 or newer** on your computer (only needed for Option A).
- For Option B: the code pushed to a **GitHub repository** (see section 5).

Optional but recommended: run the app locally first (see `docs/ARCHITECTURE.md`, section 8) to make sure it works before deploying.

---

## 3. Option A: Deploy from your computer (Vercel CLI)

This is the quickest way. Run all commands from the **project root folder** (the folder containing `vercel.json`).

**Step 1: log in to Vercel**
```bash
npx vercel login
```
Choose how to log in (for example "Continue with GitHub") and finish in the browser.

**Step 2: make a first (preview) deployment**
```bash
npx vercel
```
Vercel asks a few questions. Answer like this:

| Question | Answer |
|---|---|
| Set up and deploy? | **Y** |
| Which scope? | Your personal account |
| Link to existing project? | **N** |
| What's your project's name? | Any name, for example `wind-monitor` |
| In which directory is your code located? | **./** (press Enter) |
| Want to modify these settings? | **N** (vercel.json already has the right settings) |

At the end you get a **preview URL**. Open it and check it works (see section 6).

**Step 3: deploy to production**
```bash
npx vercel --prod
```
This gives you the final, stable address, for example `https://wind-monitor.vercel.app`. **This is the link to put in the README and the submission form.**

**Later updates:** after you change the code, just run `npx vercel --prod` again.

---

## 4. Option B: Deploy from GitHub (automatic updates)

With this option, Vercel deploys again by itself every time you push to GitHub.

1. Push the code to GitHub (see section 5).
2. Go to https://vercel.com/new.
3. Click **Import** next to your repository. If you don't see it, click "Adjust GitHub App Permissions" and give Vercel access to the repo.
4. On the settings screen:
   - **Root Directory:** leave as `./`
   - **Framework Preset:** leave as detected ("Other" is fine)
   - **Build and Output Settings:** don't change anything (vercel.json is used)
   - **Environment Variables:** none needed
5. Click **Deploy** and wait about 1–2 minutes.
6. Click **Visit** to open the app.

From now on:
- A push to the `main` branch → new **production** deployment.
- A push to any other branch or a pull request → a **preview** deployment with its own URL.

---

## 5. Pushing the code to GitHub

The assignment needs a **public** repo with a **random name** (for example `kjhwr`).

1. Go to https://github.com/new.
2. **Repository name:** a random string, for example `kjhwr`.
3. Choose **Public**.
4. Do **not** add a README, .gitignore or license (the project already has them).
5. Click **Create repository**, then run from the project root:

```bash
git add -A
git commit -m "Initial version of Wind Position Monitor"
git remote add origin https://github.com/<your-username>/kjhwr.git
git push -u origin main
```

If git asks for a password, use a **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens), not your account password. Or install the GitHub CLI and run `gh auth login`.

---

## 6. Check that the deployment works

Replace `https://your-app.vercel.app` with your real address.

| Check | How | Expected result |
|---|---|---|
| Backend is running | Open `https://your-app.vercel.app/api/health` | `{"status":"ok"}` |
| Data is loaded | Open `https://your-app.vercel.app/api/meta` | JSON with `"dataSource":"snapshot"` |
| Website loads | Open `https://your-app.vercel.app` | The dashboard with charts and numbers |
| Controls work | Switch to "Fixed lead time" and move the slider | Numbers and charts update |
| Public access | Open the link in an **incognito / private window** | It opens **without** asking you to log in |

Note: the **first request after a quiet period can take a few seconds**. This is normal for serverless functions (a "cold start"). Later requests are fast.

### Make sure the link is public
New Vercel projects can have **Deployment Protection** turned on, which asks visitors to log in. The assignment reviewers must be able to open the link, so check it:

1. Open the project on vercel.com → **Settings** → **Deployment Protection**.
2. Make sure **Vercel Authentication** is **off** for production (or set to "Only Preview Deployments").
3. Test again in an incognito window.

---

## 7. After deploying

1. Put the production link in `README.md` (replace `<add Vercel URL here after deploy>`).
2. Commit and push (or run `npx vercel --prod` again) so the README on GitHub has the link.
3. Use the same link in the demo video and the submission form.

---

## 8. Common problems and fixes

| Problem | Likely cause | Fix |
|---|---|---|
| Build fails at `npm ci` | `frontend/package-lock.json` is missing from the repo | Commit `frontend/package-lock.json` and deploy again |
| Website loads, but shows "Request failed (404)" | `/api` requests are not reaching the Python function | Check that `vercel.json` (with the `rewrites` part) and `api/index.py` are in the repo, at the root |
| `/api/health` gives error 500 | The function crashed while starting | Open the project on vercel.com → **Logs** (or run `npx vercel logs <url>`) to see the Python error |
| Logs show `ModuleNotFoundError: No module named 'app'` | The backend files were not packed with the function | Check that `vercel.json` has `"includeFiles": "backend/**"` and that `backend/` is not in `.vercelignore` |
| Logs show `ModuleNotFoundError: fastapi` | Root `requirements.txt` is missing | Commit the root `requirements.txt` |
| `/api/meta` shows `"dataSource":"live"` and the first load is slow | The snapshot file was not uploaded, so data is downloaded from Elexon | Check that `backend/data/snapshot_jan2026.json` is committed |
| Reviewers see a Vercel login page | Deployment Protection is on | Turn it off for production (section 6) |
| The old version still shows | Browser cache, or you only made a preview deployment | Hard refresh (Ctrl/Cmd + Shift + R), and make sure you ran `npx vercel --prod` |

---

## 9. Other ways to host it (not needed for the assignment)

The app also comes with Docker files, so it can run on any server or platform that supports containers:

```bash
docker compose up --build -d
```
This starts the website on port **8080** and the API on port **8000**. To use the app from other computers, open port 8080 on the server's firewall and point a domain name to it.
