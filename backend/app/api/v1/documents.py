# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, UploadFile, File
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
)
from app.services.document_service import DocumentService
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document (PDF, DOCX, or TXT)."""
    service = DocumentService(db)
    document = await service.upload_document(file, current_user)
    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the current user."""
    service = DocumentService(db)
    documents = await service.get_documents(current_user)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document by ID."""
    service = DocumentService(db)
    document = await service.get_document(document_id, current_user)
    return document


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its associated data."""
    service = DocumentService(db)
    await service.delete_document(document_id, current_user)
    return DocumentDeleteResponse(
        message="Document deleted successfully",
        document_id=document_id,
    )
