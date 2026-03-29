FROM python:3.12-slim

LABEL maintainer="FUVA Team"
LABEL description="File Upload Validation Analyzer - Security testing tool"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p /app/data /app/logs /app/reports /app/exports

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/stats || exit 1

# Run the application
CMD ["python3", "web/main.py"]
