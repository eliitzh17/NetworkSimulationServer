# ---- Build stage ----
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Set work directory
WORKDIR /app

# Install pipenv or pip-tools if you use them (optional)
# RUN pip install pipenv

# Copy requirements first for better cache
COPY requirements.txt .

# Install dependencies to a virtual environment in /install
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# ---- Final stage ----
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m appuser

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Set permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 9090 8001 8002 8003

# Set environment variables (override in docker-compose or k8s)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Entrypoint: run main app
CMD ["python", "main.py"]
