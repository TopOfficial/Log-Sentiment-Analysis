import requests
import time

# URL of the FastAPI endpoint you're calling
PROCESS_LOGS_URL = "http://localhost:8000/api/processlogs/process-logs"

def trigger_log_processing():
    print("Triggering log processing via API...")
    try:
        response = requests.post(PROCESS_LOGS_URL)
        if response.status_code == 200:
            print("Log processing triggered successfully.")
            print("Response:", response.json())
            return
        else:
            print(f"Status Code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {str(e)}")
    
    print("All retry attempts failed. Could not trigger log processing.")

if __name__ == "__main__":
    trigger_log_processing()