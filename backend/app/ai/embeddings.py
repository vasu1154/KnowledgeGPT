"""Generate embeddings using Gemini API."""

from typing import List, Optional
# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Generates text embeddings using Gemini."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = GoogleGenerativeAIEmbeddings(
                model=self.model_name,
                google_api_key=self.api_key,
            )
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = self.model.embed_documents(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.model.embed_query(text)
