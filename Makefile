.PHONY: bootstrap run test lint

bootstrap:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -e .[dev]

run:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && . .venv/bin/activate && pytest -q

lint:
	cd backend && . .venv/bin/activate && ruff check .
