from pydantic import BaseModel
from typing import Optional, List
from app.schemas.messages import MessageCreate


class ConversationResponse(BaseModel):
    ConversationId: int
    LogId: int

class ConversationCreate(BaseModel):
    pass

class ConversationResponse(BaseModel):
    ConversationId: int

    class Config:
        orm_mode = True

# Define the schema for the request body
class CreateConversationRequest(BaseModel):
    logId: int
    messages: Optional[List[MessageCreate]] = None  # Optional messages
