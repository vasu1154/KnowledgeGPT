"""Orchestrates the complete document processing pipeline."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, DocumentStatus
from app.document_processing.extractor import TextExtractor
from app.document_processing.cleaner import TextCleaner
from app.document_processing.chunker import DocumentChunker
from app.ai.embeddings import EmbeddingService
from app.ai.vector_store import VectorStoreService
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """
    Complete document processing pipeline:
    
    Upload → Extract → Clean → Chunk → Embed → Store in ChromaDB
    """

    def __init__(
        self,
        db: AsyncSession,
        extractor: Optional[TextExtractor] = None,
        cleaner: Optional[TextCleaner] = None,
        chunker: Optional[DocumentChunker] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStoreService] = None,
    ):
        self.db = db
        self.extractor = extractor or TextExtractor()
        self.cleaner = cleaner or TextCleaner()
        self.chunker = chunker or DocumentChunker()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    async def process_document(self, document_id: int) -> None:
        """Run the full processing pipeline for a document."""

        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        try:
            # Update status to PROCESSING
            document.status = DocumentStatus.PROCESSING
            await self.db.flush()

            logger.info(f"Processing document {document_id}: {document.original_filename}")

            # Step 1: Extract text
            logger.info(f"[{document_id}] Step 1/5: Extracting text...")
            pages = self.extractor.extract(
                document.storage_path, document.file_type
            )
            if not pages:
                raise ValueError("No text could be extracted from the document")

            document.page_count = len(pages)

            # Step 2: Clean text
            logger.info(f"[{document_id}] Step 2/5: Cleaning text...")
            cleaned_pages = self.cleaner.clean(pages)

            # Step 3: Chunk text
            logger.info(f"[{document_id}] Step 3/5: Chunking text...")
            chunks = self.chunker.chunk(
                pages=cleaned_pages,
                document_id=document.id,
                user_id=document.user_id,
                filename=document.original_filename,
            )

            if not chunks:
                raise ValueError("No chunks were generated from the document")

            document.chunk_count = len(chunks)

            # Step 4: Generate embeddings
            logger.info(f"[{document_id}] Step 4/5: Generating embeddings...")
            texts = [chunk["text"] for chunk in chunks]

            # Process in batches to avoid API limits
            batch_size = 100
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_embeddings = self.embedding_service.embed_texts(batch)
                all_embeddings.extend(batch_embeddings)

            # Step 5: Store in ChromaDB
            logger.info(f"[{document_id}] Step 5/5: Storing vectors...")
            self.vector_store.add_chunks(chunks, all_embeddings)

            # Update status to COMPLETED
            document.status = DocumentStatus.COMPLETED
            document.error_message = None
            await self.db.flush()

            logger.info(
                f"Document {document_id} processed successfully: "
                f"{document.page_count} pages, {document.chunk_count} chunks"
            )

        except Exception as e:
            # Update status to FAILED
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            document.retry_count += 1
            await self.db.flush()

            logger.error(
                f"Document {document_id} processing failed: {e}",
                exc_info=True,
            )
            raise
