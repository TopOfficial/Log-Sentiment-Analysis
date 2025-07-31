from pydantic import BaseModel

class MachineBase(BaseModel):
    MachineName: str

class MachineCreate(MachineBase):
    pass

class MachineResponse(BaseModel):
    MachineId: int
    MachineName: str

    class Config:
        orm_mode = True
