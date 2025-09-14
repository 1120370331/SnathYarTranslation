# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    SHATHYAR_DB_URL=sqlite:////app/shathyar.db \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=9301 \
    UVICORN_WORKERS=1 \
    LOG_LEVEL=info \
    RELOAD=false

WORKDIR /app

# Install system dependencies only if needed (kept minimal for manylinux wheels)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ca-certificates \
#  && rm -rf /var/lib/apt/lists/*

# Copy backend project
COPY . /app/

# Ensure container entrypoint is executable
RUN chmod +x /app/container_entrypoint.sh

# Install Python dependencies (project and runtime deps)
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -e .

# Create mount points for logs and data (optional volumes)
RUN mkdir -p /logs /data
VOLUME ["/logs", "/data"]

EXPOSE 9301

ENTRYPOINT ["/app/container_entrypoint.sh"]
CMD []
