#!/bin/sh
set -e

# Wait for Ollama to be ready
until curl --silent http://ollama:11434/api/tags > /dev/null
do
  echo "Waiting for Ollama..."
  sleep 2
done

# Pull model if needed
echo "Pulling model: llama3.2:3b-instruct-q8_0"
curl -X POST http://ollama:11434/api/pull -d '{"name":"llama3.2:3b-instruct-q8_0"}'

# Start the app
echo "Starting LLM service..."
exec uvicorn llm_rag_api:app --host 0.0.0.0 --port 8001