from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Messages(Base):
    __tablename__ = "messages"

    MessageId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    SentDate = Column(DateTime, nullable=False)  # Updated from Timestamp to SentDate
    Role = Column(Integer, nullable=False)  # Role: 0 = LLM, 1 = User
    Content = Column(String, nullable=False)
    ConversationId = Column(Integer, ForeignKey("conversation.ConversationId"), nullable=False)

    # Relationship: Many Messages -> One Conversation
    conversation = relationship("Conversation", back_populates="messages")
