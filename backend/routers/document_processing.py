from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document, DocumentChunk
from database.config import get_db
from backend.services.document_processing_service import (
    extract_text_from_pdf,
    split_text_into_chunks,
    generate_embeddings,
)
from backend.services.auth import get_current_user

router = APIRouter(tags=["Document Processing"])

# Pydantic schemas
class DocumentProcessingRequest(BaseModel):
    document_id: UUID

class DocumentProcessingResponse(BaseModel):
    document_id: UUID
    chunks: List[dict]

class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: dict

# Route to process a document
@router.post("/process", response_model=DocumentProcessingResponse)
async def process_document(
    request: DocumentProcessingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch the document from the database
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to process this document",
        )

    # Extract text from the document
    try:
        extracted_text = extract_text_from_pdf(document.file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from document: {str(e)}",
        )

    # Split the text into chunks
    try:
        chunks = split_text_into_chunks(extracted_text, chunk_size=1000, overlap=200)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to split text into chunks: {str(e)}",
        )

    # Generate embeddings for each chunk
    try:
        chunk_objects = []
        for index, chunk in enumerate(chunks):
            embedding = generate_embeddings(chunk)
            chunk_object = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
                metadata={},
            )
            db.add(chunk_object)
            chunk_objects.append(chunk_object)
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}",
        )

    # Prepare response
    response_chunks = [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "embedding": chunk.embedding,
            "metadata": chunk.metadata,
        }
        for chunk in chunk_objects
    ]
    return DocumentProcessingResponse(document_id=document.id, chunks=response_chunks)

# Route to list all document chunks
@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch the document from the database
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view chunks for this document",
        )

    # Fetch chunks from the database
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    return [
        DocumentChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=chunk.metadata,
        )
        for chunk in chunks
    ]

# Route to delete a document chunk
@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch the chunk from the database
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document chunk not found",
        )

    # Fetch the document to verify ownership
    document = db.query(Document).filter(Document.id == chunk.document_id).first()
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this chunk",
        )

    # Delete the chunk
    db.delete(chunk)
    db.commit()