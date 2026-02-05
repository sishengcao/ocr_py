# Multi-stage Dockerfile for OCR Service (PaddleOCR only)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Use Aliyun mirrors for faster downloads in China
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 ocruser && \
    mkdir -p /app /tmp/.cache && \
    chown -R ocruser:ocruser /app /tmp/.cache

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies using Aliyun pip mirror
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# Copy application code
COPY --chown=ocruser:ocruser app ./app
COPY --chown=ocruser:ocruser tests ./tests

# Switch to non-root user
USER ocruser

# Expose port
EXPOSE 8808

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8808/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8808"]
