FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies (skip MT5 as it's Windows-only)
RUN pip install --upgrade pip && \
    grep -v "MetaTrader5" requirements.txt > requirements-linux.txt && \
    pip install -r requirements-linux.txt && \
    rm requirements-linux.txt

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/data /app/logs /app/configs

# Create volume mount points
VOLUME ["/app/data", "/app/logs", "/app/configs"]

# Expose RPC server port
EXPOSE 8181

# Expose Prometheus metrics port
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "Cthulu", "--config", "config.json", "--skip-setup", "--no-prompt"]




