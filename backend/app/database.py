from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from app.config import settings

# Database Configuration
DATABASE_URL = settings.DATABASE_URL

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Async Database for FastAPI
db = Database(DATABASE_URL)

# Dependency to get the database session (sync operations)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
