from sqlalchemy.orm import Session
from app.models.messages import Messages
from app.schemas.messages import MessageCreate

def get_messages_by_conversation(db: Session, conversation_id: int):
    """Retrieve all messages for a specific conversation."""
    return db.query(Messages).filter(Messages.ConversationId == conversation_id).all()

def create_message(db: Session, message: MessageCreate):
    """Create a new message."""
    db_message = Messages(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
