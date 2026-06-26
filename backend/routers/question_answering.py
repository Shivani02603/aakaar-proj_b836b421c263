from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from backend.services.question_answering_service import generate_answer_with_citations
from backend.services.auth import get_current_user

router = APIRouter(tags=["Question Answering"])

# Pydantic schemas
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query for question answering")

class Citation(BaseModel):
    chunk_id: UUID = Field(..., description="The ID of the document chunk")
    content: str = Field(..., description="The content of the document chunk")

class AnswerResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the query")
    citations: List[Citation] = Field(..., description="List of citations used to generate the answer")

# Route handlers
@router.post("/answer", response_model=AnswerResponse, status_code=status.HTTP_200_OK)
async def get_answer(
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
):
    """
    Generate an answer to the user's query using relevant document chunks and an LLM.
    """
    try:
        # Retrieve the top-5 most relevant chunks and generate an answer
        answer, citations = generate_answer_with_citations(
            query=query_request.query,
            user_id=current_user,
            db=db,
            top_k=5
        )
        return AnswerResponse(answer=answer, citations=citations)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}"
        )