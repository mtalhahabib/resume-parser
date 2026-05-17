"""
pdf_extractor.py
Extract raw text from PDF and DOCX files.
Uses pdfplumber (better than pypdf for layout) and python-docx.
"""

import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using pdfplumber.
    Handles multi-column layouts better than basic extractors.
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

    text_parts = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Try bounding-box based extraction first (better for multi-column)
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if page_text:
                text_parts.append(page_text)

    full_text = "\n".join(text_parts)

    # Basic cleanup
    full_text = "\n".join(
        line for line in full_text.splitlines()
        if line.strip()
    )

    return full_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX bytes using python-docx.
    """
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)
