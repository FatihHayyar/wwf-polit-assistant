FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
COPY migrations ./migrations
COPY alembic.ini ./
COPY data/demo ./data/demo

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /app/logs \
    && chown app:app /app/logs

# The application only writes run reports and sync state below /app/logs.
USER app

CMD ["python", "-u", "-m", "scripts.sync.scheduler"]
