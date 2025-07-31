from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.crud.processed_log import get_processed_logs, update_resolved_status
from app.crud.logs import get_logs_by_machine
from app.schemas.processed_log import ProcessedLogResponse, ResolvedStatusUpdate
from app.models.processed_log import ProcessedLog
from app.models.logs import Logs
from app.models.machine import Machine
router = APIRouter()

@router.get("/", response_model=List[ProcessedLogResponse])
def get_errors(
    machine_name: Optional[str] = None,
    resolved: Optional[bool] = None,
    sentiment: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Join ProcessedLog, Logs, and Machine tables
    query = (
        db.query(ProcessedLog, Logs, Machine)
        .join(Logs, ProcessedLog.LogId == Logs.LogId)
        .join(Machine, Logs.MachineId == Machine.MachineId)
    )

    # Apply filters
    if machine_name:
        query = query.filter(Machine.MachineName == machine_name)  # Filter by machine name
    if resolved is not None:
        query = query.filter(ProcessedLog.Resolved == resolved)  # Filter by resolved status
    if sentiment is not None:
        query = query.filter(ProcessedLog.Sentiment == sentiment)  # Filter by sentiment

    # Execute the query
    results = query.all()

    # Prepare the response
    response = [
        ProcessedLogResponse(
            ProcessId=processed_log.ProcessId,
            LogId=processed_log.LogId,
            Sentiment=processed_log.Sentiment,
            Resolved=processed_log.Resolved,
            DateCreated=log.DateCreated.isoformat(),  # Format datetime to ISO string
            LogContent=log.LogContent,
            MachineName=machine.MachineName  # Include MachineName
        )
        for processed_log, log, machine in results
    ]

    return response




@router.patch("/{process_id}", response_model=dict)
def update_error_resolved_status(process_id: int, update: ResolvedStatusUpdate, db: Session = Depends(get_db)):
    # Use the `resolved` value from the request body
    processed_log = update_resolved_status(db, process_id, update.resolved)
    if not processed_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    return {"success": True, "message": "Resolved status updated successfully"}
