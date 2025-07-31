from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
import time
from typing import List

# Import the existing logic
from dotenv import load_dotenv
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import PromptTemplate
import os

# Load environment variables
load_dotenv()
os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

# Initialize the FastAPI app
app = FastAPI()

# Example LLM initialization (replace with your actual setup)
llm = init_chat_model("llama3.2:3b-instruct-q8_0", model_provider="ollama", temperature=0)

# Define input and output schemas
# class QueryInput(BaseModel):
#     log_sentence: str  # Input log sentence for analysis

# Define input and output schemas
class QueryInput(BaseModel):
    log_sentences: List[str]  # List of input log sentences for analysis

class SentimentResponse(BaseModel):
    sentiment: int  # Sentiment result (-1, 0, 1)
    explanation: str  # Optional explanation (for debugging or verbose output)

class BatchSentimentResponse(BaseModel):
    results: List[SentimentResponse]  # List of sentiment results for batch processing

# Define the logic for the structured output prompt
class SentimentPromptCache:
    def __init__(self):
        self.prompt_template = None
        self.format_instructions = None
        self.parser = None
    
    def get_prompt(self):
        if not self.prompt_template or not self.format_instructions:
            # Generate the prompt template and format instructions only once
            response_schemas = [
                ResponseSchema(name="log_sentence", description="The original log sentence."),
                ResponseSchema(name="negative_check", description="Step 1: Explanation of why the sentence fits or does not fit the negative sentiment category."),
                ResponseSchema(name="neutral_check", description="Step 2: Explanation of why the sentence fits or does not fit the neutral sentiment category."),
                ResponseSchema(name="positive_check", description="Step 3: Explanation of why the sentence fits or does not fit the positive sentiment category."),
                ResponseSchema(name="sentiment", description="The final sentiment classification as a single number (-1 for negative, 0 for neutral, 1 for positive)."),
            ]

            # response_schemas = [
            #     ResponseSchema(name="log_sentence", description="The original log sentence."),
            #     ResponseSchema(name="sentiment", description="The final sentiment classification as a single number (-1 for negative, 0 for neutral, 1 for positive)."),
            # ]

            self.parser = StructuredOutputParser.from_response_schemas(response_schemas)
            self.format_instructions = self.parser.get_format_instructions()
            
            template_cot = """You are tasked with performing sentiment analysis on individual log sentences from an application log in the Wafer Testing process. Follow the rules below to analyze the sentiment of each sentence and respond in a structured JSON format.

            Sentiment Analysis Rules:
            1. Negative Check (Step 1):
            - Look for keywords that indicate problems, failures, or errors (e.g., "fail," "error," "incomplete," "bad").
            - If such keywords exist, classify the sentiment as negative (-1) and provide reasoning for this classification.
            - If not applicable, proceed to Neutral Check.

            2. Neutral Check (Step 2):
            - If no negative sentiment is detected, check if the sentence is purely descriptive, informational, or lacks evaluative context (e.g., "YIELD MONITORING FOR TESTCOMPLETE (touchdown 512)").
            - If descriptive or ambiguous, classify the sentiment as neutral (0) and provide reasoning for this classification.
            - If not applicable, proceed to Positive Check.

            3. Positive Check (Step 3):
            - If neither negative nor neutral applies, look for keywords indicating progress, success, or completion (e.g., "completed," "success," "done," "finish," "TestCompletes").
            - If such keywords exist, classify the sentiment as positive (1) and provide reasoning for this classification.

            4. Output Format:
            - Provide the response as a JSON object in the following format:
            {format_instructions}

            ---

            Example Analysis:
            Log Sentence: "Error occurred while processing the wafer."
            Step 1 (Negative Check): 'Error' indicates a failure.
            Step 2 (Neutral Check): Not applicable because the sentence is negative.
            Step 3 (Positive Check): Not applicable because the sentence is negative.
            Final Sentiment: -1

            Log Sentence: "YIELD MONITORING FOR TESTCOMPLETE (touchdown 512)."
            Step 1 (Negative Check): No negative keywords found.
            Step 2 (Neutral Check): Descriptive sentence reporting an activity without evaluative context.
            Step 3 (Positive Check): Not applicable because the sentence fits the neutral category.
            Final Sentiment: 0

            Log Sentence: "TestCompletes: 494."
            Step 1 (Negative Check): No negative keywords found.
            Step 2 (Neutral Check): Not purely descriptive; implies success or completion.
            Step 3 (Positive Check): 'TestCompletes' suggests progress or completion.
            Final Sentiment: 1

            Log Sentence: "---> TC: event catched"
            Step 1 (Negative Check): No negative keywords found.
            Step 2 (Neutral Check): Descriptive sentence reporting an activity without evaluative context.
            Step 3 (Positive Check): Not applicable because the sentence fits the neutral category.
            Final Sentiment: 0

            ---

            Analyze the following log sentence and respond in the required JSON format:
            Log Sentence: {question} """

            # template_short_cot = """You are tasked with performing sentiment analysis on individual log sentences from the Wafer Testing process. Follow these rules to classify the sentiment and respond in JSON format:

            # Negative (-1): Check for keywords indicating problems or failures (e.g., "fail," "error"). If found, classify as negative and provide reasoning. Otherwise, proceed to Neutral.

            # Neutral (0): If no negative sentiment applies, check if the sentence is purely descriptive or ambiguous (e.g., "YIELD MONITORING FOR TESTCOMPLETE"). If so, classify as neutral with reasoning. Otherwise, proceed to Positive.

            # Positive (1): If neither negative nor neutral applies, check for keywords indicating success or progress (e.g., "completed," "success"). If found, classify as positive with reasoning.

            # Output Format:
            # - Provide the response as a JSON object in the following format:
            # {format_instructions}

            # ----
            # Example Analysis:
            # Log Sentence: "Error occurred while processing the wafer."
            # Negative Check: 'Error' indicates failure.
            # Neutral Check: Not applicable, as the sentence is negative.
            # Positive Check: Not applicable, as the sentence is negative.
            # Final Sentiment: -1  

            # Analyze the following log sentence and respond in JSON format:
            # Log Sentence: {question} 
            # """

            # template = """You are tasked with performing sentiment analysis on individual log sentences from an application log in the Wafer Testing process. Use the following rules to classify the sentiment as negative (-1), neutral (0), or positive (1).

            # 1. Negative (-1): Classify as negative if the sentence contains keywords indicating problems or failures (e.g., "fail," "error," "incomplete"). Provide reasoning for why it's negative.
            # 2. Neutral (0): Classify as neutral if the sentence is purely descriptive, informational, or lacks evaluative context. Provide reasoning for why it's neutral.
            # 3. Positive (1): Classify as positive if the sentence contains keywords indicating progress, success, or completion (e.g., "completed," "success," "done"). Provide reasoning for why it's positive.

            # Respond with the sentiment classification in JSON format:
            # {format_instructions}

            # Analyze the following log sentence and respond: {question}"""

            self.prompt_template = PromptTemplate.from_template(template_cot)
        
        return self.prompt_template, self.format_instructions, self.parser

# Initialize the cache object
prompt_cache = SentimentPromptCache()

# Usage
prompt_template, format_instructions, parser = prompt_cache.get_prompt()

def query_sentiment(query, FORMAT=format_instructions):
    try:
        # Generate the prompt and query the LLM
        generated_prompt = prompt_template.invoke({'question': query, 'format_instructions': FORMAT})
        response = llm.invoke(generated_prompt)
        return response.content  # Return raw LLM response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # Handle LLM errors

def get_result(response):
    try:
        # Parse the structured response
        parsed_response = parser.parse(response)
        return parsed_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # Handle parsing errors
    
def preprocess_sentiment(log_sentence: str):
    """
    Preprocess the log sentence to classify its sentiment using exact sentence matches.
    If the sentiment cannot be classified, return None for LLM processing.
    """
    # Define exact sentence matches for each sentiment
    negative_sentences = {
        "error occurred while processing the wafer",
        "failed to complete the testing process",
        "wafer test incomplete",
        "test aborted due to missing data",
        "bad result observed in the test"
    }

    positive_sentences = {
        "test completed successfully",
        "process finished with no errors",
        "all wafers passed the quality tests",
        "successfully completed wafer testing",
        "TestCompletes successfully"
    }

    neutral_sentences = {
        "yield monitoring for touchdown 512",
        "descriptive report generated for the wafer",
        "monitoring process initiated",
        "report created for the test batch",
        "system is in descriptive mode"
    }
    
    # Normalize the input sentence (case insensitive comparison)
    normalized_sentence = log_sentence.strip().lower()

    # Check for exact matches in negative sentences
    if normalized_sentence in negative_sentences:
        return {
            "sentiment": -1,
            "explanation": f"The sentence matches a predefined negative sentence: '{normalized_sentence}'."
        }

    # Check for exact matches in positive sentences
    elif normalized_sentence in positive_sentences:
        return {
            "sentiment": 1,
            "explanation": f"The sentence matches a predefined positive sentence: '{normalized_sentence}'."
        }

    # Check for exact matches in neutral sentences
    elif normalized_sentence in neutral_sentences:
        return {
            "sentiment": 0,
            "explanation": f"The sentence matches a predefined neutral sentence: '{normalized_sentence}'."
        }

    # If no exact match is found, return None
    return None

@app.get("/")
async def root():
    return {"message": "Welcome to the Sentiment Analysis API! Visit /docs for API documentation."}

# Define the FastAPI endpoint
@app.post("/analyze", response_model=SentimentResponse)
async def analyze_log_sentence(input_query: QueryInput):
    """
    Perform sentiment analysis on the given log sentence.
    """
    try:

        # start_time = time.time()

        # Extract the log sentence from the input
        log_sentence = input_query.log_sentence

        # Query the sentiment analysis model
        response = query_sentiment(log_sentence)

        # Parse and extract the result
        parsed_response = get_result(response)

        # end_time = time.time()

        # elapsed_time = end_time - start_time
        # print(f"Elapsed time: {elapsed_time:.4f} seconds")
        # Preprocess the log sentence
        preprocessed_result = preprocess_sentiment(log_sentence)
        if preprocessed_result:
            # If preprocessing classifies the sentiment, return it directly
            return SentimentResponse(
                sentiment=preprocessed_result["sentiment"],
                explanation=preprocessed_result["explanation"]
            )

        # Return the result as a structured API response
        return SentimentResponse(
            sentiment=parsed_response["sentiment"],
            explanation=f"Negative check: {parsed_response['negative_check']}, "
                        f"Neutral check: {parsed_response['neutral_check']}, "
                        f"Positive check: {parsed_response['positive_check']}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing log sentence: {str(e)}")

# Batch processing logic
@app.post("/analyze_batch", response_model=BatchSentimentResponse)
async def analyze_log_sentences(input_query: QueryInput):
    """
    Perform sentiment analysis on a batch of log sentences individually.
    """
    try:
        log_sentences = input_query.log_sentences
        # if len(log_sentences) > 10:
        #     raise HTTPException(status_code=400, detail="Batch size should not exceed 10 sentences.")

        # Initialize the results list
        results = []

        for log_sentence in log_sentences:
            # Preprocess each log sentence
            preprocessed_result = preprocess_sentiment(log_sentence)
            if preprocessed_result:
                # If preprocessing classifies the sentiment, append it directly
                results.append(SentimentResponse(
                    sentiment=preprocessed_result["sentiment"],
                    explanation=preprocessed_result["explanation"]
                ))
            else:
                # If preprocessing cannot classify, query the LLM
                response = query_sentiment(log_sentence)
                parsed_response = get_result(response)
                results.append(SentimentResponse(
                    sentiment=parsed_response["sentiment"],
                    explanation=f"Negative check: {parsed_response['negative_check']}, "
                                f"Neutral check: {parsed_response['neutral_check']}, "
                                f"Positive check: {parsed_response['positive_check']}"
                ))

        return BatchSentimentResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing log sentences: {str(e)}")

# @app.post("/analyze_batch_full", response_model=BatchSentimentResponse)
# async def analyze_log_sentences(input_query: QueryInput):
#     """
#     Perform sentiment analysis on a batch of log sentences.
#     """
#     try:
#         log_sentences = input_query.log_sentences

#         # Limit batch size
#         # if len(log_sentences) > 10:
#         #     raise HTTPException(status_code=400, detail="Batch size should not exceed 10 sentences.")

#         # Step 1: Combine log sentences into a single prompt
#         combined_prompt = "\n".join([f"Log Sentence {i+1}: {sentence}" for i, sentence in enumerate(log_sentences)])

#         # Step 2: Query the LLM with the combined prompt
#         try:
#             response = query_sentiment(combined_prompt)  # query_sentiment now returns a plain string
#         except Exception as query_error:
#             raise HTTPException(status_code=500, detail=f"Error querying the LLM: {str(query_error)}")

#         # Step 3: Parse the structured response from the LLM
#         try:
#             parsed_responses = parser.parse(response)  # Directly parse the string response
#             if not isinstance(parsed_responses, list):
#                 raise ValueError("Parsed response is not in the expected list format.")
#         except Exception as parse_error:
#             raise HTTPException(status_code=500, detail=f"Error parsing LLM response: {str(parse_error)}")

#         # Step 4: Process each parsed response
#         results = []
#         for parsed_response in parsed_responses:
#             results.append(SentimentResponse(
#                 sentiment=parsed_response["sentiment"],
#                 explanation=f"Negative check: {parsed_response['negative_check']}, "
#                             f"Neutral check: {parsed_response['neutral_check']}, "
#                             f"Positive check: {parsed_response['positive_check']}"
#             ))

#         # Step 5: Return all results
#         return BatchSentimentResponse(results=results)

#     except HTTPException as e:
#         raise e  # Re-raise HTTP exceptions to propagate error codes properly
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
