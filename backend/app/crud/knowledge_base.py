from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseCreate
from app.models.machine import Machine

def get_knowledge_base_entries(db: Session):
    """Retrieve all knowledge base entries."""
    return db.query(KnowledgeBase).all()

def get_knowledge_base_entry_by_id(db: Session, knowledge_id: int):
    """Retrieve a knowledge base entry by its ID."""
    return db.query(KnowledgeBase).filter(KnowledgeBase.KnowledgeId == knowledge_id).first()

def get_knowledge_base_entries_with_machine_name(db: Session):
    """Retrieve all knowledge base entries with the machine name."""
    results = (
        db.query(
            KnowledgeBase.KnowledgeId,
            KnowledgeBase.Content,
            KnowledgeBase.ContentType,
            KnowledgeBase.MachineId,  # Include MachineId
            KnowledgeBase.Solution,
            Machine.MachineName
        )
        .join(Machine, KnowledgeBase.MachineId == Machine.MachineId)
        .all()
    )
    return results



def get_knowledge_base_entry_by_content(db: Session, content: str):
    """Retrieve a knowledge base entry by its content."""
    return db.query(KnowledgeBase).filter(KnowledgeBase.Content.ilike(f"%{content}%")).all()

def create_knowledge_base_entry(db: Session, entry: KnowledgeBaseCreate):
    """Create a new knowledge base entry."""
    db_entry = KnowledgeBase(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def update_knowledge_base_entry_solution(db: Session, knowledge_id: int, solution: str):
    """Update the solution for a knowledge base entry."""
    entry = db.query(KnowledgeBase).filter(KnowledgeBase.KnowledgeId == knowledge_id).first()
    if entry:
        entry.Solution = solution
        db.commit()
        db.refresh(entry)
    return entry
