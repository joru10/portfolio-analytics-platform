# Trade Import Contract

Defines the canonical broker-file schema for `POST /v1/trades/import`.

## File formats
- Supported: `.csv`, `.xlsx`
- Header row required
- Column names are case-insensitive and trimmed

## Required columns
- `account` (string)
- `symbol` (string)
- `trade_date` (date)
- `side` (`BUY` or `SELL`)
- `quantity` (decimal, must be `> 0`)
- `price` (decimal, must be `>= 0`)

## Optional columns
- `fees` (decimal, default `0`, must be `>= 0`)
- `currency` (string, default `USD`)
- `broker_ref` (string)

## Date parsing
Accepted date formats:
- `YYYY-MM-DD`
- `MM/DD/YYYY`
- `YYYY/MM/DD`

## Normalization
- `symbol`, `side`, and `currency` are uppercased
- Blank optional fields map to defaults

## Idempotency
Each row generates deterministic `trade_uid` by hashing:
- account, symbol, trade_date, side, quantity, price, fees, currency, broker_ref

Rows with existing `trade_uid` are treated as duplicates and are not re-inserted.

## Error behavior
Validation fails with `422` and deterministic messages:
- Missing required fields listed in sorted column order
- Invalid side/date/decimal messages include row number context
