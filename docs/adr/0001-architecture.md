# ADR-0001: API-first, code-centric analytics architecture

## Status
Accepted

## Context
The source workflow blends Python scripts with spreadsheet formulas. We need stronger testability, observability, and reproducibility.

## Decision
Implement portfolio calculations in backend services as deterministic code, and treat spreadsheets as export artifacts.

## Consequences
- Pros: testability, versioning, auditability, easier API integration
- Cons: higher upfront implementation effort vs pure spreadsheet setup
