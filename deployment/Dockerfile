# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY config.py ./config.py

# Copy .env if present (optional, for local dev)
COPY .env .env

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
