from fastapi import FastAPI, Depends
from app.routers import error_page, chat_page, knowledge_base_page, process_log
from app.models import *
from app.database import Base, engine, db
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy.sql import text  
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Machine Logs App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include routers for API endpoints
app.include_router(error_page.router, prefix="/api/errors", tags=["Error Page"])
app.include_router(chat_page.router, prefix="/api/chat", tags=["Chat Page"])
app.include_router(knowledge_base_page.router, prefix="/api/knowledgebase", tags=["Knowledge Base"])
app.include_router(process_log.router, prefix="/api/processlogs", tags=["Log Processing"])

# Start/stop database connection when the app starts/stops
@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Use `text()` to execute raw SQL queries in SQLAlchemy 2.x
        db.execute(text("SELECT 1"))
        return {"success": True, "message": "Database connection is working!"}
    except Exception as e:
        return {"success": False, "error": str(e)}
