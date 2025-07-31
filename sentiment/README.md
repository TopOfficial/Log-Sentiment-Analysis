# Sentiment Analysis API for Wafer Testing Logs

This project is a FastAPI-based sentiment analysis system designed to classify log sentences from the Wafer Testing process as negative (-1), neutral (0), or positive (1). It uses LangChain for prompt engineering, Ollama for local LLM inference, and structured output parsing for consistent responses.

## **Important**
1. Frequent log lines that are seen a lot should be added in the filter function to check before letting the LLM analyze.
    - Can be automated.
2. Currently the performance is still undesirable, but doing the `1.` should help improve the performance, having better GPU and optimizing the pipeline is recommended.

## Features

- Sentiment analysis of individual or batched log sentences
- Chain-of-thought reasoning for transparent sentiment classification
- Structured JSON output with sentiment scores and explanations
- Stateless API with clear error handling
- Local LLM for privacy and performance

## Installation

1. **Install uv package manager** (https://github.com/astral-sh/uv)
   ```bash
   pip install uv
   ```

2. **Clone this repository**
   ```bash
   git clone <repository_url>
   cd <repository_directory>/sentiment
   ```

3. **Set up the environment**

   Create a `.env` file in the project directory with the following:
   ```plaintext
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=your_langsmith_key
   LANGCHAIN_PROJECT=your_project_name
   ```
   - Obtain a LangSmith API key from [LangSmith](https://docs.smith.langchain.com/administration/how_to_guides/organization_management/create_account_api_key).

### First-Time Setup

1. **Install Ollama**
   - **Windows**: Download and install from [Ollama Windows](https://ollama.com/download/windows).
   - **Linux**:
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ```

2. **Download the LLM model**
   ```bash
   ollama run llama3.2:3b-instruct-q8_0
   ```

3. **Create a virtual environment in the sentiment folder**
   ```bash
   uv venv
   ```

4. **Activate the virtual environment**
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```

5. **Install dependencies**
   ```bash
   uv sync
   ```
   Alternatively:
   ```bash
   uv pip install -r requirements.txt
   ```

### Subsequent Runs (Finished First-Time Setup)

1. **Activate the virtual environment in the sentiment folder**
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```

# Usage (Everything should be run under "sentiment" folder except database which needs to be run in 'backend' folder)

## First method: Automatically pull data from database and do sentiment analysis

- **Need to run database api first**

1. Run the API in venv environment

```bash
uvicorn llm_sentiment_api:app --reload --port 8002
```

- or run outside venv

```bash
uv run uvicorn llm_sentiment_api:app --reload --port 8002
```

2. Run the main script to use Sentiment Analysis in venv environment.

```bash
python main_db.py
```
- or run outside venv

```bash
uv run python main_db.py
```

## Second Method: Local logs

1. Run the API in venv environment

```bash
uvicorn llm_sentiment_api:app --reload --port 8002
```

- or run outside venv

```bash
uv run uvicorn llm_sentiment_api:app --reload --port 8002
```

2. Run the main script to use Sentiment Analysis in venv environment.

```bash
python main.py
```
- or run outside venv

```bash
uv run python main.py
```

The API will be available at `http://localhost:8002`. Visit `http://localhost:8002/docs` for interactive API documentation.

## API Endpoints

| **Endpoint**          | **Method** | **Description**                                                                 | **Request Body**                                                                 | **Response**                                                                 |
|-----------------------|------------|--------------------------------------------------------------------------------|----------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `/`                   | `GET`      | Welcome endpoint to verify the API is running.                                  | None                                                                             | `{"message": "Welcome to the Sentiment Analysis API! Visit /docs for API documentation."}` |
| `/analyze`            | `POST`     | Analyzes the sentiment of a single log sentence.                                | `{"log_sentences": ["<log_sentence>"]}`                                          | `{"sentiment": <int>, "explanation": "<reasoning>"}`                            |
| `/analyze_batch`      | `POST`     | Analyzes the sentiment of multiple log sentences individually.                  | `{"log_sentences": ["<sentence1>", "<sentence2>", ...]}`                         | `{"results": [{"sentiment": <int>, "explanation": "<reasoning>"}, ...]}`        |
| `/analyze_batch_full` | `POST`     | Analyzes a batch of log sentences as a single combined prompt (experimental).   | `{"log_sentences": ["<sentence1>", "<sentence2>", ...]}`                         | `{"results": [{"sentiment": <int>, "explanation": "<reasoning>"}, ...]}`        |

### Example Request (Single Analysis)

```bash
curl -X POST "http://localhost:8002/analyze" -H "Content-Type: application/json" -d '{"log_sentences": ["Error occurred while processing the wafer."]}'
```

**Response**:
```json
{
  "sentiment": -1,
  "explanation": "Negative check: 'Error' indicates a failure., Neutral check: Not applicable because the sentence is negative., Positive check: Not applicable because the sentence is negative."
}
```

### Example Request (Batch Analysis)

```bash
curl -X POST "http://localhost:8002/analyze_batch" -H "Content-Type: application/json" -d '{"log_sentences": ["Error occurred while processing the wafer.", "TestCompletes: 494."]}'
```

**Response**:
```json
{
  "results": [
    {
      "sentiment": -1,
      "explanation": "Negative check: 'Error' indicates a failure., Neutral check: Not applicable because the sentence is negative., Positive check: Not applicable because the sentence is negative."
    },
    {
      "sentiment": 1,
      "explanation": "Negative check: No negative keywords found., Neutral check: Not purely descriptive; implies success or completion., Positive check: 'TestCompletes' suggests progress or completion."
    }
  ]
}
```

## How It Works (Simplified)

### Lifespan Initialization

During application startup:
- `.env` variables are loaded.
- The LLM is initialized via Ollama.
- A prompt template with chain-of-thought reasoning is cached for sentiment analysis.
- A structured output parser ensures consistent JSON responses.

### Sentiment Analysis Process

1. **Input**: Receives a log sentence or a list of log sentences.
2. **Prompt Generation**: Uses a chain-of-thought prompt to analyze the sentence(s) for negative, neutral, or positive sentiment based on predefined rules.
3. **Filtering**: Check the log sentences if it exist in the known list, return result early if so.
4. **LLM Inference**: Queries the local LLM to classify the sentiment and generate reasoning.
5. **Output Parsing**: Parses the LLM response into a structured JSON format with sentiment (-1, 0, or 1) and an explanation.
6. **Response**: Returns the sentiment classification and reasoning to the client.

### Sentiment Rules

- **Negative (-1)**: Keywords like "fail," "error," or "incomplete" indicate problems.
- **Neutral (0)**: Descriptive or ambiguous sentences without evaluative context (e.g., "YIELD MONITORING FOR TESTCOMPLETE").
- **Positive (1)**: Keywords like "completed," "success," or "TestCompletes" indicate progress or success.

## Function Overview

| **Function**                        | **Description**                                                                 | **Input**                     | **Output**                          |
|-------------------------------------|--------------------------------------------------------------------------------|-------------------------------|-------------------------------------|
| `load_dotenv()`                     | Loads environment variables from a `.env` file.                                | -                             | Sets environment variables          |
| `init_chat_model()`                 | Initializes the LLM (Llama3.2:3b-instruct-q8_0) via Ollama.                    | Model name, provider, config  | LLM instance                        |
| `SentimentPromptCache.get_prompt()` | Caches and returns the prompt template, format instructions, and parser.       | -                             | PromptTemplate, instructions, parser |
| `query_sentiment()`                 | Queries the LLM with a log sentence and prompt template.                       | Query, format instructions    | Raw LLM response (string)           |
| `get_result()`                      | Parses the LLM response into a structured JSON format.                         | Raw response                  | Parsed JSON object                  |

## Tech Stack

- **FastAPI**: Web server for API endpoints
- **LangChain**: Prompt engineering and structured output parsing
- **Ollama**: Local LLM provider (Llama3.2:3b-instruct-q8_0)
- **Pydantic**: Data validation and request/response schemas
- **Python-dotenv**: Environment variable management

## Notes

- **Ollama**: The LLM stops automatically after 5 minutes of inactivity but restarts upon querying.
- **Batch Processing**: The `/analyze_batch` endpoint processes each sentence individually, while `/analyze_batch_full` combines sentences into a single prompt (experimental, may be less reliable).
- **Error Handling**: The API includes robust error handling for LLM failures, parsing errors, and invalid inputs.
- **Virtual Environment**: Run commands within the activated virtual environment (`venv`) or use `uv run` for convenience.
- **Scalability**: For production, consider replacing the in-memory prompt cache with a persistent store and adding rate limiting.

## Example Output Schema

```json
{
  "sentiment": -1,
  "explanation": "Negative check: 'Error' indicates a failure., Neutral check: Not applicable because the sentence is negative., Positive check: Not applicable because the sentence is negative."
}
```

For batch processing:
```json
{
  "results": [
    {
      "sentiment": 0,
      "explanation": "Negative check: No negative keywords found., Neutral check: Descriptive sentence reporting an activity without evaluative context., Positive check: Not applicable because the sentence fits the neutral category."
    },
    ...
  ]
}
```