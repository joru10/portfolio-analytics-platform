# Portfolio Analytics Platform

Production-oriented portfolio analytics app inspired by spreadsheet-first workflows, with deterministic backend logic and AI-assisted developer tooling.

## Monorepo Layout

- `docs/` product and engineering specs
- `backend/` FastAPI service (portfolio ledger, analytics, data adapters)
- `frontend/` React dashboard (placeholder scaffold)
- `.github/` CI, templates, repo hygiene
- `infra/` deployment/infrastructure notes and IaC placeholders

## Quickstart

```bash
cp .env.example backend/.env
make bootstrap
make db-up
make migrate
make run
```

API health: `http://localhost:8000/health`
UI: `http://localhost:8000/`
OpenAPI docs: `http://localhost:8000/docs`

No-upload compare API: `POST /v1/companies/compare` (symbols + providers)

## Local DB and Migrations

```bash
make db-up
make migrate
make db-down
```

## Initial Roadmap

1. Trade ingestion API + canonical ledger model
2. Market data adapter abstraction + first provider
3. Positions, PnL, risk metrics endpoints
4. Dashboard + Excel export parity checks
5. Auth, audit trail, and scheduled jobs

## Guides

- End-user setup and usage: `docs/user-guide.md`
- Deployment options: `docs/deployment-guide.md`

## Codex Workflow

- Use Codex for implementation, tests, and refactoring
- Keep core business logic deterministic and test-covered
- Use AI for scaffolding/docs/automation, not source-of-truth calculations
