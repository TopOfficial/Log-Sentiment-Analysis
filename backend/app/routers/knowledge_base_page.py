from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.crud.knowledge_base import (
    get_knowledge_base_entries,
    get_knowledge_base_entry_by_id,
    create_knowledge_base_entry,
    update_knowledge_base_entry_solution,
    get_knowledge_base_entries_with_machine_name
)
from app.schemas.knowledge_base import KnowledgeBaseUpdate,KnowledgeBaseCreate, KnowledgeBaseResponse
from app.schemas.machine import MachineResponse
from app.models.machine import Machine

router = APIRouter()

@router.get("/", response_model=List[KnowledgeBaseResponse])
def get_all_knowledge_base_entries(
    machine_name: Optional[str] = None,
    content: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Retrieve all knowledge base entries with optional filters
    entries = get_knowledge_base_entries(db)
    if machine_name:
        entries = [entry for entry in entries if entry.machine.MachineName == machine_name]
    if content:
        entries = [entry for entry in entries if content.lower() in entry.Content.lower()]
    return entries


@router.post("/", response_model=KnowledgeBaseResponse)
def add_new_knowledge_base_entry(entry: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    # Create a new knowledge base entry
    return create_knowledge_base_entry(db, entry)

@router.get("/with_name", response_model=List[KnowledgeBaseResponse])
def get_all_knowledge_base_entries(db: Session = Depends(get_db)):
    entries = get_knowledge_base_entries_with_machine_name(db)

    # Convert query results (tuples) into KnowledgeBaseResponse objects
    response = [
        KnowledgeBaseResponse(
            KnowledgeId=entry[0],  # From KnowledgeBase.KnowledgeId
            Content=entry[1],      # From KnowledgeBase.Content
            ContentType=entry[2],  # From KnowledgeBase.ContentType
            MachineId=entry[3],    # From KnowledgeBase.MachineId
            Solution=entry[4],     # From KnowledgeBase.Solution
            MachineName=entry[5]   # From Machine.MachineName
        )
        for entry in entries
    ]
    return response

@router.patch("/{knowledge_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base_entry(
    knowledge_id: int, update: KnowledgeBaseUpdate, db: Session = Depends(get_db)
):
    # Update the solution for a knowledge base entry
    entry = update_knowledge_base_entry_solution(db, knowledge_id, update.solution)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")
    return entry

@router.get("/machines", response_model=List[MachineResponse])
def get_all_machines(db: Session = Depends(get_db)):
    machines = db.query(Machine).all()
    return [
        MachineResponse(MachineId=machine.MachineId, MachineName=machine.MachineName)
        for machine in machines
    ]

# New endpoint to check if a problem exists in the knowledge base
@router.get("/exists", response_model=dict)
def check_problem_exists(
    content: str,
    db: Session = Depends(get_db)
):
    """
    Check if a problem (based on content) exists in the knowledge base.
    
    Args:
        content (str): The content of the problem to check.
        db (Session): Database session dependency.
    
    Returns:
        dict: Contains 'exists' (bool) and 'knowledge_id' (int or null) if found.
    """
    entries = get_knowledge_base_entries(db)
    matching_entries = [entry for entry in entries if content.lower() in entry.Content.lower()]
    
    if matching_entries:
        return {"exists": True, "knowledge_id": matching_entries[0].KnowledgeId}
    return {"exists": False, "knowledge_id": None}