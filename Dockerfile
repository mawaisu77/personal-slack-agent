# T-052 — production image should pin digest, run as non-root, and set HEALTHCHECK in prod.
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY personal_ai ./personal_ai

RUN pip install --no-cache-dir -U pip hatchling && \
    pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["uvicorn", "personal_ai.slack_interface.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
