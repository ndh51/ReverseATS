"""
Document Parsers Package (Pluggable).
Each parser extracts text from a specific file format (.pdf, .docx, .txt, .md).
Adding a new file format tomorrow only requires creating a class implementing `DocumentParserPlugin`
and registering it in `ParserRegistry`.
"""
import io
import os
from typing import Dict, List
from reverse_ats.core import DocumentParserPlugin


class PDFParserPlugin(DocumentParserPlugin):
    """Extracts text from PDF files using pypdf."""

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for idx, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_text.append(f"--- Page {idx + 1} ---\n{txt.strip()}")
        return "\n\n".join(pages_text).strip()


class DocxParserPlugin(DocumentParserPlugin):
    """Extracts text from Microsoft Word (.docx) files."""

    @property
    def supported_extensions(self) -> List[str]:
        return [".docx"]

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        import docx

        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        # Also extract text from tables if present
        for table in doc.tables:
            for row in table.rows:
                row_txt = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_txt:
                    paragraphs.append(row_txt)
        return "\n".join(paragraphs).strip()


class PlainTextParserPlugin(DocumentParserPlugin):
    """Extracts text from .txt, .md, .json, or .tex files."""

    @property
    def supported_extensions(self) -> List[str]:
        return [".txt", ".md", ".markdown", ".tex", ".json"]

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return file_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace").strip()


class ParserRegistry:
    """Registry that routes any file to the matching DocumentParserPlugin."""

    def __init__(self) -> None:
        self._parsers: Dict[str, DocumentParserPlugin] = {}

    def register(self, parser: DocumentParserPlugin) -> None:
        for ext in parser.supported_extensions:
            self._parsers[ext.lower()] = parser

    def supported_extensions(self) -> List[str]:
        return sorted(self._parsers.keys())

    def parse(self, file_bytes: bytes, filename: str) -> str:
        _, ext = os.path.splitext(filename.lower())
        parser = self._parsers.get(ext)
        if not parser:
            raise ValueError(
                f"Format '{ext}' non supporté. Formats acceptés : {', '.join(self.supported_extensions())}"
            )
        return parser.extract_text(file_bytes, filename)


def create_default_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PDFParserPlugin())
    registry.register(DocxParserPlugin())
    registry.register(PlainTextParserPlugin())
    return registry
