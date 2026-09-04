"""
ResumeService — PDF/DOCX → structured text extraction.

Implemented in ST-05.
"""


class ResumeService:
    """
    Parses uploaded resume files into raw text and structured fields.
    Uses pdfplumber for PDF, python-docx for DOCX.
    Implemented in ST-05.
    """

    async def parse(self, file_path: str, mime_type: str) -> dict:
        raise NotImplementedError("ResumeService implemented in ST-05")
