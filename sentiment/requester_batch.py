import csv
import requests
import time

# Define the input and output CSV file paths
input_csv = "..\code\WFTB33-13-TEC_20250509.csv"  # Replace with your input CSV file path
output_csv = "output_with_sentiment.csv"  # Output file path

# The API endpoint for the sentiment analysis
api_url = "http://localhost:8002/analyze_batch"  # Replace with your API URL for batch processing
BATCH_SIZE = 50

def process_csv(input_file, output_file):
    try:
        print("Starting CSV processing...")
        start_time = time.time()

        # Open the input CSV file
        with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if not reader.fieldnames:
                raise ValueError("Input file is invalid or missing headers.")
            print(f"Input file fieldnames: {reader.fieldnames}")

            # Prepare output CSV file
            fieldnames = reader.fieldnames + ["Sentiment", "Explanation"]
            with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                print("Header written successfully.")

                # Batch processing logic
                batch = []
                row_counter = 0

                for row in reader:
                    message = row.get("Message")
                    if not message:
                        print("Row missing 'Message' column. Skipping.")
                        continue
                    
                    # Add row and its message to the batch
                    batch.append((row, message))

                    # Process the batch if it reaches 10 rows
                    if len(batch) == 50:
                        process_batch(batch, writer)
                        batch = []  # Reset the batch
                    
                    row_counter += 1

                    if row_counter == 50:
                        break

                # Process any remaining rows in the batch
                if batch:
                    process_batch(batch, writer)

        # Stop the timer
        end_time = time.time()
        print(f"Processing complete. Output written to {output_file}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Failed to process CSV. Error: {str(e)}")

def process_batch(batch, writer):
    """
    Processes a batch of rows by sending them to the API and writing the results to the output CSV.
    """
    try:
        # Extract messages for the API request
        messages = [item[1] for item in batch]  # Extract the "Message" of each row

        # Send the batch to the API
        response = requests.post(api_url, json={"log_sentences": messages})
        if response.status_code == 200:
            # Parse API response
            results = response.json().get("results", [])
            for (row, _), result in zip(batch, results):
                row["Sentiment"] = result.get("sentiment", "Undefined")
                row["Explanation"] = result.get("explanation", "No explanation provided")
                writer.writerow(row)
            print(f"Processed and wrote {len(batch)} rows.")
        else:
            # Handle API errors
            print(f"API error: {response.status_code}, {response.text}")
            for row, _ in batch:
                row["Sentiment"] = "Error"
                row["Explanation"] = f"API error: {response.status_code}, {response.text}"
                writer.writerow(row)
    except Exception as e:
        # Handle exceptions during batch processing
        print(f"Exception while processing batch: {str(e)}")
        for row, _ in batch:
            row["Sentiment"] = "Error"
            row["Explanation"] = f"Exception: {str(e)}"
            writer.writerow(row)

# Run the function
process_csv(input_csv, output_csv)
