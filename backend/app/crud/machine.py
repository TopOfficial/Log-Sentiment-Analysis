from sqlalchemy.orm import Session
from app.models.machine import Machine
from app.schemas.machine import MachineCreate

def get_machines(db: Session):
    """Retrieve all machines."""
    return db.query(Machine).all()

def get_machine_by_id(db: Session, machine_id: int):
    """Retrieve a machine by its ID."""
    return db.query(Machine).filter(Machine.MachineId == machine_id).first()

def create_machine(db: Session, machine: MachineCreate):
    """Create a new machine."""
    db_machine = Machine(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine
