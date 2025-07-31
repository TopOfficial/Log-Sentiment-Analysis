# Use official Python runtime as base image
FROM python:3.10.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including apt-utils
RUN apt-get update && apt-get install -y \
    apt-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the application with environment variables
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level ${LOG_LEVEL:-info}"]