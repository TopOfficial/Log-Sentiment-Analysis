import pandas as pd
import requests
import time
import os
import csv

# Custom imports
from utils.logs_to_csv import transform_logs_to_csv
from utils.create_folders import create_folder_if_not_exists, get_output_subdirectory
from utils.process_logs import process_logs_folder

# API endpoint for sentiment analysis
api_url = "http://localhost:8002/analyze_batch"
BATCH_SIZE = 5
CHUNK_SIZE = 1000

def process_directory(input_dir, output_dir):
    """
    Processes all CSV files in a directory and its subdirectories.
    """
    try:
        print("Starting directory processing...")
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.csv'):
                    input_file_path = os.path.join(root, file)
                    output_subdir = get_output_subdirectory(input_dir, root, output_dir)
                    output_file_path = os.path.join(output_subdir, file)
                    print(f"Processing file: {input_file_path}")
                    print(f"Output will be saved to: {output_file_path}")
                    process_csv(input_file_path, output_file_path)
        print("Directory processing complete.")
    except Exception as e:
        print(f"Failed to process directory. Error: {str(e)}")

def process_csv(input_file, output_file):
    try:
        print(f"Processing CSV: {input_file}")
        start_time = time.time()

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Read the first chunk to get fieldnames
        df = pd.read_csv(input_file, nrows=1)
        if not df.columns.any():
            raise ValueError("Input file is invalid or missing headers.")
        print(f"Input file fieldnames: {df.columns.tolist()}")

        # Prepare output CSV fieldnames
        fieldnames = df.columns.tolist()
        if 'Predicted' not in fieldnames:
            fieldnames.append('Predicted')
        fieldnames.extend(["Sentiment", "Explanation"])

        # Check if output file exists to determine mode
        file_mode = 'a' if os.path.exists(output_file) else 'w'
        write_header = not os.path.exists(output_file)

        # Initialize output CSV
        with open(output_file, mode=file_mode, newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
                print("Header written successfully.")

            # Load full dataframe for Predicted column updates
            full_df = pd.read_csv(input_file)
            if 'Predicted' not in full_df.columns:
                print("Adding 'Predicted' column to input CSV...")
                full_df['Predicted'] = False
                full_df.to_csv(input_file, index=False)
                print("'Predicted' column added and initialized to False.")

            # Process CSV in chunks
            for chunk in pd.read_csv(input_file, chunksize=CHUNK_SIZE, encoding='utf-8'):
                # Filter unpredicted rows
                unpredicted_rows = chunk[chunk.get('Predicted', False) == False]
                if unpredicted_rows.empty:
                    print("No unpredicted rows in this chunk. Skipping.")
                    continue

                # Prepare batch for API processing
                batch = []
                for index, row in unpredicted_rows.iterrows():
                    message = row.get("Message")
                    if not message:
                        print(f"Row {index} missing 'Message' column. Skipping.")
                        continue
                    batch.append((row.to_dict(), message, index))

                    if len(batch) == BATCH_SIZE:
                        process_batch(batch, writer, outfile, full_df, input_file)
                        batch = []

                # Process remaining batch
                if batch:
                    process_batch(batch, writer, outfile, full_df, input_file)

        end_time = time.time()
        print(f"Processing complete. Output written to {output_file}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Failed to process CSV. Error: {str(e)}")

def process_batch(batch, writer, outfile, full_df, input_file):
    """
    Processes a batch of rows by sending them to the API, writing results to the output CSV,
    and updating the 'Predicted' column in the input CSV.

    :param batch: List of (row_dict, message, index) tuples to process.
    :param writer: csv.DictWriter object for writing to the output file.
    :param outfile: File object to flush after writing.
    :param full_df: Full DataFrame to update the Predicted column.
    :param input_file: Path to the input CSV file to save updates.
    """
    try:
        messages = [item[1] for item in batch]
        response = requests.post(api_url, json={"log_sentences": messages})
        if response.status_code == 200:
            results = response.json().get("results", [])
            for (row, _, index), result in zip(batch, results):
                row['Predicted'] = True
                row["Sentiment"] = result.get("sentiment", "Undefined")
                row["Explanation"] = result.get("explanation", "No explanation provided")
                writer.writerow(row)

                # Update Predicted column for this row
                full_df.at[index, 'Predicted'] = True
                # print(f"Updated Predicted to True for row {index}")

            outfile.flush()  # Flush after writing each row
            print('flushed')
            # Save updated DataFrame to input CSV
            full_df.to_csv(input_file, index=False)
            # print(f"Saved {len(batch)} Predicted updates to {input_file}")
        else:
            print(f"API error: {response.status_code}, {response.text}")
            for (row, _, index), _ in zip(batch, results):
                row["Sentiment"] = "Error"
                row["Explanation"] = f"API error: {response.status_code}, {response.text}"
                writer.writerow(row)
                outfile.flush()  # Flush after writing each row
                # Update Predicted column for this row
                full_df.at[index, 'Predicted'] = True
                print(f"Updated Predicted to True for row {index} after API error")
            # Save updated DataFrame to input CSV
            full_df.to_csv(input_file, index=False)
            print(f"Saved {len(batch)} Predicted updates to {input_file} after API error")
    except Exception as e:
        print(f"Exception while processing batch: {str(e)}")
        for (row, _, index), _ in zip(batch, results):
            row["Sentiment"] = "Error"
            row["Explanation"] = f"Exception: {str(e)}"
            writer.writerow(row)
            outfile.flush()  # Flush after writing each row
            # Update Predicted column for this row
            full_df.at[index, 'Predicted'] = True
            print(f"Updated Predicted to True for row {index} after exception")
        # Save updated DataFrame to input CSV
        full_df.to_csv(input_file, index=False)
        print(f"Saved {len(batch)} Predicted updates to {input_file} after exception")

# Run the functions
logs_directory = "../logs"
input_directory = "../transformed_logs"
output_directory = "../sentiment_results"

create_folder_if_not_exists(logs_directory)
create_folder_if_not_exists(input_directory)
create_folder_if_not_exists(output_directory)

process_logs_folder(logs_directory, input_directory)
process_directory(input_directory, output_directory)