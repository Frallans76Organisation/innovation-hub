# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory and set ownership for OpenShift (non-root)
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with retry and timeout settings
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout=1000 --retries=5 -r requirements.txt

# Copy application code
COPY . .

# Create directories for persistent data with proper permissions
RUN mkdir -p /app/data /app/chroma_db && \
    chmod -R 777 /app/data /app/chroma_db

# OpenShift runs containers with random UIDs, so we need to ensure
# the application directory is writable by the root group
RUN chgrp -R 0 /app && \
    chmod -R g=u /app

# Create a non-root user (OpenShift will override UID but respect GID)
RUN useradd -m -u 1001 -g 0 appuser && \
    chown -R 1001:0 /app

# Switch to non-root user
USER 1001

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application with uvicorn directly
CMD ["python", "-m", "uvicorn", "innovation_hub.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
