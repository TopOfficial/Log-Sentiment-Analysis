from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.logs import Logs
from app.models.processed_log import ProcessedLog
from app.schemas.processed_log import ProcessedLogResponse, ProcessedLogCreate
from app.models.machine import Machine
from app.schemas.machine import MachineResponse
import requests
import time

# Initialize the FastAPI router
router = APIRouter()

# API endpoint for sentiment analysis
api_url = "http://localhost:8002/analyze_batch"
BATCH_SIZE = 10

# # Dependency to get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

def process_batch_db(batch, db: Session):
    """
    Processes a batch of logs by sending them to the API and saving results to the ProcessedLog table.
    Retries API request up to 3 times on failure.

    :param batch: List of (log_id, log_content) tuples to process.
    :param db: SQLAlchemy database session.
    """
    try:
        messages = [log_content for _, log_content in batch]
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            response = requests.post(api_url, json={"log_sentences": messages})
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                for (log_id, _), result in zip(batch, results):
                    # Transform sentiment: 1 if API returns -1, else 0
                    api_sentiment = result.get("sentiment", 0)
                    transformed_sentiment = 1 if api_sentiment == -1 else 0
                    
                    # Create ProcessedLog entry
                    processed_log = ProcessedLogCreate(
                        LogId=log_id,
                        Sentiment=transformed_sentiment,
                        Resolved=False
                    )
                    db_processed_log = ProcessedLog(**processed_log.dict())
                    db.add(db_processed_log)
                    db.commit()
                    db.refresh(db_processed_log)
                    print(f"Saved sentiment result for LogId {log_id}: API Sentiment={api_sentiment}, Transformed Sentiment={transformed_sentiment}")
                break  # Exit retry loop on success
            else:
                print(f"API error on attempt {attempt}/{max_retries}: {response.status_code}, {response.text}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"All {max_retries} retries failed. Saving default results.")
                    for log_id, _ in batch:
                        # Save default result (Sentiment=0 for errors)
                        processed_log = ProcessedLogCreate(
                            LogId=log_id,
                            Sentiment=0,
                            Resolved=False
                        )
                        db_processed_log = ProcessedLog(**processed_log.dict())
                        db.add(db_processed_log)
                        db.commit()
                        db.refresh(db_processed_log)
                        print(f"Saved error result for LogId {log_id} after API error")
                        
    except Exception as e:
        print(f"Exception while processing batch: {str(e)}")
        for log_id, _ in batch:
            # Save default result (Sentiment=0 for exceptions)
            processed_log = ProcessedLogCreate(
                LogId=log_id,
                Sentiment=0,
                Resolved=False
            )
            db_processed_log = ProcessedLog(**processed_log.dict())
            db.add(db_processed_log)
            db.commit()
            db.refresh(db_processed_log)
            print(f"Saved error result for LogId {log_id} after exception")

def process_logs_from_db(db: Session):
    """
    Processes unprocessed logs from the Logs table, performs sentiment analysis,
    and saves results to the ProcessedLog table.

    :param db: SQLAlchemy database session.
    :return: Dictionary with processing status and details.
    """
    try:
        print("Starting log processing from database...")
        start_time = time.time()

        # Query unprocessed logs (logs without corresponding ProcessedLog entries)
        unprocessed_logs = (
            db.query(Logs)
            .outerjoin(ProcessedLog, Logs.LogId == ProcessedLog.LogId)
            .filter(ProcessedLog.LogId.is_(None))
            .all()
        )
        
        if not unprocessed_logs:
            print("No unprocessed logs found.")
            return {"status": "success", "message": "No unprocessed logs found.", "logs_processed": 0}

        print(f"Found {len(unprocessed_logs)} unprocessed logs.")
        
        # Process logs in batches
        batch = []
        for log in unprocessed_logs:
            batch.append((log.LogId, log.LogContent))
            if len(batch) == BATCH_SIZE:
                process_batch_db(batch, db)
                batch = []
        
        # Process remaining batch
        if batch:
            process_batch_db(batch, db)
        
        end_time = time.time()
        print(f"Processing complete. Total time taken: {end_time - start_time:.2f} seconds")
        return {
            "status": "success",
            "message": f"Processed {len(unprocessed_logs)} logs successfully.",
            "logs_processed": len(unprocessed_logs),
            "time_taken_seconds": round(end_time - start_time, 2)
        }
        
    except Exception as e:
        print(f"Failed to process logs from database. Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process logs: {str(e)}")

@router.post("/process-logs", response_model=dict)
async def process_logs_endpoint(db: Session = Depends(get_db)):
    """
    API endpoint to trigger processing of unprocessed logs from the Logs table.
    Returns a summary of the processing result.
    """
    result = process_logs_from_db(db)
    return result

@router.get("/processed-logs", response_model=List[ProcessedLogResponse])
async def get_processed_logs(
    machine_id: Optional[int] = None,
    sentiment: Optional[int] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all processed logs with optional filters for machine_id, sentiment, and resolved status.
    """
    try:
        query = (
            db.query(ProcessedLog, Logs.DateCreated, Logs.LogContent, Machine.MachineName)
            .join(Logs, ProcessedLog.LogId == Logs.LogId)
            .join(Machine, Logs.MachineId == Machine.MachineId)
        )

        # Apply filters
        if machine_id is not None:
            query = query.filter(Logs.MachineId == machine_id)
        if sentiment is not None:
            query = query.filter(ProcessedLog.Sentiment == sentiment)
        if resolved is not None:
            query = query.filter(ProcessedLog.Resolved == resolved)

        processed_logs = query.all()

        # Convert to response model
        response = [
            ProcessedLogResponse(
                ProcessId=entry[0].ProcessId,
                LogId=entry[0].LogId,
                Sentiment=entry[0].Sentiment,
                Resolved=entry[0].Resolved,
                DateCreated=entry[1].isoformat(),
                LogContent=entry[2],
                MachineName=entry[3]
            )
            for entry in processed_logs
        ]
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve processed logs: {str(e)}")

@router.get("/exists", response_model=dict)
async def check_processed_log_exists(
    log_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a log has been processed (exists in ProcessedLog table).
    
    Args:
        log_id (int): The ID of the log to check.
        db (Session): Database session dependency.
    
    Returns:
        dict: Contains 'exists' (bool) and 'process_id' (int or null) if found.
    """
    try:
        processed_log = db.query(ProcessedLog).filter(ProcessedLog.LogId == log_id).first()
        if processed_log:
            return {"exists": True, "process_id": processed_log.ProcessId}
        return {"exists": False, "process_id": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check processed log: {str(e)}")

@router.get("/machines", response_model=List[MachineResponse])
async def get_all_machines(db: Session = Depends(get_db)):
    """
    Retrieve all machines.
    """
    try:
        machines = db.query(Machine).all()
        return [
            MachineResponse(MachineId=machine.MachineId, MachineName=machine.MachineName)
            for machine in machines
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve machines: {str(e)}")