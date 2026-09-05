import pymupdf
import pytest

from app.core.errors import ApiError
from app.services.pdf_extraction import extract_text_from_pdf


def make_pdf(text: str, pages: int = 1) -> bytes:
    document = pymupdf.open()
    for _ in range(pages):
        page = document.new_page()
        page.insert_textbox((72, 72, 520, 760), text)
    data = document.tobytes()
    document.close()
    return data


def test_extracts_page_aware_text():
    data = make_pdf("Photosynthesis converts light energy into chemical energy. " * 30)
    extracted = extract_text_from_pdf(data, max_pages=20, max_chars=5000)
    assert extracted.page_count == 1
    assert "[Page 1]" in extracted.combined_text
    assert "Photosynthesis" in extracted.combined_text


def test_rejects_too_many_pages():
    data = make_pdf("Meaningful text " * 20, pages=2)
    with pytest.raises(ApiError) as exc:
        extract_text_from_pdf(data, max_pages=1, max_chars=5000)
    assert exc.value.code == "too_many_pages"


def test_rejects_image_only_or_tiny_text():
    data = make_pdf("tiny")
    with pytest.raises(ApiError) as exc:
        extract_text_from_pdf(data, max_pages=20, max_chars=5000)
    assert exc.value.code == "no_extractable_text"
