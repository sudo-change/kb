# Service-specific Dockerfile for the collector.
# Identical to root Dockerfile — docker-compose uses `build: .` (root context).
# This file exists for standalone builds: docker build -f collector/Dockerfile .

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "collector/main.py"]
