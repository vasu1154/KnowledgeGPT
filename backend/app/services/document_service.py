import os
import uuid
import aiofiles
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.config import settings
from app.core.exceptions import (
    NotFoundError,
    FileTooLargeError,
    UnsupportedFileError,
    ForbiddenError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Handles document upload, retrieval, and deletion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _validate_file(self, file: UploadFile) -> str:
        """Validate file type and size."""
        if not file.filename:
            raise UnsupportedFileError("Filename is required")

        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in settings.allowed_extensions_list:
            raise UnsupportedFileError(
                f"File type '.{extension}' not supported. "
                f"Allowed: {settings.ALLOWED_EXTENSIONS}"
            )

        if file.size and file.size > settings.max_file_size_bytes:
            raise FileTooLargeError(
                f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )

        return extension

    async def _save_file(self, file: UploadFile, user_id: int) -> tuple[str, str, int]:
        """Save uploaded file to local storage. Returns (stored_filename, path, size)."""
        user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(user_dir, unique_name)

        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_file_size_bytes:
            raise FileTooLargeError(
                f"File size ({file_size} bytes) exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info(f"File saved: {file_path} ({file_size} bytes)")
        return unique_name, file_path, file_size

    async def upload_document(self, file: UploadFile, user: User) -> Document:
        """Upload and store a document."""
        file_type = self._validate_file(file)
        stored_name, file_path, file_size = await self._save_file(file, user.id)

        document = Document(
            user_id=user.id,
            filename=stored_name,
            original_filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=file_path,
            status=DocumentStatus.UPLOADED,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        logger.info(
            f"Document uploaded: id={document.id}, "
            f"user={user.id}, file={file.filename}"
        )

        return document

    async def get_documents(self, user: User) -> List[Document]:
        """Get all documents for a user."""
        result = await self.db.execute(
            select(Document)
            .where(Document.user_id == user.id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_document(self, document_id: int, user: User) -> Document:
        """Get a specific document (user-scoped)."""
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user.id,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise NotFoundError(f"Document with id {document_id} not found")
        return document

    async def delete_document(self, document_id: int, user: User) -> None:
        """Delete a document and its file."""
        document = await self.get_document(document_id, user)

        if os.path.exists(document.storage_path):
            try:
                os.remove(document.storage_path)
                logger.info(f"File deleted: {document.storage_path}")
            except OSError as e:
                logger.warning(f"Failed to delete file from disk: {e}")

        await self.db.delete(document)
        await self.db.flush()
        logger.info(f"Document deleted: id={document_id}, user={user.id}")

    async def get_document_count(self, user_id: Optional[int] = None) -> int:
        """Get total document count, optionally filtered by user."""
        query = select(func.count(Document.id))
        if user_id:
            query = query.where(Document.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar() or 0
