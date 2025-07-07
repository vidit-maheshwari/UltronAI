# Agents/document_reader_agent.py

from agno.utils.log import log_info
from pathlib import Path
from typing import Dict, Any
import pypdf # Import the new library

class DocumentReaderAgent:
    """
    A deterministic agent responsible for reading the content of various file types.
    """
    def __init__(self):
        log_info("Initialized deterministic DocumentReaderAgent.")

    def _read_pdf(self, file_path: Path) -> str:
        """Reads and extracts all text from a PDF file."""
        try:
            log_info(f"Reading PDF file at: {file_path}")
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text_content = ""
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            log_info(f"Successfully extracted {len(text_content)} characters from PDF.")
            return text_content
        except Exception as e:
            log_info(f"Error reading PDF file: {e}")
            return f"Error: Could not read PDF file at {file_path}. Reason: {e}"

    def run(self, file_path_str: str) -> Dict[str, Any]:
        """
        Reads a file and returns its content. Currently supports PDF.
        """
        file_path = Path(file_path_str)
        if not file_path.exists():
            return {"status": "error", "error": f"File not found at path: {file_path}"}

        if file_path.suffix.lower() == '.pdf':
            content = self._read_pdf(file_path)
        else:
            # For now, we only support PDF, but this can be extended
            return {"status": "error", "error": f"Unsupported file type: {file_path.suffix}"}

        if "Error:" in content:
             return {"status": "error", "error": content}

        return {
            "status": "success",
            "output": f"Successfully read content from {file_path.name}.",
            "file_content": content
        }