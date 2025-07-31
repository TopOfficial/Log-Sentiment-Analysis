import csv
import requests
import time

# Define the input and output CSV file paths
input_csv = "code\\WFTB33-13-TEC_20250509.csv"  # Replace with your input CSV file path
output_csv = "output_with_sentiment.csv"  # Output file path

# The API endpoint for the sentiment analysis
api_url = "http://localhost:8000/analyze"  # Replace with your API URL

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
                
                # Initialize row counter
                row_counter = 0

                # Iterate through each row in the input CSV
                for row in reader:
                    # print(f"Processing row: {row}")
                    message = row.get("Message")
                    if not message:
                        print("Row missing 'Message' column. Skipping.")
                        continue
                    try:
                        # Call the API with the log sentence
                        response = requests.post(api_url, json={"log_sentence": message})
                        # print(f"API response: {response.status_code}, {response.text}")
                        if response.status_code == 200:
                            result = response.json()
                            row["Sentiment"] = result.get("sentiment", "Undefined")
                            row["Explanation"] = result.get("explanation", "No explanation provided")
                        else:
                            row["Sentiment"] = "Error"
                            row["Explanation"] = f"API error: {response.status_code}, {response.text}"
                    except Exception as e:
                        row["Sentiment"] = "Error"
                        row["Explanation"] = f"Exception: {str(e)}"
                    
                    # Write the updated row to the output file
                    writer.writerow(row)
                    row_counter += 1
                    # print(f"Row written successfully: {row}")

                    # Flush after every 5 rows
                    if row_counter % 50 == 0:
                        outfile.flush()
                        print(f"Flushed output file after {row_counter} rows.")

                    if row_counter == 50:
                        break
        
        # Stop the timer
        end_time = time.time()
        print(f"Processing complete. Output written to {output_file}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Failed to process CSV. Error: {str(e)}")

# Run the function
process_csv(input_csv, output_csv)
