#!/usr/bin/env sh
set -eu

PORT_VALUE="${PORT:-8000}"
if [ -f "/app/alembic.ini" ]; then
  ALEMBIC_CFG="/app/alembic.ini"
else
  ALEMBIC_CFG="alembic.ini"
fi

alembic -c "${ALEMBIC_CFG}" upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_VALUE}"
