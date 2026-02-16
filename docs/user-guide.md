# End-User Guide

## What is already available
- Trade import (`.csv`/`.xlsx`)
- Provider-based company compare (no upload required)
- Price refresh (`demo`, `yfinance`)
- AI Analyst panel (OpenAI/Anthropic via backend keys)
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

### A. Company compare mode (no upload)
1. Open **Settings**
2. Set:
- `API Base URL` (for deployed frontend, set your backend URL)
- `Providers Priority` (example: `yfinance, demo`)
- `Companies to Follow` (example: `AAPL, MSFT, BLAIZE`)
3. Set `Snapshot Date` and `Lookback Days`
4. Click **Compare Companies**
5. Review:
- Relative performance chart
- Return by symbol chart
- Comparison summary table

### C. AI Analyst mode
1. Open **Settings**
2. Set AI provider/model (`OpenAI` or `Anthropic`)
3. Ensure backend has matching API key env var:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Claude
4. Run compare or portfolio analysis first (to create context)
5. Ask a question in **AI Analyst** and click **Analyze with AI**

### B. Portfolio analytics mode (requires trades)

1. Open `http://localhost:8000/`
2. In **Trade Import**, choose your CSV/XLSX file and click **Import Trades**
3. Click **Refresh Prices**
4. Click **Run Analysis**
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
  -d '{"price_date":"2026-02-15","symbols":["AAPL","MSFT"],"providers":["yfinance","demo"]}'
```

Company compare (no upload):

```bash
curl -X POST "http://localhost:8000/v1/companies/compare" \
  -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL","MSFT","BLAIZE"],"start_date":"2025-09-01","end_date":"2026-02-15","providers":["yfinance","demo"]}'
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
- If compare returns no data: verify symbols are valid for selected provider or keep `demo` as fallback
