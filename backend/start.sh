#!/usr/bin/env sh
set -eu

PORT_VALUE="${PORT:-8000}"

alembic -c /app/alembic.ini upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_VALUE}"
