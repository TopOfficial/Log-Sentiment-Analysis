# Use an official Python runtime as a parent image
FROM python:3.10.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including curl
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8002

# Copy wait script
COPY wait-for-ollama.sh /app/wait-for-ollama.sh
RUN chmod +x /app/wait-for-ollama.sh

# Command to run the application
CMD ["/app/wait-for-ollama.sh"]