from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artifact, ArtifactVersion


router = APIRouter(
    prefix="/projects/{project_id}/artifacts",
    tags=["Versions"],
)


STORAGE_DIR = Path("storage")


@router.post("/{artifact_id}/versions")
async def create_version(
    project_id: int,
    artifact_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Encontrar artefato
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

    # Encontra ultima versao
    latest_version = (
        db.query(ArtifactVersion)
        .filter(
            ArtifactVersion.artifact_id == artifact_id
        )
        .order_by(
            ArtifactVersion.version_number.desc()
        )
        .first()
    )

    # Calcula o numero da ultima versao
    if latest_version:
        new_version_number = latest_version.version_number + 1
    else:
        new_version_number = 1

    #Cria diretorio para artefato
    artifact_dir = (
        STORAGE_DIR
        / str(project_id)
        / str(artifact_id)
    )

    artifact_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Cria caminho do arquivo
    file_path = (
        artifact_dir
        / f"v{new_version_number}_{file.filename}"
    )

    #salva arquivo
    file_content = await file.read()
    file_path.write_bytes(file_content)

    #cria registro
    version = ArtifactVersion(
        artifact_id=artifact_id,
        version_number=new_version_number,
        file_path=str(file_path),
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return version

@router.get("/{artifact_id}/versions")
def list_versions(
    project_id: int,
    artifact_id: int,
    db: Session = Depends(get_db),
):
    # Verify that the artifact exists
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

    versions = (
        db.query(ArtifactVersion)
        .filter(
            ArtifactVersion.artifact_id == artifact_id
        )
        .order_by(
            ArtifactVersion.version_number.desc()
        )
        .all()
    )

    return versions
