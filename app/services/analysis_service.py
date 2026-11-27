import os
import logging

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.version import ArtifactVersion
from app.models.artifact_analysis import ArtifactAnalysis

from app.services.pdf_extraction_service import (
    extract_text_from_pdf,
    PDFExtractionError,
)

from app.services.classification_service import (
    classify_document,
    ClassificationError,
)

from app.services.enrichment_service import enrich_document

logger = logging.getLogger(__name__)


class DocumentExtractionError(Exception):
    """Erro durante a extração do conteúdo de um documento."""


def extract_document_text(file_path: str) -> str:
    """
    Extrai texto de documentos PDF e Markdown.
    """

    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise DocumentExtractionError(
            f"Arquivo não encontrado: {path}"
        )

    extension = path.suffix.lower()

    try:
        if extension == ".pdf":
            return extract_text_from_pdf(path)

        elif extension in (".md", ".markdown"):
            content = path.read_text(encoding="utf-8")

            if not content.strip():
                raise DocumentExtractionError(
                    "O documento Markdown está vazio."
                )

            return content

        else:
            raise DocumentExtractionError(
                f"Formato não suportado para análise: {extension}"
            )

    except UnicodeDecodeError as error:
        raise DocumentExtractionError(
            "Não foi possível interpretar o arquivo como UTF-8."
        ) from error

    except PDFExtractionError as error:
        raise DocumentExtractionError(str(error)) from error


def analyze_artifact_version(
    db: Session,
    artifact_version_id: int,
) -> ArtifactAnalysis:
    """
    Executa a análise de uma versão de artefato e
    persiste o resultado no banco de dados.
    """

    artifact_version = (
        db.query(ArtifactVersion)
        .filter(
            ArtifactVersion.id == artifact_version_id
        )
        .first()
    )

    if artifact_version is None:
        raise ValueError(
            f"Versão de artefato {artifact_version_id} não encontrada."
        )

    analysis = ArtifactAnalysis(
        artifact_version_id=artifact_version.id,
        status="PENDING",
        provider="groq",
        model_name=os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3.8-27b",
        ),
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    try:
        analysis.status = "PROCESSING"
        db.commit()

        document_text = extract_document_text(
            artifact_version.file_path
        )

        classification = classify_document(document_text)

        analysis.classification = classification["category"]
        analysis.confidence = classification["confidence"]
        analysis.classification_reason = classification["reason"]
        analysis.classification_evidence = classification["evidence"]


        enrichment = enrich_document(document_text)
        analysis.summary = enrichment["summary"]
        analysis.architecture = enrichment["architecture"]
        analysis.extracted_metadata = enrichment["extracted_metadata"]

        analysis.status = "COMPLETED"
        analysis.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(analysis)

        return analysis

    except (
        DocumentExtractionError,
        ClassificationError,
    ) as error:

        db.rollback()

        analysis = db.query(ArtifactAnalysis).filter(
            ArtifactAnalysis.id == analysis.id
        ).first()

        if analysis is None:
            raise RuntimeError(
                "Não foi possível recuperar o registro da análise."
            ) from error

        analysis.status = "FAILED"
        analysis.error_message = str(error)
        analysis.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(analysis)

        logger.warning(
            "Análise %s falhou: %s",
            analysis.id,
            error,
        )

        return analysis

    except Exception as error:

        db.rollback()

        analysis = db.query(ArtifactAnalysis).filter(
            ArtifactAnalysis.id == analysis.id
        ).first()

        if analysis is None:
            raise RuntimeError(
                "Não foi possível recuperar o registro da análise."
            ) from error

        analysis.status = "FAILED"
        analysis.error_message = (
            "Erro inesperado durante o processamento."
        )
        analysis.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(analysis)

        logger.exception(
            "Erro inesperado na análise %s.",
            analysis.id,
        )

        return analysis
