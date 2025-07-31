from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Logs(Base):
    __tablename__ = "logs"

    LogId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    MachineId = Column(Integer, ForeignKey("machine.MachineId"), nullable=False)
    DateCreated = Column(DateTime, nullable=False)
    LogContent = Column(String, nullable=False)

    # Relationship: Many Logs -> One Machine
    machine = relationship("Machine", back_populates="logs")

    # Relationship: One Log -> One ProcessedLog
    processed_log = relationship("ProcessedLog", back_populates="log", uselist=False)

    # Relationship: One Log -> One Conversation
    conversation = relationship("Conversation", back_populates="log", uselist=False)
