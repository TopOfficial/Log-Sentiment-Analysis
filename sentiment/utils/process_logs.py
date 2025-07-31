import os
from utils.create_folders import get_output_subdirectory
from utils.logs_to_csv import transform_logs_to_csv


def process_logs_folder(logs_dir, output_dir):
    """
    Processes all log files in the specified logs directory.

    :param logs_dir: Directory containing log files.
    :param output_dir: Directory to save transformed CSV files.
    """
    try:
        print(f"Processing logs folder: {logs_dir}")
        for root, _, files in os.walk(logs_dir):
            for file in files:
                if file.endswith('.log'):
                    log_file_path = os.path.join(root, file)

                    # Get the corresponding output subdirectory
                    output_subdir = get_output_subdirectory(logs_dir, root, output_dir)

                    # Generate transformed CSV file path
                    csv_file_path = os.path.join(output_subdir, file.replace(".log", ".csv"))

                    # Transform log file to CSV
                    transform_logs_to_csv(log_file_path, csv_file_path)

        print("Log folder processing complete. Transformed logs saved as CSV.")
    except Exception as e:
        print(f"Failed to process logs folder. Error: {str(e)}")