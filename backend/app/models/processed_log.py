from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ProcessedLog(Base):
    __tablename__ = "processedlog"

    ProcessId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    LogId = Column(Integer, ForeignKey("logs.LogId"), nullable=False)
    Sentiment = Column(Integer, nullable=False)
    Resolved = Column(Boolean, default=False)

    # Define the relationship to Logs
    log = relationship("Logs", back_populates="processed_log")
