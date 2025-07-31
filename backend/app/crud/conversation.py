from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate

def get_conversations(db: Session):
    """Retrieve all conversations."""
    return db.query(Conversation).all()

def create_conversation(db: Session, conversation: ConversationCreate):
    """Create a new conversation."""
    db_conversation = Conversation(**conversation.dict())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation
