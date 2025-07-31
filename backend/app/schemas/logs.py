from pydantic import BaseModel
from datetime import datetime

class LogBase(BaseModel):
    MachineId: int
    DateCreated: datetime
    LogContent: str

class LogCreate(LogBase):
    pass

class LogResponse(LogBase):
    LogId: int

    class Config:
        orm_mode = True
