from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Machine(Base):
    __tablename__ = "machine"

    MachineId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    MachineName = Column(String(255), nullable=False)

    # Relationship: One Machine -> Many Logs
    logs = relationship("Logs", back_populates="machine")

    # Relationship: One Machine -> Many KnowledgeBase entries
    knowledge_entries = relationship("KnowledgeBase", back_populates="machine")
