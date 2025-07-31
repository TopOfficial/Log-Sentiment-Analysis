from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()
os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

# Example LLM initialization (replace with your actual setup)
llm = init_chat_model("llama3.2:3b-instruct-q8_0", model_provider="ollama", temperature=0)

# Define input and output schemas
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

            Analyze the following log sentence and respond in the required JSON format:
            Log Sentence: {question} """

            self.prompt_template = PromptTemplate.from_template(template_cot)
        
        return self.prompt_template, self.format_instructions, self.parser

# Initialize the cache object
prompt_cache = SentimentPromptCache()
prompt_template, format_instructions, parser = prompt_cache.get_prompt()

def query_sentiment(query, FORMAT=format_instructions):
    try:
        # Generate the prompt and query the LLM
        generated_prompt = prompt_template.invoke({'question': query, 'format_instructions': FORMAT})
        response = llm.invoke(generated_prompt)
        return response.content  # Return raw LLM response
    except Exception as e:
        raise Exception(f"Error querying the LLM: {str(e)}")

def get_result(response):
    try:
        # Parse the structured response
        parsed_response = parser.parse(response)
        return parsed_response
    except Exception as e:
        raise Exception(f"Error parsing LLM response: {str(e)}")
    
def preprocess_sentiment(log_sentence: str):
    """
    Preprocess the log sentence to classify its sentiment using exact sentence matches.
    If the sentiment cannot be classified, return None for LLM processing.
    """
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
    
    normalized_sentence = log_sentence.strip().lower()

    if normalized_sentence in negative_sentences:
        return {
            "sentiment": -1,
            "explanation": f"The sentence matches a predefined negative sentence: '{normalized_sentence}'."
        }

    elif normalized_sentence in positive_sentences:
        return {
            "sentiment": 1,
            "explanation": f"The sentence matches a predefined positive sentence: '{normalized_sentence}'."
        }

    elif normalized_sentence in neutral_sentences:
        return {
            "sentiment": 0,
            "explanation": f"The sentence matches a predefined neutral sentence: '{normalized_sentence}'."
        }

    return None

def analyze_batch(log_sentences: List[str]):
    """
    Perform sentiment analysis on a batch of log sentences individually.
    """
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
    return results

# def analyze_full_batch(log_sentences: List[str]):
#     """
#     Perform sentiment analysis on a batch of log sentences combined into a single input.
#     """
#     # Combine log sentences into a single prompt
#     combined_prompt = "\n".join([f"Log Sentence {i+1}: {sentence}" for i, sentence in enumerate(log_sentences)])
#     print(combined_prompt)

#     # Query the LLM with the combined prompt
#     response = query_sentiment(combined_prompt)
#     print(response)

#     # Parse the structured response from the LLM
#     parsed_responses = parser.parse(response)

#     # Process each parsed response
#     results = []
#     for parsed_response in parsed_responses:
#         results.append(SentimentResponse(
#             sentiment=parsed_response["sentiment"],
#             explanation=f"Negative check: {parsed_response['negative_check']}, "
#                         f"Neutral check: {parsed_response['neutral_check']}, "
#                         f"Positive check: {parsed_response['positive_check']}"
#         ))

#     return results

# Main function for testing
def main():
    print("Welcome to the Sentiment Analysis Tool!")
    while True:
        mode = input("\nChoose mode (single / batch or type 'exit' to quit): ").strip().lower()
        if mode == 'exit':
            print("Exiting the tool. Goodbye!")
            break
        elif mode not in {'single', 'batch'}:
            print("Invalid mode! Please choose 'single' or 'batch'.")
            continue

        if mode == 'single':
            log_sentence = input("Enter a log sentence: ").strip()
            result = preprocess_sentiment(log_sentence)
            if result:
                print(f"Result: Sentiment = {result['sentiment']}, Explanation = {result['explanation']}")
            else:
                response = query_sentiment(log_sentence)
                parsed_response = get_result(response)
                print(f"Result: Sentiment = {parsed_response['sentiment']}")
                print(f"Explanation: Negative check = {parsed_response['negative_check']}, "
                      f"Neutral check = {parsed_response['neutral_check']}, "
                      f"Positive check = {parsed_response['positive_check']}")
        elif mode == 'batch':
            log_sentences = input("Enter log sentences separated by '|' (e.g., sentence1|sentence2|sentence3): ").strip().split('|')
            results = analyze_batch(log_sentences)
            for i, result in enumerate(results, 1):
                print(f"Sentence {i}: Sentiment = {result.sentiment}, Explanation = {result.explanation}")
        # elif mode == 'full_batch':
        #     log_sentences = input("Enter log sentences separated by '|' (e.g., sentence1|sentence2|sentence3): ").strip().split('|')
        #     results = analyze_full_batch(log_sentences)
        #     for i, result in enumerate(results, 1):
        #         print(f"Sentence {i}: Sentiment = {result.sentiment}, Explanation = {result.explanation}")

if __name__ == "__main__":
    main()
