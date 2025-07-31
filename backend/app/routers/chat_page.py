from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.crud.knowledge_base import get_knowledge_base_entry_by_content, create_knowledge_base_entry
from app.crud.conversation import create_conversation
from app.crud.messages import create_message
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.messages import MessageCreate, MessageBase, MessageResponse
from app.schemas.knowledge_base import KnowledgeBaseCreate
from pydantic import BaseModel
from app.models.conversation import Conversation
from app.models.messages import Messages
from app.models.logs import Logs
from app.models.processed_log import ProcessedLog
from app.schemas.processed_log import ResolvedStatusUpdate
from typing import Optional
from app.schemas.conversation import CreateConversationRequest
import uuid
import requests

router = APIRouter()

class SolutionRequest(BaseModel):
    conversation_id: str
    log_content: str

@router.post("/solution", response_model=dict)
def get_solution_for_error(request: SolutionRequest, db: Session = Depends(get_db)):
    # Check if the solution exists in the knowledge base
    knowledge_entry = get_knowledge_base_entry_by_content(db, content=request.log_content)
    if knowledge_entry:
        return {"knownError": True, "solution": knowledge_entry[0].Solution}

    # If no solution exists, query the LLM API for a generated solution
    try:
        # Use the provided conversation_id or generate a new one if not provided (though it should be provided by the client)
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Prepare the query for the LLM
        query_input = {
            "conversation_id": conversation_id,
            "query": f"Provide a solution for the error: {request.log_content}"
        }

        # Call the LLM API to get the solution
        llm_response = requests.post("http://localhost:8001/query", json=query_input)
        if llm_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get LLM response")
        llm_data = llm_response.json()
        generated_solution = llm_data["answer"]

        return {"knownError": False, "generatedSolution": generated_solution}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")




@router.post("/conversation", response_model=ConversationResponse)
def create_conversation_with_body(
    request: CreateConversationRequest,  # Use the new schema
    db: Session = Depends(get_db)
):
    # Extract logId and messages from the request body
    logId = request.logId
    messages = request.messages

    # Check if a conversation for this logId already exists
    existing_conversation = db.query(Conversation).filter(Conversation.LogId == logId).first()
    if existing_conversation:
        raise HTTPException(status_code=400, detail="A conversation for this logId already exists")

    # Create a new conversation
    db_conversation = Conversation(LogId=logId)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)

    # Save messages dynamically linked to the conversation (if provided)
    if messages:
        for message in messages:
            db_message = Messages(
                SentDate=message.SentDate,
                Role=message.Role,
                Content=message.Content,
                ConversationId=db_conversation.ConversationId
            )
            db.add(db_message)

    db.commit()
    return db_conversation



@router.put("/conversation/{conversation_id}/messages", response_model=list[MessageResponse])
def add_messages_to_conversation(
    conversation_id: int, messages: list[MessageBase], db: Session = Depends(get_db)
):
    # Find the conversation by ID
    db_conversation = db.query(Conversation).filter(Conversation.ConversationId == conversation_id).first()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Add new messages to the conversation
    message_responses = []
    for message in messages:
        db_message = Messages(
            SentDate=message.SentDate,
            Role=message.Role,
            Content=message.Content,
            ConversationId=conversation_id
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        message_responses.append(db_message)

    return message_responses

@router.get("/conversation/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages_by_conversation(
    conversation_id: int, db: Session = Depends(get_db)
):
    # Check if the conversation exists
    db_conversation = db.query(Conversation).filter(Conversation.ConversationId == conversation_id).first()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Fetch all messages for the conversation
    messages = db.query(Messages).filter(Messages.ConversationId == conversation_id).all()
    return messages


@router.get("/conversation/{conversation_id}/log", response_model=dict)
def get_log_by_conversation(
    conversation_id: int, db: Session = Depends(get_db)
):
    # Check if the conversation exists
    db_conversation = db.query(Conversation).filter(Conversation.ConversationId == conversation_id).first()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Fetch the LogContent and LogId from the Logs table using the LogId in the Conversation table
    log = db.query(Logs).filter(Logs.LogId == db_conversation.LogId).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found for the given conversation")

    # Return LogId and LogContent
    return {
        "LogId": log.LogId,
        "LogContent": log.LogContent
    }


@router.get("/log/{log_id}/resolved", response_model=dict)
def get_resolved_status_by_log_id(
    log_id: int, db: Session = Depends(get_db)
):
    # Fetch the processed log entry using logId
    processed_log = db.query(ProcessedLog).filter(ProcessedLog.LogId == log_id).first()
    
    if not processed_log:
        raise HTTPException(status_code=404, detail="Processed log not found")

    # Return the resolved status
    return {"resolved": processed_log.Resolved}

@router.patch("/log/{log_id}/resolved", response_model=dict)
def update_resolved_status_by_log_id(
    log_id: int,
    update: ResolvedStatusUpdate,
    db: Session = Depends(get_db)
):
    # Find the processed log entry by logId
    processed_log = db.query(ProcessedLog).filter(ProcessedLog.LogId == log_id).first()

    if not processed_log:
        raise HTTPException(status_code=404, detail="Processed log not found")

    # Update the resolved status
    processed_log.Resolved = update.resolved
    db.commit()
    db.refresh(processed_log)

    return {
        "success": True,
        "message": "Resolved status updated successfully",
        "resolved": processed_log.Resolved,
    }

@router.get("/conversation/log/{log_id}", response_model=Optional[ConversationResponse])
def get_conversation_by_log_id(log_id: int, db: Session = Depends(get_db)):
    # Query the Conversation table to check if a conversation exists for the given LogId
    conversation = db.query(Conversation).filter(Conversation.LogId == log_id).first()

    if not conversation:
        return None  # Return None if no conversation exists

    # Return the conversation details
    return ConversationResponse(
        ConversationId=conversation.ConversationId,
        LogId=conversation.LogId
    )
