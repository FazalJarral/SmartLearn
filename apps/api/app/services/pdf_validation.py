from dataclasses import dataclass

from app.core.errors import ApiError

PDF_MAGIC = b"%PDF-"


@dataclass(frozen=True)
class PdfValidationResult:
    filename: str
    size_bytes: int


def validate_pdf_upload(filename: str, content_type: str | None, data: bytes, max_bytes: int) -> PdfValidationResult:
    safe_name = filename.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    if not safe_name.lower().endswith(".pdf"):
        raise ApiError("invalid_file_extension", "Upload a file with a .pdf extension.", 415)
    if content_type not in {"application/pdf", "application/x-pdf", None, ""}:
        raise ApiError("invalid_mime_type", "Upload a PDF file.", 415)
    if len(data) > max_bytes:
        raise ApiError("file_too_large", "The PDF exceeds the configured upload size limit.", 413)
    if not data.startswith(PDF_MAGIC):
        raise ApiError("invalid_pdf_signature", "The file does not appear to be a valid PDF.", 415)
    return PdfValidationResult(filename=safe_name, size_bytes=len(data))
