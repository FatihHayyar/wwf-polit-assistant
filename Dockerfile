
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts

RUN pip install --no-cache-dir .

CMD ["python", "-u", "-m", "scripts.sync.scheduler"]
