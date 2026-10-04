"""Extract text from PDF, DOCX, and TXT files."""

from typing import List, Dict
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextExtractor:
    """Extracts text from various document formats."""

    def extract(self, file_path: str, file_type: str) -> List[Dict]:
        """
        Extract text from a file.

        Returns a list of dicts with:
            - page_number: int
            - text: str
        """
        extractors = {
            "pdf": self._extract_pdf,
            "docx": self._extract_docx,
            "txt": self._extract_txt,
        }

        extractor = extractors.get(file_type.lower())
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")

        pages = extractor(file_path)
        logger.info(f"Extracted {len(pages)} pages from {file_path}")
        return pages

    def _extract_pdf(self, file_path: str) -> List[Dict]:
        """Extract text from PDF using PyMuPDF."""
        pages = []
        doc = fitz.open(file_path)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text.strip():
                    pages.append({
                        "page_number": page_num + 1,
                        "text": text,
                    })
        finally:
            doc.close()
        return pages

    def _extract_docx(self, file_path: str) -> List[Dict]:
        """Extract text from DOCX."""
        doc = DocxDocument(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        if full_text.strip():
            return [{"page_number": 1, "text": full_text}]
        return []

    def _extract_txt(self, file_path: str) -> List[Dict]:
        """Extract text from plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if text.strip():
            return [{"page_number": 1, "text": text}]
        return []
