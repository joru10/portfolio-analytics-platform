# Product Spec: Portfolio Analytics Platform

## 1. Objective
Build an app that reproduces and extends the spreadsheet-based portfolio tracking workflow into a reliable, testable, API-first system suitable for institutional workflows.

## 2. Problem Statement
Spreadsheet-only systems are fast to start but become brittle at scale:
- Logic spread across formulas and scripts
- Low testability and weak lineage/auditability
- Data-source reliability and governance gaps

## 3. Goals (v1)
- Ingest trades from broker exports (CSV/XLSX)
- Maintain canonical portfolio ledger
- Compute positions, realized/unrealized PnL, exposure, and risk metrics
- Provide dashboard API + downloadable Excel reports
- Support scheduled refresh/update runs

## 4. Non-Goals (v1)
- Order execution or broker trading API writes
- Multi-tenant entitlements at enterprise depth
- Intraday tick-level backtesting engine

## 5. Users
- PM/analyst maintaining strategy portfolios
- Operations user validating books and reports
- Developer extending data connectors and metrics

## 6. Functional Requirements
1. Trade ingestion
- Upload CSV/XLSX trade files
- Validate schema and normalize fields
- Idempotent import with duplicate detection

2. Market/reference data
- Adapter layer for providers
- EOD pricing for all held symbols
- FX normalization for base currency support

3. Analytics engine
- Position quantities by instrument/account
- Realized/unrealized PnL
- Portfolio return series
- Risk metrics: volatility, Sharpe, max drawdown, VaR/CVaR (historical, configurable)
- Concentration and sector/country exposures (where mapping available)

4. Reporting
- REST API for dashboard cards/tables/charts
- Export workbook with deterministic tab outputs
- Daily snapshot persistence for audit/repro

5. Operations
- Scheduled refresh jobs
- Structured logging + run metadata
- Health checks and readiness probes

## 7. Architecture (v1)
- Backend: Python 3.12 + FastAPI
- Database: Postgres 16
- Cache/queue: Redis (optional in v1, enabled for scheduled jobs)
- Frontend: React + Vite
- Jobs: APScheduler/Celery (decision in ADR)
- Infra: Dockerized local stack, cloud deployment later

## 8. Data Model (initial)
- `accounts`
- `instruments`
- `trades`
- `corporate_actions`
- `prices_eod`
- `fx_rates`
- `positions_snapshot`
- `portfolio_metrics_snapshot`
- `job_runs`

## 9. API Surface (initial)
- `GET /health`
- `POST /v1/trades/import`
- `GET /v1/positions`
- `GET /v1/metrics`
- `GET /v1/returns`
- `POST /v1/reports/excel`

## 10. Quality Attributes
- Deterministic calculations with fixed rounding policy
- Reproducible snapshots by valuation date
- Unit + integration tests for calculations and ingestion
- Pydantic validation on all external inputs

## 11. Security & Compliance Baseline
- Secrets in environment/secret manager only
- Access logs for import/export/report generation
- Strict dependency pinning and vulnerability scanning in CI

## 12. Milestones
- M1: Core ledger + ingestion + health + CI
- M2: Prices + positions + PnL + tests
- M3: Risk metrics + report export + scheduler
- M4: Frontend dashboard + auth + deployment
