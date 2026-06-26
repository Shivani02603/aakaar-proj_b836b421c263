import uuid
from typing import Generator, Optional, List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from database.models import ChatMessage, ChatSession
from database.config import get_db

class StreamingResponsesService:
    def __init__(self, db: Session):
        self.db = db

    def create_streaming_response(self, session_id: uuid.UUID, role: str, content: str, chunk_ids: Optional[List[uuid.UUID]] = None) -> ChatMessage:
        """
        Create a new streaming response message.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        new_message = ChatMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            chunk_ids=chunk_ids or [],
            created_at=session.updated_at  # Assuming updated_at is refreshed during streaming
        )
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)
        return new_message

    def get_streaming_response_by_id(self, message_id: uuid.UUID) -> ChatMessage:
        """
        Retrieve a streaming response message by its ID.
        """
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Streaming response not found")
        return message

    def list_all_streaming_responses(self, session_id: uuid.UUID) -> List[ChatMessage]:
        """
        List all streaming response messages for a given chat session.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        return messages

    def update_streaming_response(self, message_id: uuid.UUID, content: Optional[str] = None, chunk_ids: Optional[List[uuid.UUID]] = None) -> ChatMessage:
        """
        Update an existing streaming response message.
        """
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Streaming response not found")

        if content is not None:
            message.content = content
        if chunk_ids is not None:
            message.chunk_ids = chunk_ids

        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_streaming_response(self, message_id: uuid.UUID) -> None:
        """
        Delete a streaming response message by its ID.
        """
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Streaming response not found")

        self.db.delete(message)
        self.db.commit()

    def stream_response_tokens(self, session_id: uuid.UUID, content_generator: Generator[str, None, None]) -> Generator[str, None, None]:
        """
        Stream response tokens to the frontend in real-time.
        """
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        for token in content_generator:
            yield token