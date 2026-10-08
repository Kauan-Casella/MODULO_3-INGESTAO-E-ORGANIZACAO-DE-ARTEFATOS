from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artifact, ArtifactVersion, Project
from app.schemas.artifact import ArtifactResponse


router = APIRouter(
    prefix="/projects/{project_id}/artifacts",
    tags=["Artifacts"],
)


STORAGE_DIR = Path("storage")


ALLOWED_TYPES = {
    "application/pdf": "PDF",
    "text/markdown": "MARKDOWN",
    "image/png": "PNG",
    "image/jpeg": "JPEG",
}


@router.post(
    "/",
    response_model=ArtifactResponse,
)
async def upload_artifact(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    # verifica se projeto existe
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # verifica tipo de arquivo
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type",
        )

    # cria diretorio de armazenamento do projeto
    project_dir = STORAGE_DIR / str(project_id)
    project_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # salva arquivo
    file_path = project_dir / file.filename

    file_content = await file.read()

    file_path.write_bytes(file_content)

    # salva metadados
    artifact = Artifact(
        project_id=project_id,
        name=file.filename,
        artifact_type=ALLOWED_TYPES[file.content_type],
        file_path=str(file_path),
        version=1,
    )

    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    version = ArtifactVersion(
        artifact_id=artifact.id,
        version_number=1,
        file_path=str(file_path),
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return artifact

# lista artefatos
@router.get("/")
def list_artifacts(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    artifacts = (
        db.query(Artifact)
        .filter(Artifact.project_id == project_id)
        .all()
    )

    return artifacts

#download de artefatos
@router.get("/{artifact_id}/download")
def download_artifact(
    project_id: int,
    artifact_id: int,
    db: Session = Depends(get_db),
):
    artifact = (
        db.query(Artifact)
        .filter(
            Artifact.id == artifact_id,
            Artifact.project_id == project_id,
        )
        .first()
    )

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found",
        )

    file_path = Path(artifact.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return FileResponse(
        path=file_path,
        filename=artifact.name,
    )

