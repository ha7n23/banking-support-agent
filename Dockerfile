# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-docker.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    python -m pip install -r requirements-docker.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "banking_agent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]