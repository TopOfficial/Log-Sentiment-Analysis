from sqlalchemy.orm import Session
from app.models.processed_log import ProcessedLog
from app.schemas.processed_log import ProcessedLogCreate

def get_processed_logs(db: Session):
    """Retrieve all processed logs."""
    return db.query(ProcessedLog).all()

def get_processed_log_by_id(db: Session, process_id: int):
    """Retrieve a processed log by its ID."""
    return db.query(ProcessedLog).filter(ProcessedLog.ProcessId == process_id).first()

def create_processed_log(db: Session, processed_log: ProcessedLogCreate):
    """Create a new processed log."""
    db_processed_log = ProcessedLog(**processed_log.dict())
    db.add(db_processed_log)
    db.commit()
    db.refresh(db_processed_log)
    return db_processed_log

def update_resolved_status(db: Session, process_id: int, resolved: bool):
    """Update the resolved status of a processed log."""
    processed_log = db.query(ProcessedLog).filter(ProcessedLog.ProcessId == process_id).first()
    if processed_log:
        processed_log.Resolved = resolved
        db.commit()
        db.refresh(processed_log)
    return processed_log
