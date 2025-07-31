from pydantic import BaseModel

class ProcessedLogBase(BaseModel):
    LogId: int
    Sentiment: int
    Resolved: bool

class ProcessedLogCreate(ProcessedLogBase):
    pass

from typing import Optional

class ProcessedLogResponse(BaseModel):
    ProcessId: int
    LogId: int
    Sentiment: Optional[int]
    Resolved: bool
    DateCreated: str  # From Logs table
    LogContent: str   # From Logs table
    MachineName: str  # From Machine table



class ResolvedStatusUpdate(BaseModel):
    resolved: bool