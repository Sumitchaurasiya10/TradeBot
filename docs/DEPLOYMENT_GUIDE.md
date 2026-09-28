# TradeBot India — Cloud Deployment Guide (Vercel + Render)

This guide provides step-by-step instructions to deploy **TradeBot India** for free using **Render** for the FastAPI Python backend and **Vercel** for the Next.js frontend.

---

## Architecture Overview

```
                      +-----------------------------+
                      |       Next.js 14 Web UI     |
                      |      (Hosted on Vercel)     |
                      +--------------+--------------+
                                     |
               HTTPS (REST API)      |      WSS (Live Ticks & Candlesticks)
                                     v
                      +-----------------------------+
                      |       FastAPI Backend       |
                      |      (Hosted on Render)     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   SQLite / PostgreSQL DB    |
                      |   (Auto-seeded Trader Acc)  |
                      +-----------------------------+
```

---

## Step 1: Push Code to GitHub

1. If you haven't already, initialize or push your project to a GitHub repository:
   ```bash
   git add .
   git commit -m "feat: prepare project for cloud deployment"
   git remote add origin https://github.com/<your-username>/TradeBot.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 2: Deploy Backend on Render (Free)

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. Click **New +** > **Web Service**.
3. Select your GitHub repository (`TradeBot`).
4. Configure the Web Service settings:
   - **Name**: `tradebot-backend` (or your chosen name)
   - **Region**: Choose the closest region (e.g. `Singapore` or `Oregon`)
   - **Branch**: `main` (or `master`)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Under **Environment Variables**, add:
   | Key | Value | Notes |
   |---|---|---|
   | `PYTHON_VERSION` | `3.11.9` | Ensures Python 3.11 runtime |
   | `ENVIRONMENT` | `production` | Production mode |
   | `SECRET_KEY` | *(Click "Generate")* | Random secure JWT key |
   | `LOG_LEVEL` | `INFO` | Standard logging |
   | `CORS_ORIGINS` | `http://localhost:3000` | Will also match `*.vercel.app` automatically |

6. Click **Create Web Service**.
7. Wait 2–3 minutes for the build to finish. Once deployed, Render will provide your public backend URL, for example:
   `https://tradebot-backend.onrender.com`
8. Verify it works by opening in your browser:
   `https://tradebot-backend.onrender.com/docs` (FastAPI Swagger UI will open!)

---

## Step 3: Deploy Frontend on Vercel (Free)

1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **Add New...** > **Project**.
3. Import your `TradeBot` repository.
4. In the **Configure Project** screen:
   - **Project Name**: `tradebot-india`
   - **Framework Preset**: `Next.js` (automatically detected)
   - **Root Directory**: Click **Edit** and select `frontend`
5. Expand **Environment Variables** and add:
   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://tradebot-backend.onrender.com/api/v1` *(replace with your Render URL)* |
6. Click **Deploy**.
7. Vercel will install dependencies, build the Next.js production bundle, and assign a live URL, for example:
   `https://tradebot-india.vercel.app`

---

## Step 4: Verification

1. Open your live Vercel URL (`https://tradebot-india.vercel.app`).
2. You will be greeted by the **Authentication Gate**.
3. Click **1-Click Demo Login (`demo@tradebot.in`)** or create a new trader account.
4. You will enter the live terminal with:
   - Live tick streaming via WebSocket (`wss://`)
   - Brokerage-style order placement with ₹1,00,000 virtual balance
   - F&O Option Chain analysis
   - Strategy signals & portfolio tracking
