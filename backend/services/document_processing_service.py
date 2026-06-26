import os
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader
from openai import OpenAI
from database.models import Document, DocumentChunk
from database.config import get_db

class DocumentProcessingService:
    def __init__(self, db: Session):
        self.db = db

    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

    def split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        tokens = text.split()
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk = " ".join(tokens[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def generate_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
            openai_client = OpenAI(api_key=openai_api_key)
            embeddings = []
            for chunk in text_chunks:
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk
                )
                embeddings.append(response["data"][0]["embedding"])
            return embeddings
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

    def create_document_chunks(self, document_id: uuid.UUID, text_chunks: List[str], embeddings: List[List[float]]) -> None:
        try:
            for index, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
                document_chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                    metadata={},
                    created_at=datetime.utcnow()
                )
                self.db.add(document_chunk)
            self.db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create document chunks: {str(e)}")

    def process_document(self, document_id: uuid.UUID) -> None:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")

        text = self.extract_text_from_pdf(document.file_path)
        text_chunks = self.split_text_into_chunks(text)
        embeddings = self.generate_embeddings(text_chunks)
        self.create_document_chunks(document_id, text_chunks, embeddings)

        document.status = "processed"
        document.processed_at = datetime.utcnow()
        self.db.commit()

    def create_document(self, user_id: uuid.UUID, filename: str, file_size: int, file_path: str) -> Document:
        try:
            document = Document(
                id=uuid.uuid4(),
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                file_path=file_path,
                status="uploaded",
                created_at=datetime.utcnow(),
                processed_at=None
            )
            self.db.add(document)
            self.db.commit()
            return document
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

    def get_document_by_id(self, document_id: uuid.UUID) -> Document:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    def list_all_documents(self, user_id: uuid.UUID) -> List[Document]:
        documents = self.db.query(Document).filter(Document.user_id == user_id).all()
        return documents

    def update_document(self, document_id: uuid.UUID, status: Optional[str] = None) -> Document:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if status:
            document.status = status
        document.updated_at = datetime.utcnow()
        self.db.commit()
        return document

    def delete_document(self, document_id: uuid.UUID) -> None:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        self.db.delete(document)
        self.db.commit()