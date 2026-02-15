# Sample Trade Datasets

Use these fake datasets to test import, idempotency, and validation.

Files:
- `trades_seed.csv`: baseline portfolio across two accounts
- `trades_incremental.csv`: next batch with one intentional duplicate (`BRK-1010` row)
- `trades_bad_rows.csv`: invalid rows to test error handling

## Quick API test (local)

```bash
curl -X POST "http://localhost:8000/v1/trades/import" -F "file=@sample-data/trades_seed.csv"
curl -X POST "http://localhost:8000/v1/trades/import" -F "file=@sample-data/trades_incremental.csv"
curl "http://localhost:8000/v1/metrics?snapshot_date=2026-02-14"
```

## Quick UI test

1. Open `http://localhost:8000/`
2. Import `trades_seed.csv`
3. Click `Refresh Prices`
4. Click `Load Positions + Metrics`
5. Import `trades_incremental.csv` and repeat to confirm duplicate handling
