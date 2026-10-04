from typing import List, Dict, Optional

try:
    # pyrefly: ignore [missing-import]
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    # pyrefly: ignore [missing-import]
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentChunker:
    """Splits document text into overlapping chunks with metadata."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(
        self,
        pages: List[Dict],
        document_id: int,
        user_id: int,
        filename: str,
    ) -> List[Dict]:
        """
        Split pages into chunks with metadata.

        Returns list of dicts with:
            - chunk_id: str (e.g., "doc123_chunk0")
            - text: str
            - metadata: dict
        """
        chunks = []
        chunk_index = 0

        for page in pages:
            page_chunks = self.splitter.split_text(page["text"])

            for chunk_text in page_chunks:
                chunk_id = f"doc{document_id}_chunk{chunk_index}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "user_id": user_id,
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "page": page["page_number"],
                        "filename": filename,
                        "chunk_index": chunk_index,
                    },
                })
                chunk_index += 1

        logger.info(
            f"Document {document_id}: {len(pages)} pages → {len(chunks)} chunks "
            f"(size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks
