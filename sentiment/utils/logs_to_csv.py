import csv
import re
import os  # Add this import to check if the CSV file exists


def transform_logs_to_csv(log_file, csv_file):
    """
    Transforms a structured log file into a CSV file if the CSV does not already exist.
    
    :param log_file: Path to the log file.
    :param csv_file: Path to save the transformed CSV file.
    """
    try:
        # Check if the CSV file already exists
        if os.path.exists(csv_file):
            print(f"CSV file already exists: {csv_file}. Skipping transformation.")
            return  # Skip processing if the CSV already exists

        print(f"Transforming log file: {log_file} to CSV: {csv_file}")

        # Regular expression to identify a line starting with a timestamp
        timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}/\d{2}:\d{2}:\d{2}\.\d{3}")

        # Open the log file and the output CSV file
        with open(log_file, 'r') as infile, open(csv_file, 'w', newline='') as outfile:
            # Define the CSV writer
            csv_writer = csv.writer(outfile)

            # Define the headers
            headers = ["Timestamp", "lot_id", "log_level", "Category", "Source", "ID", "Message"]
            
            # Write headers to the CSV
            csv_writer.writerow(headers)

            # Variables to hold the current log entry being processed
            current_entry = None

            # Read the log file line by line
            for line in infile:
                # Check if the line starts with a timestamp
                if re.match(timestamp_pattern, line):
                    # If a new timestamp is found, write the previous entry to the CSV
                    if current_entry:
                        csv_writer.writerow(current_entry)

                    # Parse the new log entry
                    parts = line.split(maxsplit=5)
                    if len(parts) >= 6:
                        timestamp = parts[0]
                        lot_id = parts[1]
                        log_level = parts[2]
                        category = parts[3]
                        source = parts[4]
                        message_id_and_message = parts[5].strip()

                        # Split message_id_and_message further into ID and Message
                        if ' ' in message_id_and_message:
                            message_id, message = message_id_and_message.split(maxsplit=1)
                        else:
                            message_id = message_id_and_message
                            message = ""

                        # Initialize current entry with parsed values
                        current_entry = [timestamp, lot_id, log_level, category, source, message_id, message]
                    else:
                        current_entry = None
                else:
                    # If no timestamp, append line content to the current entry's message field
                    if current_entry:
                        current_entry[-1] += f" {line.strip()}"

            # Write the last entry to the CSV (if any)
            if current_entry:
                csv_writer.writerow(current_entry)

        print(f"Log file transformed successfully: {csv_file}")
    except Exception as e:
        print(f"Failed to transform log file. Error: {str(e)}")
