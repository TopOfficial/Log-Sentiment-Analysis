from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledgebase"

    KnowledgeId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Content = Column(String, nullable=False)
    ContentType = Column(String(255), nullable=False)
    MachineId = Column(Integer, ForeignKey("machine.MachineId"), nullable=False)
    Solution = Column(String, nullable=True)

    # Relationship: Many KnowledgeBase entries -> One Machine
    machine = relationship("Machine", back_populates="knowledge_entries")
