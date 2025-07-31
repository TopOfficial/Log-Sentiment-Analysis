from pydantic import BaseModel
from typing import Optional

class KnowledgeBaseBase(BaseModel):
    Content: str
    ContentType: str
    MachineId: int
    Solution: Optional[str] = None

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseResponse(KnowledgeBaseBase):
    # Include MachineName only in the response schema
    KnowledgeId: int
    MachineName: Optional[str] = None

    class Config:
        orm_mode = True

class KnowledgeBaseUpdate(BaseModel):
    solution: str
