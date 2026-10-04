"""ChromaDB vector store operations."""

from typing import List, Dict, Optional
# pyrefly: ignore [missing-import]
import chromadb
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Manages ChromaDB operations for storing and retrieving document vectors."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB collection '{self.collection_name}' ready "
            f"({self.collection.count()} vectors)"
        )

    def add_chunks(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
    ) -> None:
        """Store chunks with their embeddings in ChromaDB."""
        if not chunks:
            return

        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"].copy() for chunk in chunks]

        # ChromaDB metadata values must be str, int, float, or bool
        for meta in metadatas:
            meta["user_id"] = int(meta["user_id"])
            meta["document_id"] = int(meta["document_id"])
            meta["page"] = int(meta["page"])
            meta["chunk_index"] = int(meta["chunk_index"])

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} vectors to ChromaDB")

    def search(
        self,
        query_embedding: List[float],
        user_id: int,
        top_k: Optional[int] = None,
        document_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """
        Search for similar chunks, filtered by user_id.

        Returns list of dicts with: text, metadata, distance
        """
        top_k = top_k or settings.TOP_K_RESULTS

        # Build where filter
        where_filter = {"user_id": user_id}
        if document_ids:
            if len(document_ids) == 1:
                where_filter = {
                    "$and": [
                        {"user_id": user_id},
                        {"document_id": document_ids[0]},
                    ]
                }
            else:
                where_filter = {
                    "$and": [
                        {"user_id": user_id},
                        {"document_id": {"$in": document_ids}},
                    ]
                }

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })

        logger.info(f"Search returned {len(formatted)} results for user {user_id}")
        return formatted

    def delete_document_vectors(self, document_id: int) -> None:
        """Delete all vectors for a specific document."""
        self.collection.delete(where={"document_id": document_id})
        logger.info(f"Deleted vectors for document {document_id}")

    def get_document_chunk_count(self, document_id: int) -> int:
        """Get the number of chunks stored for a document."""
        results = self.collection.get(
            where={"document_id": document_id},
            include=[],
        )
        return len(results["ids"]) if results["ids"] else 0
