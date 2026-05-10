"""Parse PDF and plain-text buffers into page objects."""

from io import BytesIO

from pypdf import PdfReader


def parse_pdf(buffer: bytes) -> list[dict]:
    """Parse a PDF buffer into a list of dicts with keys pageNumber, text (1-based pages)."""
    reader = PdfReader(BytesIO(buffer))
    page_texts: list[dict] = []
    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text()
        text = raw if raw else ""
        page_texts.append({"pageNumber": i, "text": text})
    if not page_texts:
        return [{"pageNumber": 1, "text": ""}]
    return page_texts


def parse_txt(buffer: bytes) -> list[dict]:
    """Parse a plain-text buffer as a single page."""
    return [{"pageNumber": 1, "text": buffer.decode("utf-8")}]
