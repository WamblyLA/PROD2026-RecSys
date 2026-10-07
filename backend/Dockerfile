# syntax=docker/dockerfile:1

ARG PY_IMAGE=python:3.12-slim

# --------------------------------------------- builder
FROM ${PY_IMAGE} AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY ./src ./src

RUN uv sync --no-cache --group backend


# ---------------------------------------------- api
FROM ${PY_IMAGE} AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src ./src

CMD ["python", "src/app/presentation/api/bootstrap/main.py"]
