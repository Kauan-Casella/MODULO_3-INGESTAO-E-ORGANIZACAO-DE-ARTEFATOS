from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisResponse(BaseModel):
    id: int
    artifact_version_id: int

    status: str

    classification: str | None = None
    confidence: float | None = None
    classification_reason: str | None = None
    classification_evidence: list | None = None

    extracted_metadata: dict | None = None
    summary: str | None = None
    architecture: dict | None = None

    provider: str
    model_name: str

    error_message: str | None = None

    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)