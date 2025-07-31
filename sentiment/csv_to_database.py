import csv
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# File paths
input_csv = 'sentiment/example_logs/output.csv'
output_csv = 'sentiment/example_logs/cleaned_output.csv'
duplicates_log = 'sentiment/example_logs/duplicates.csv'

# MySQL database configuration from .env
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Step 1: Parse CSV and filter all duplicates, keeping only the first occurrence with fixed MachineId = 4
def parse_and_filter_logs(input_csv, output_csv, duplicates_log):
    unique_rows = []
    duplicates = []
    seen_contents = {}  # Tracks the first occurrence of each LogContent

    try:
        # Read the CSV file
        with open(input_csv, 'r', encoding='utf-8') as csv_file:
            print("Reading CSV file...")  # Debug
            reader = csv.reader(csv_file)
            header = next(reader, None)  # Skip header and store it
            print(f"Header: {header}")  # Debug: Print header
            for idx, row in enumerate(reader):
                print(f"Row {idx} raw: {row}")  # Debug: Print raw row
                if not row:
                    print(f"Skipping empty row {idx}")  # Debug
                    continue

                # Handle different input formats
                if len(row) == 1 and row[0].startswith('['):  # Raw log line format
                    log_line = row[0].strip()
                    timestamp_str = log_line[1:18]  # Extract [DD/MM/YY HH:MM:SS]
                    content = log_line[19:].strip()  # Extract content
                    date_obj = datetime.strptime(timestamp_str, '%d/%m/%y %H:%M:%S')
                    date_created = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                elif len(row) == 2:  # DateCreated, LogContent format
                    date_created, content = row[0], row[1]
                else:
                    print(f"Skipping row {idx} due to invalid format: {row}")  # Debug
                    continue

                # Fixed MachineId = 4
                machine_id = '4'
                row_data = [machine_id, date_created, content]

                # Check if this LogContent has been seen before
                if content in seen_contents:
                    duplicates.append((idx, row_data))
                    print(f"Skipping duplicate at row {idx}: {content}")  # Debug
                    continue  # Skip duplicate

                # Store the first occurrence
                seen_contents[content] = row_data
                unique_rows.append(row_data)
                print(f"Added unique row {idx}: {content}")  # Debug

        # Write unique rows to a new CSV
        with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL, escapechar='\\')
            writer.writerow(['MachineId', 'DateCreated', 'LogContent'])  # Write header
            writer.writerows(unique_rows)

        # Log duplicates to a separate file
        if duplicates:
            with open(duplicates_log, 'w', encoding='utf-8') as log_file:
                log_file.write("Duplicate rows skipped:\n")
                for idx, dup in duplicates:
                    log_file.write(f"Row {idx}: {dup}\n")

        print(f"Processed {len(unique_rows)} unique rows. Skipped {len(duplicates)} duplicates.")
        return unique_rows

    except FileNotFoundError:
        print(f"Error: Input CSV file '{input_csv}' not found.")
        return []
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return []

# Step 2: Insert unique rows into MySQL database
def insert_into_database(unique_rows, db_config):
    try:
        # Validate environment variables
        if not all(db_config.values()):
            raise ValueError("Missing database configuration. Check .env file.")

        # Connect to MySQL database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                LogId INT AUTO_INCREMENT PRIMARY KEY,
                MachineId INT NOT NULL,
                DateCreated DATETIME NOT NULL,
                LogContent VARCHAR(255) NOT NULL
            )
        ''')

        # Insert unique rows in batches for efficiency
        insert_query = '''
            INSERT INTO logs (MachineId, DateCreated, LogContent)
            VALUES (%s, %s, %s)
        '''
        cursor.executemany(insert_query, [(row[0], row[1], row[2]) for row in unique_rows])

        # Commit the transaction
        conn.commit()
        print(f"Inserted {len(unique_rows)} rows into the database successfully.")

    except Error as e:
        print(f"Error connecting to MySQL or inserting data: {str(e)}")
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed.")

# Main execution
if __name__ == "__main__":
    print(f"Current working directory: {os.getcwd()}")  # Debug: Current directory
    print(f"Input CSV path: {input_csv}")  # Debug: Input path
    # Step 1: Parse CSV and filter duplicates
    unique_rows = parse_and_filter_logs(input_csv, output_csv, duplicates_log)
    
    # Step 2: Insert into MySQL database if there are rows to insert
    if unique_rows:
        insert_into_database(unique_rows, db_config)
    else:
        print("No rows to insert into the database.")