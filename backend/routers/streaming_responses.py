from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import ChatMessage, ChatSession, Document
from database.config import get_db
from backend.services.streaming_responses_service import generate_streaming_response
from backend.services.auth import get_current_user

router = APIRouter(tags=["Streaming Responses"])

class StreamingRequest(BaseModel):
    session_id: UUID = Field(..., description="ID of the chat session")
    query: str = Field(..., description="User's query for the AI system")

class StreamingResponseSchema(BaseModel):
    token: str = Field(..., description="Generated token from the AI system")

@router.post("/stream", response_model=None, status_code=status.HTTP_200_OK)
async def stream_response(
    request: StreamingRequest,
    db: Session = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """
    Stream AI-generated tokens in real-time based on the user's query.
    """
    # Validate session existence
    session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Validate document association
    document = db.query(Document).filter(Document.id == session.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated document not found"
        )

    # Generate streaming response
    async def token_generator():
        async for token in generate_streaming_response(request.query, document.file_path):
            yield f"data: {token}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")