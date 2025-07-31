from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    SentDate: datetime
    Role: int  # 0 = LLM, 1 = User
    Content: str
    ConversationId: int

class MessageCreate(BaseModel):
    SentDate: datetime
    Role: int  # 0 = LLM, 1 = User
    Content: str


class MessageResponse(MessageBase):
    MessageId: int

    class Config:
        orm_mode = True
