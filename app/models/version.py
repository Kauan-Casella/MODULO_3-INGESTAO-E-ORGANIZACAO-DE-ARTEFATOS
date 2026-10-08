from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    artifact_id: Mapped[int] = mapped_column(
        ForeignKey("artifacts.id"),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )