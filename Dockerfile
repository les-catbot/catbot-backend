FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

FROM base AS production
COPY alembic.ini ./
COPY alembic/ ./alembic/
EXPOSE 8000
CMD ["uvicorn", "catbot.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS development
RUN pip install --no-cache-dir ".[dev]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "catbot.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
