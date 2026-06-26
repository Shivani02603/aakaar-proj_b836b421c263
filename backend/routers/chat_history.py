from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import ChatSession, ChatMessage, User
from database.config import get_db
from fastapi.security import OAuth2PasswordBearer

# OAuth2 dependency for JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# APIRouter for Chat History
router = APIRouter(tags=["Chat History"])

# Pydantic schemas for request and response validation
class ChatSessionBase(BaseModel):
    user_id: UUID
    document_id: UUID
    title: str

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionResponse(ChatSessionBase):
    id: UUID
    created_at: str
    updated_at: str

class ChatMessageBase(BaseModel):
    session_id: UUID
    role: str
    content: str
    chunk_ids: List[UUID]

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    created_at: str

# Dependency to get the current user from the JWT token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user

# Endpoint to create a new chat session
@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(session_data: ChatSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_session = ChatSession(
        user_id=current_user.id,
        document_id=session_data.document_id,
        title=session_data.title,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

# Endpoint to list all chat sessions for the current user
@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_chat_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()
    return sessions

# Endpoint to get all messages for a specific chat session
@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_chat_messages(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    return messages

# Endpoint to delete a chat session
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Chat session deleted successfully"}