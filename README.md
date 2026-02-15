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
make bootstrap
make run
```

## Initial Roadmap

1. Trade ingestion API + canonical ledger model
2. Market data adapter abstraction + first provider
3. Positions, PnL, risk metrics endpoints
4. Dashboard + Excel export parity checks
5. Auth, audit trail, and scheduled jobs

## Codex Workflow

- Use Codex for implementation, tests, and refactoring
- Keep core business logic deterministic and test-covered
- Use AI for scaffolding/docs/automation, not source-of-truth calculations
