# Deployment Guide

## Current status
This project is **not auto-deployed yet**. It runs locally and is ready for deployment.

## Recommended production shape
- Frontend UI: Netlify (static hosting)
- Backend API: Render / Railway / Fly.io (container or Python service)
- Database: managed Postgres (Render PG / Neon / Supabase / RDS)
- Redis: managed Redis if/when scheduled jobs need it

Netlify alone is not a good fit for this full backend because you need a persistent API process + Postgres connections + migrations.

## Option A (recommended): Netlify + Backend Host

1. Deploy backend to Render/Railway/Fly with env vars:
- `DATABASE_URL`
- `MARKET_DATA_PROVIDER=demo` (or real provider later)
- `CORS_ALLOW_ORIGINS=https://<your-netlify-site>.netlify.app`

2. Run migrations on backend host:
- `alembic -c alembic.ini upgrade head`

3. Deploy frontend to Netlify:
- Publish directory: `frontend`
- Set UI API base URL manually in input field, or later hardcode/env-wire in frontend build

## Option B: Single service deploy (backend serves UI)
Deploy FastAPI service only. It serves `frontend/index.html` from `/` and API under `/v1/*`.

## Pre-deploy checklist
- Replace demo market data provider
- Add auth before exposing publicly
- Set strict `CORS_ALLOW_ORIGINS`
- Add backups/monitoring for Postgres
- Configure HTTPS and domain
