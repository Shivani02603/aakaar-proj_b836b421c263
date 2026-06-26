import uuid
from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database.models import ChatSession, ChatMessage, User, Document
from database.config import get_db

class ChatHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_chat_session(self, user_id: uuid.UUID, document_id: uuid.UUID, title: str) -> ChatSession:
        user = self.db.query(User).filter(User.id == user_id).first()
        document = self.db.query(Document).filter(Document.id == document_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        chat_session = ChatSession(
            id=uuid.uuid4(),
            user_id=user_id,
            document_id=document_id,
            title=title,
        )
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        return chat_session

    def get_chat_session_by_id(self, session_id: uuid.UUID) -> ChatSession:
        chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return chat_session

    def list_chat_sessions(self, user_id: uuid.UUID) -> List[ChatSession]:
        chat_sessions = self.db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
        return chat_sessions

    def update_chat_session(self, session_id: uuid.UUID, title: Optional[str] = None) -> ChatSession:
        chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        if title:
            chat_session.title = title

        self.db.commit()
        self.db.refresh(chat_session)
        return chat_session

    def delete_chat_session(self, session_id: uuid.UUID) -> None:
        chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        self.db.delete(chat_session)
        self.db.commit()

    def create_chat_message(self, session_id: uuid.UUID, role: str, content: str, chunk_ids: Optional[List[uuid.UUID]] = None) -> ChatMessage:
        chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        chat_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            chunk_ids=chunk_ids or [],
        )
        self.db.add(chat_message)
        self.db.commit()
        self.db.refresh(chat_message)
        return chat_message

    def get_chat_message_by_id(self, message_id: uuid.UUID) -> ChatMessage:
        chat_message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")
        return chat_message

    def list_chat_messages(self, session_id: uuid.UUID) -> List[ChatMessage]:
        chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        chat_messages = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        return chat_messages

    def update_chat_message(self, message_id: uuid.UUID, content: Optional[str] = None, chunk_ids: Optional[List[uuid.UUID]] = None) -> ChatMessage:
        chat_message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")

        if content:
            chat_message.content = content
        if chunk_ids is not None:
            chat_message.chunk_ids = chunk_ids

        self.db.commit()
        self.db.refresh(chat_message)
        return chat_message

    def delete_chat_message(self, message_id: uuid.UUID) -> None:
        chat_message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")

        self.db.delete(chat_message)
        self.db.commit()