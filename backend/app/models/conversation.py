from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversation"

    ConversationId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    LogId = Column(Integer, ForeignKey("logs.LogId"), nullable=False)

    # Relationship: Many Conversations -> One Log
    log = relationship("Logs", back_populates="conversation")

    # Relationship: One Conversation -> Many Messages
    messages = relationship("Messages", back_populates="conversation")
