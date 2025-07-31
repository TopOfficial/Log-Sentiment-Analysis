# Use official Python runtime as base image
FROM python:3.10.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 8001
EXPOSE 8001

# Copy wait script
COPY wait-for-ollama.sh /app/wait-for-ollama.sh
RUN chmod +x /app/wait-for-ollama.sh

# Start the app using the script
CMD ["/app/wait-for-ollama.sh"]