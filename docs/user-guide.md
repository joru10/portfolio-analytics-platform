# End-User Guide

## What is already available
- Trade import (`.csv`/`.xlsx`)
- Price refresh (demo provider)
- Positions and portfolio metrics
- Browser UI served by backend at `/`
- API docs at `/docs`

## 1) Local setup

From repo root:

```bash
cp .env.example backend/.env
make bootstrap
make db-up
make migrate
make run
```

Open:
- UI: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

## 2) Prepare a trade file

Required columns:
- `account`
- `symbol`
- `trade_date` (`YYYY-MM-DD` recommended)
- `side` (`BUY` or `SELL`)
- `quantity`
- `price`

Optional:
- `fees`
- `currency`
- `broker_ref`

## 3) Use the UI

1. Open `http://localhost:8000/`
2. In **Trade Import**, choose your CSV/XLSX file and click **Import Trades**
3. Click **Refresh Prices** (uses demo provider now)
4. Click **Load Positions + Metrics**
5. Adjust `Snapshot Date` and optional `Account` filter

## 4) API usage (optional)

Import trades:

```bash
curl -X POST "http://localhost:8000/v1/trades/import" \
  -F "file=@/path/to/trades.csv"
```

Refresh prices:

```bash
curl -X POST "http://localhost:8000/v1/prices/refresh" \
  -H "Content-Type: application/json" \
  -d '{"price_date":"2026-02-15","symbols":[]}'
```

Read positions:

```bash
curl "http://localhost:8000/v1/positions?snapshot_date=2026-02-15"
```

Read metrics:

```bash
curl "http://localhost:8000/v1/metrics?snapshot_date=2026-02-15"
```

## 5) Troubleshooting
- If DB errors appear: run `make db-up` then `make migrate`
- If import fails: check required columns and `side` values
- If UI can’t connect: verify `API Base URL` in the UI
