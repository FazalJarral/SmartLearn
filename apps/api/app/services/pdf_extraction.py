from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

from app.core.errors import ApiError


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedDocument:
    page_count: int
    pages: list[ExtractedPage]

    @property
    def combined_text(self) -> str:
        return "\n\n".join(f"[Page {page.page_number}]\n{page.text}" for page in self.pages)


def normalize_text(value: str) -> str:
    collapsed = re.sub(r"[ \t\r\f\v]+", " ", value)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    return collapsed.strip()


def remove_repeated_headers_footers(page_texts: list[str]) -> list[str]:
    if len(page_texts) < 3:
        return page_texts
    first_lines = [text.splitlines()[0].strip() for text in page_texts if text.splitlines()]
    last_lines = [text.splitlines()[-1].strip() for text in page_texts if text.splitlines()]
    repeated = {
        line
        for line in set(first_lines + last_lines)
        if line and (first_lines + last_lines).count(line) >= 3 and len(line) <= 120
    }
    if not repeated:
        return page_texts
    cleaned: list[str] = []
    for text in page_texts:
        lines = [line for line in text.splitlines() if line.strip() not in repeated]
        cleaned.append("\n".join(lines).strip())
    return cleaned


def extract_text_from_pdf(data: bytes, max_pages: int, max_chars: int) -> ExtractedDocument:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF exposes several parse exceptions.
        raise ApiError("malformed_pdf", "The PDF is malformed or cannot be parsed.", 422) from exc

    try:
        if document.is_encrypted:
            raise ApiError("encrypted_pdf", "Password-protected PDFs are not supported.", 422)
        if document.page_count == 0:
            raise ApiError("empty_pdf", "The PDF has no pages.", 422)
        if document.page_count > max_pages:
            raise ApiError("too_many_pages", f"The PDF exceeds the {max_pages}-page limit.", 413)

        raw_pages = [normalize_text(page.get_text("text")) for page in document]
        cleaned_pages = remove_repeated_headers_footers(raw_pages)
        pages = [
            ExtractedPage(page_number=index, text=text)
            for index, text in enumerate(cleaned_pages, start=1)
            if text
        ]
        meaningful_chars = sum(len(page.text) for page in pages)
        if meaningful_chars < 200:
            raise ApiError(
                "no_extractable_text",
                "This PDF does not contain enough extractable text. Scanned or image-only PDFs are not supported.",
                422,
            )
        combined_chars = 0
        bounded_pages: list[ExtractedPage] = []
        for page in pages:
            remaining = max_chars - combined_chars
            if remaining <= 0:
                break
            bounded_text = page.text[:remaining]
            bounded_pages.append(ExtractedPage(page.page_number, bounded_text))
            combined_chars += len(bounded_text)
        return ExtractedDocument(page_count=document.page_count, pages=bounded_pages)
    finally:
        document.close()
