from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ArtifactAnalysis(Base):
    __tablename__ = "artifact_analyses"

    __table_args__ = (
        Index(
            "ix_artifact_analyses_version_created",
            "artifact_version_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    artifact_version_id: Mapped[int] = mapped_column(
        ForeignKey("artifact_versions.id"),
        nullable=False,
        index=True,
    )

    # PENDING, PROCESSING, COMPLETED ou FAILED
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )

    # Ex.: requirements_specification, user_story, diagram
    classification: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    classification_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    classification_evidence: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Resultado da extração de metadados
    extracted_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Resumo produzido pela IA
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Informações estruturadas sobre a arquitetura identificada
    architecture: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Identificação do provedor e do modelo utilizado
    provider: Mapped[str] = mapped_column(
        String(50),
        default="groq",
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
