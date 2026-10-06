"""Document extraction, MIME sniffing, and in-memory text parsing."""

import io
import zipfile
from typing import Any, List, Optional, Tuple

import pypdf
import docx

from app.core.config import Settings, get_settings
from app.core.errors import AppException, PayloadTooLargeError
from app.core.logging import logger
from app.modules.extractor.llm_client import LLMClient
from app.modules.ingest.ocr import image_to_text, sniff_image_mime


def sniff_document_mime(data: bytes) -> Optional[str]:
    """Sniff magic bytes to verify PDF, DOCX, or supported image format in-memory."""
    if not data or len(data) < 4:
        return None

    # 1. PDF: %PDF-
    if data.startswith(b"%PDF"):
        return "application/pdf"

    # 2. DOCX: PK zip containing word/document.xml
    if data.startswith(b"PK\x03\x04") or data.startswith(b"PK\x05\x06"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if "word/document.xml" in zf.namelist():
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except Exception:
            pass

    # 3. Delegate to image magic byte sniffer
    img_mime = sniff_image_mime(data)
    if img_mime:
        return img_mime

    # 4. Text/plain check
    try:
        data.decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        try:
            data.decode("latin-1")
            return "text/plain"
        except Exception:
            return None


def infer_doc_type_from_text(text: str) -> str:
    """Infer high-level document type based on key domain keywords."""
    t_lower = text.lower()
    if any(k in t_lower for k in ("loan agreement", "borrower", "lender", "sanction letter", "emi", "interest rate", "repayment schedule")):
        return "loan_agreement"
    if any(k in t_lower for k in ("insurance", "policyholder", "premium", "coverage", "exclusion", "sum insured", "claim")):
        return "insurance_policy"
    if any(k in t_lower for k in ("rent agreement", "lease", "tenant", "landlord", "security deposit", "premises")):
        return "rental_agreement"
    if any(k in t_lower for k in ("terms and conditions", "terms of service", "privacy policy", "user agreement")):
        return "terms_of_service"
    if any(k in t_lower for k in ("employment agreement", "employee", "employer", "probation", "salary", "non-disclosure")):
        return "employment_contract"
    if any(k in t_lower for k in ("investment agreement", "shareholders agreement", "promissory note", "guarantee", "sebi", "portfolio")):
        return "investment_agreement"
    return "general_document"


async def extract_document_text(
    data: Optional[bytes] = None,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    plain_text: Optional[str] = None,
    settings: Optional[Settings] = None,
    client: Optional[LLMClient] = None,
) -> Tuple[str, str, str, List[str]]:
    """Extract and normalize document text in-memory.

    Guarantees:
    - Zero disk writes: all parsing operates directly on in-memory buffers (BytesIO).
    - Enforces EXPLAIN_MAX_MB, EXPLAIN_MAX_PAGES, and EXPLAIN_MAX_CHARS.
    - Rejects invalid or malicious MIME signatures with HTTP 422 standard envelope.
    - Gracefully records degradation flags ("truncated", "ocr_low_quality", "scanned_pdf_unsupported").

    Returns:
        (extracted_text, doc_type_guess, ocr_quality, degraded_flags)
    """
    conf = settings or get_settings()
    degraded: List[str] = []
    ocr_quality = "n/a"

    # Case A: Plain text input directly provided
    if plain_text and plain_text.strip():
        text = plain_text.strip()
        doc_type = infer_doc_type_from_text(text)
        if len(text) > conf.EXPLAIN_MAX_CHARS:
            text = text[: conf.EXPLAIN_MAX_CHARS]
            degraded.append("truncated")
        return text, doc_type, "n/a", degraded

    if not data:
        raise AppException(
            status_code=422,
            code="missing_document",
            message="No document content or text provided for explanation.",
        )

    # 1. Enforce payload size limit
    max_bytes = conf.EXPLAIN_MAX_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise PayloadTooLargeError(
            message=f"Document size ({len(data)} bytes) exceeds limit of {conf.EXPLAIN_MAX_MB}MB"
        )

    # 2. Sniff MIME type
    sniffed_mime = sniff_document_mime(data)
    effective_mime = sniffed_mime or (content_type.lower() if content_type else None)
    fn_lower = (filename or "").lower()

    extracted_text = ""

    # 3. PDF Ingestion
    if effective_mime == "application/pdf" or fn_lower.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise AppException(
                status_code=422,
                code="invalid_pdf_format",
                message="File claims to be PDF but header does not match genuine PDF signature.",
            )
        try:
            reader = pypdf.PdfReader(io.BytesIO(data), strict=False)
            num_pages = len(reader.pages)
            if num_pages > conf.EXPLAIN_MAX_PAGES:
                raise AppException(
                    status_code=422,
                    code="document_too_long",
                    message=f"Document has {num_pages} pages, which exceeds the limit of {conf.EXPLAIN_MAX_PAGES} pages.",
                )

            pages_text = []
            for idx, page in enumerate(reader.pages):
                p_text = page.extract_text() or ""
                if p_text.strip():
                    pages_text.append(p_text.strip())

            extracted_text = "\n\n".join(pages_text).strip()

            # Scanned PDF check: if PDF has pages but 0 extractable text
            if not extracted_text and num_pages > 0:
                logger.warning("Scanned PDF with no text layer detected.")
                degraded.append("scanned_pdf_unsupported")
                raise AppException(
                    status_code=422,
                    code="scanned_pdf_unsupported",
                    message="The uploaded PDF contains scanned images without a text layer. Please upload page images (.png/.jpg) or select a text PDF.",
                )

        except AppException:
            raise
        except Exception as exc:
            logger.error("Failed to parse PDF document in-memory: %s", exc)
            raise AppException(
                status_code=422,
                code="unsupported_document_type",
                message=f"Failed to read PDF document: {exc}",
            )

    # 4. DOCX Ingestion
    elif effective_mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or fn_lower.endswith(".docx"):
        try:
            doc = docx.Document(io.BytesIO(data))
            parts = []
            for p in doc.paragraphs:
                if p.text.strip():
                    parts.append(p.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_texts:
                        parts.append(" | ".join(row_texts))
            extracted_text = "\n\n".join(parts).strip()
        except Exception as exc:
            logger.error("Failed to parse DOCX document: %s", exc)
            raise AppException(
                status_code=422,
                code="unsupported_document_type",
                message="Invalid or corrupted DOCX file.",
            )

    # 5. Image OCR Ingestion
    elif effective_mime in ("image/png", "image/jpeg", "image/webp") or any(fn_lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")):
        ocr_res = await image_to_text(data, mime_hint=effective_mime, settings=conf, client=client)
        extracted_text = ocr_res.text
        ocr_quality = "good" if len(extracted_text) >= 100 else "low"
        if ocr_quality == "low":
            degraded.append("ocr_low_quality")

    # 6. Plain Text File Ingestion
    elif effective_mime == "text/plain" or fn_lower.endswith(".txt"):
        try:
            extracted_text = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            extracted_text = data.decode("latin-1", errors="replace").strip()

    else:
        raise AppException(
            status_code=422,
            code="unsupported_document_type",
            message="Unsupported document format. Allowed formats: PDF, DOCX, PNG, JPEG, WEBP, or TXT.",
        )

    if not extracted_text or len(extracted_text.strip()) < 10:
        raise AppException(
            status_code=422,
            code="not_enough_text",
            message="Could not extract sufficient text from the uploaded document.",
        )

    # Enforce character truncation
    if len(extracted_text) > conf.EXPLAIN_MAX_CHARS:
        extracted_text = extracted_text[: conf.EXPLAIN_MAX_CHARS]
        degraded.append("truncated")

    doc_type_guess = infer_doc_type_from_text(extracted_text)
    return extracted_text, doc_type_guess, ocr_quality, degraded
