from pathlib import Path
from uuid import uuid4
import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import Artifact, ArtifactVersion


logger = logging.getLogger(__name__)

STORAGE_DIR = Path("storage")

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

ALLOWED_TYPES = {
    "application/pdf": "PDF",
    "text/markdown": "MARKDOWN",
    "image/png": "PNG",
    "image/jpeg": "JPEG",
}


router = APIRouter(
    prefix="/projects/{project_id}/artifacts",
    tags=["Versions"],
)


def cleanup_saved_file(saved_path: Path | None):
    if saved_path is not None:
        try:
            saved_path.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Could not remove temporary version file: %s",
                saved_path,
            )


# Criar uma nova versão
@router.post("/{artifact_id}/versions")
async def create_version(
    project_id: int,
    artifact_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    saved_path = None

    try:
        # 1. Verifica se o artefato existe
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
                detail="Artefato não encontrado",
            )

        # 2. Valida o nome do arquivo
        original_name = (file.filename or "").replace("\\", "/")
        original_name = Path(original_name).name.strip()

        if not original_name or original_name in {".", ".."}:
            raise HTTPException(
                status_code=400,
                detail="Nome de arquivo inválido",
            )

        # 3. Valida o tipo de arquivo
        uploaded_type = ALLOWED_TYPES.get(file.content_type)

        if uploaded_type is None:
            raise HTTPException(
                status_code=400,
                detail="Tipo de arquivo inválido",
            )

        if uploaded_type != artifact.artifact_type:
            raise HTTPException(
                status_code=400,
                detail="O tipo do arquivo deve ser igual ao do artefato original",
            )

        # 4. Lê o arquivo respeitando o limite
        file_content = await file.read(MAX_FILE_SIZE + 1)

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="O arquivo não pode estar vazio",
            )

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="O arquivo excedeu o limite de 20 MB",
            )

        # 5. Consulta a última versão
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

        # 6. Calcula o próximo número
        if latest_version:
            new_version_number = latest_version.version_number + 1
        else:
            new_version_number = 1

        # 7. Cria diretório para o artefato
        artifact_dir = (
            STORAGE_DIR
            / str(project_id)
            / str(artifact_id)
        )

        artifact_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 8. Gera nome interno único
        extension = Path(original_name).suffix.lower()

        stored_name = (
            f"v{new_version_number}_{uuid4().hex}{extension}"
        )

        saved_path = artifact_dir / stored_name

        saved_path.write_bytes(file_content)

        # 9. Cria registro da versão
        version = ArtifactVersion(
            artifact_id=artifact_id,
            version_number=new_version_number,
            file_path=str(saved_path),
        )

        artifact.version = new_version_number
        artifact.file_path = str(saved_path)

        db.add(version)

        # 10. Salva as alterações
        db.commit()
        db.refresh(version)

        return version

    except HTTPException:
        db.rollback()
        cleanup_saved_file(saved_path)
        raise

    except OSError:
        db.rollback()
        cleanup_saved_file(saved_path)

        raise HTTPException(
            status_code=500,
            detail="Não foi possível salvar ou acessar o arquivo",
        )

    except SQLAlchemyError:
        db.rollback()
        cleanup_saved_file(saved_path)
        raise

    finally:
        await file.close()


# Consultar histórico de versões
@router.get("/{artifact_id}/versions")
def list_versions(
    project_id: int,
    artifact_id: int,
    db: Session = Depends(get_db),
):
    try:
        # 1. Verifica se o artefato existe
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
                detail="Artefato não encontrado",
            )

        # 2. Consulta o histórico
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

    except SQLAlchemyError:
        db.rollback()
        raise
