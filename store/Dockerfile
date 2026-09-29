# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./store/app ./app

# Note: tests are intentionally excluded via .dockerignore for production images
# For development with tests, mount ./store/tests as a volume or run tests outside Docker

# Copy alembic for database migrations
COPY ./store/alembic ./alembic
COPY ./store/alembic.ini .
COPY ./store/entrypoint.sh /usr/local/bin/store-api-entrypoint
RUN chmod +x /usr/local/bin/store-api-entrypoint

# Create data directory for documents
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

ENTRYPOINT ["store-api-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
