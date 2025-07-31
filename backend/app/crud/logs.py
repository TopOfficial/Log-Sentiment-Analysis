from sqlalchemy.orm import Session
from app.models.logs import Logs
from app.schemas.logs import LogCreate

def get_logs(db: Session):
    """Retrieve all logs."""
    return db.query(Logs).all()

def get_log_by_id(db: Session, log_id: int):
    """Retrieve a log by its ID."""
    return db.query(Logs).filter(Logs.LogId == log_id).first()

def get_logs_by_machine(db: Session, machine_id: int):
    """Retrieve logs by machine ID."""
    return db.query(Logs).filter(Logs.MachineId == machine_id).all()

def create_log(db: Session, log: LogCreate):
    """Create a new log."""
    db_log = Logs(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
