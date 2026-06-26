from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime
from database.models import User
from database.config import get_db
from typing import List

# Router
router = APIRouter(tags=["Sessions"])

# SQLAlchemy Models
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas
class SessionCreate(BaseModel):
    title: str = "New Chat"

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime

# Dependency
async def get_current_user(token: str = Depends(), db: Session = Depends(get_db)):
    # Implementation same as auth.py
    pass

# Routes
@router.get("/", response_model=List[SessionResponse])
async def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    return sessions

@router.post("/", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_session = ChatSession(user_id=current_user.id, title=session_data.title)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def list_messages(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def create_message(session_id: UUID, message_data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    new_message = ChatMessage(session_id=session_id, role=message_data.role, content=message_data.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message