import tempfile
from pathlib import Path

import pymupdf

from app.services.metadata_service import (
    analyze_document_metadata,
    MetadataAnalysisError,
)


def create_sample_pdf(file_path: Path):
    """Cria um PDF fictício para testar a análise."""

    document = pymupdf.open()
    page = document.new_page()

    page.insert_text(
        (72, 72),
        "Especificacao Tecnica - Artifact Service\n"
        "Autor: Equipe de Engenharia de Software\n"
        "Data: 15/11/2026\n\n"
        "Este documento descreve a arquitetura do Artifact Service.\n"
        "O sistema utiliza Python, FastAPI, PostgreSQL e Docker.\n"
        "Sua arquitetura segue o estilo de microsservicos.\n"
        "O modulo de ingestao permite upload e versionamento de PDFs.\n"
        "O sistema tambem utiliza inteligencia artificial para "
        "classificar documentos e gerar resumos tecnicos."
    )

    document.save(file_path)
    document.close()


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "artifact_specification.pdf"

        create_sample_pdf(pdf_path)

        print("PDF de teste criado.")
        print("Enviando documento para análise com Qwen...\n")

        try:
            result = analyze_document_metadata(pdf_path)

            print("ANÁLISE CONCLUÍDA!")
            print("=" * 55)

            print("\nMETADADOS IDENTIFICADOS:\n")

            for field, value in result["metadata"].items():
                print(f"{field}: {value}")

            print("\nTEXTO EXTRAÍDO:")
            print(result["extracted_text"])

            print(
                "\nTexto truncado para análise:",
                result["truncated_for_analysis"],
            )

        except MetadataAnalysisError as error:
            print(f"ERRO NA ANÁLISE: {error}")


if __name__ == "__main__":
    main()