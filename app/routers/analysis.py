from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.artifact_analysis import ArtifactAnalysis
from app.schemas.analysis import AnalysisResponse
from app.services.analysis_service import analyze_artifact_version


router = APIRouter(
    prefix="/analyses",
    tags=["Analyses"],
)


@router.post(
    "/versions/{version_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis(
    version_id: int,
    db: Session = Depends(get_db),
):
    """
    Executa uma análise de IA para uma versão de artefato.
    """

    try:
        analysis = analyze_artifact_version(
            db=db,
            artifact_version_id=version_id,
        )

        return analysis

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Consulta uma análise previamente armazenada.
    """

    analysis = (
        db.query(ArtifactAnalysis)
        .filter(ArtifactAnalysis.id == analysis_id)
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análise não encontrada.",
        )

    return analysis