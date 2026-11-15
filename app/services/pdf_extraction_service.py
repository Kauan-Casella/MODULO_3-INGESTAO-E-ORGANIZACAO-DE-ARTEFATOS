from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Erro durante a extração de texto de um PDF."""


def extract_text_from_pdf(file_path: str | Path) -> str:
    """
    Extrai o texto de todas as páginas de um documento PDF.

    Args:
        file_path: Caminho do arquivo PDF.

    Returns:
        Texto extraído do documento.
    """

    path = Path(file_path)

    if not path.exists():
        raise PDFExtractionError(
            f"Arquivo PDF não encontrado: {path}"
        )

    if not path.is_file():
        raise PDFExtractionError(
            "O caminho informado não é um arquivo."
        )

    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError(
            "O arquivo informado não é um PDF."
        )

    try:
        extracted_pages = []

        with pymupdf.open(path) as document:

            if document.is_encrypted:
                raise PDFExtractionError(
                    "O PDF está protegido por senha."
                )

            for page_number, page in enumerate(document, start=1):

                page_text = page.get_text("text").strip()

                if page_text:
                    extracted_pages.append(
                        f"--- Página {page_number} ---\n"
                        f"{page_text}"
                    )

        extracted_text = "\n\n".join(extracted_pages)

        if not extracted_text.strip():
            raise PDFExtractionError(
                "Nenhum texto foi encontrado no PDF. "
                "O documento pode ser uma imagem digitalizada."
            )

        return extracted_text

    except PDFExtractionError:
        raise

    except Exception as error:
        raise PDFExtractionError(
            "Não foi possível processar o documento PDF."
        ) from error
