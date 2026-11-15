from pathlib import Path

import pymupdf
import pytest

from app.services.pdf_extraction_service import (
    extract_text_from_pdf,
    PDFExtractionError,
)


def test_extract_text_from_pdf(tmp_path):
    """Verifica se o texto de um PDF é extraído corretamente."""

    pdf_path = tmp_path / "document.pdf"

    document = pymupdf.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        "Artifact Service - Documento de teste"
    )

    document.save(pdf_path)
    document.close()

    extracted_text = extract_text_from_pdf(pdf_path)

    assert "Artifact Service" in extracted_text
    assert "Documento de teste" in extracted_text


def test_pdf_not_found():
    """Verifica o tratamento de arquivos inexistentes."""

    with pytest.raises(PDFExtractionError):
        extract_text_from_pdf("arquivo_inexistente.pdf")


def test_invalid_extension(tmp_path):
    """Verifica a rejeição de arquivos que não são PDFs."""

    file_path = tmp_path / "document.txt"
    file_path.write_text("Conteúdo de teste")

    with pytest.raises(PDFExtractionError):
        extract_text_from_pdf(file_path)
