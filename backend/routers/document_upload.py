from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document, User
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.document_upload_service import save_document_metadata, process_uploaded_file

router = APIRouter(tags=["Document Upload"])

# Pydantic schemas
class DocumentBase(BaseModel):
    filename: str
    file_size: int
    file_path: str
    status: str

class DocumentCreate(BaseModel):
    filename: str = Field(..., example="example.pdf")
    file_size: int = Field(..., example=1024)
    file_path: str = Field(..., example="/uploads/example.pdf")
    status: str = Field(..., example="uploaded")

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    created_at: str
    processed_at: str | None

# Routes
@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to upload a document. Requires authentication.
    """
    try:
        # Save file to disk and process metadata
        file_path, file_size = await process_uploaded_file(file)
        document_metadata = DocumentCreate(
            filename=file.filename,
            file_size=file_size,
            file_path=file_path,
            status="uploaded",
        )

        # Save metadata to the database
        document = save_document_metadata(db, user.id, document_metadata)
        return DocumentResponse(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_size=document.file_size,
            file_path=document.file_path,
            status=document.status,
            created_at=document.created_at.isoformat(),
            processed_at=document.processed_at.isoformat() if document.processed_at else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload document.")

@router.get("/", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to list all documents for the authenticated user.
    """
    try:
        documents = db.query(Document).filter(Document.user_id == user.id).all()
        return [
            DocumentResponse(
                id=doc.id,
                user_id=doc.user_id,
                filename=doc.filename,
                file_size=doc.file_size,
                file_path=doc.file_path,
                status=doc.status,
                created_at=doc.created_at.isoformat(),
                processed_at=doc.processed_at.isoformat() if doc.processed_at else None,
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.")

@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve a specific document by ID for the authenticated user.
    """
    try:
        document = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        return DocumentResponse(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_size=document.file_size,
            file_path=document.file_path,
            status=document.status,
            created_at=document.created_at.isoformat(),
            processed_at=document.processed_at.isoformat() if document.processed_at else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve document.")

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to delete a specific document by ID for the authenticated user.
    """
    try:
        document = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        db.delete(document)
        db.commit()
        return {"detail": "Document deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete document.")