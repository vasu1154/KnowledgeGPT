"""Clean extracted text for better chunking and embedding quality."""

import re
from typing import List, Dict
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """Cleans raw extracted text."""

    def clean(self, pages: List[Dict]) -> List[Dict]:
        """Clean text from all pages."""
        cleaned = []
        for page in pages:
            clean_text = self._clean_text(page["text"])
            if clean_text.strip():
                cleaned.append({
                    "page_number": page["page_number"],
                    "text": clean_text,
                })
        logger.info(f"Cleaned {len(cleaned)} pages (from {len(pages)} raw)")
        return cleaned

    def _clean_text(self, text: str) -> str:
        """Apply cleaning rules to text."""
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove excessive spaces
        text = re.sub(r" {3,}", " ", text)
        # Remove non-printable characters (keep newlines and tabs)
        text = re.sub(r"[^\S\n\t]+", " ", text)
        # Strip each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        return text.strip()
