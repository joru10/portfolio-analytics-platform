FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]"

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
