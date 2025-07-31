import csv

# Input and output file paths
input_file = 'sentiment/example_logs/test.log'
output_file = 'sentiment/example_logs/output.csv'

# Read the text file and write to CSV
with open(input_file, 'r') as txt_file, open(output_file, 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    # Each line becomes a row in the CSV
    for line in txt_file:
        # Strip newline characters and write as a single-column row
        writer.writerow([line.strip()])