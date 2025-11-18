import os
import io
import re
from typing import Optional


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"\r\n?|\n|\u2028|\u2029", "\n", text)
    text = text.replace("\t", "  ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf(path: str) -> str:
    try:
        import pdfminer.high_level  # type: ignore
    except Exception as e:
        raise RuntimeError(f"pdfminer not available: {e}")

    try:
        with open(path, "rb") as f:
            output: io.StringIO = io.StringIO()
            pdfminer.high_level.extract_text_to_fp(f, output)
            return output.getvalue()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")


def _extract_docx(path: str) -> str:
    try:
        import docx  # python-docx
    except Exception as e:
        raise RuntimeError(f"python-docx not available: {e}")

    try:
        document = docx.Document(path)
        paragraphs = [p.text for p in document.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from DOCX: {e}")


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
            return _normalize_whitespace(raw)
    elif ext == ".pdf":
        raw = _extract_pdf(file_path)
        text = _normalize_whitespace(raw)
        if not text:
            raise RuntimeError("Failed to extract meaningful text. The document may be scanned or image-based.")
        return text
    elif ext == ".docx":
        raw = _extract_docx(file_path)
        text = _normalize_whitespace(raw)
        if not text:
            raise RuntimeError("Failed to extract meaningful text from DOCX.")
        return text
    elif ext == ".doc":
        raise RuntimeError(".doc files are not supported. Please convert to .docx or export as PDF.")
    else:
        raise RuntimeError(f"Unsupported file type: {ext}")


