from pathlib import Path
from typing import Optional
from uuid import uuid4
import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import Artifact, ArtifactVersion, Project
from app.schemas.artifact import ArtifactResponse


logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

STORAGE_DIR = Path("storage")

ALLOWED_TYPES = {
    "application/pdf": "PDF",
    "text/markdown": "MARKDOWN",
    "image/png": "PNG",
    "image/jpeg": "JPEG",
}

ALLOWED_ARTIFACT_TYPES = set(ALLOWED_TYPES.values())

router = APIRouter(
    prefix="/projects/{project_id}/artifacts",
    tags=["Artifacts"],
)


def cleanup_saved_file(saved_path: Path | None):
    if saved_path is not None:
        try:
            saved_path.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Could not remove temporary file: %s",
                saved_path,
            )


# Upload de artefatos
@router.post("/", response_model=ArtifactResponse)
async def upload_artifact(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    saved_path = None

    try:
        # 1. Verifica se o projeto existe
        project = db.get(Project, project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Projeto não encontrado",
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
        artifact_type = ALLOWED_TYPES.get(file.content_type)

        if artifact_type is None:
            raise HTTPException(
                status_code=400,
                detail="Tipo de arquivo inválido",
            )

        # 4. Lê o arquivo respeitando o limite de tamanho
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

        # 5. Gera um nome interno único
        extension = Path(original_name).suffix.lower()
        stored_name = f"{uuid4().hex}{extension}"

        project_dir = STORAGE_DIR / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        saved_path = project_dir / stored_name
        saved_path.write_bytes(file_content)

        # 6. Cria o artefato
        artifact = Artifact(
            project_id=project_id,
            name=original_name,
            artifact_type=artifact_type,
            file_path=str(saved_path),
            version=1,
        )

        db.add(artifact)
        db.flush()

        # 7. Cria a versão inicial
        version = ArtifactVersion(
            artifact_id=artifact.id,
            version_number=1,
            file_path=str(saved_path),
        )

        db.add(version)

        # 8. Salva os registros na mesma transação
        db.commit()
        db.refresh(artifact)

        return artifact

    except HTTPException:
        db.rollback()
        cleanup_saved_file(saved_path)
        raise

    except OSError:
        db.rollback()
        cleanup_saved_file(saved_path)

        raise HTTPException(
            status_code=500,
            detail="Não foi possível acessar ou salvar o arquivo",
        )

    except SQLAlchemyError:
        db.rollback()
        cleanup_saved_file(saved_path)
        raise

    finally:
        await file.close()


# Lista artefatos com busca e filtros
@router.get("/")
def list_artifacts(
    project_id: int,
    search: Optional[str] = Query(
        default=None,
        description="Pesquisar artefatos por nome",
    ),
    artifact_type: Optional[str] = Query(
        default=None,
        description="Filtrar por PDF, MARKDOWN, PNG ou JPEG",
    ),
    db: Session = Depends(get_db),
):
    try:
        # 1. Verifica se o projeto existe
        project = db.get(Project, project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Projeto não encontrado",
            )

        # 2. Inicia a consulta
        query = db.query(Artifact).filter(
            Artifact.project_id == project_id
        )

        # 3. Aplica a busca pelo nome
        if search and search.strip():
            search_term = search.strip()

            query = query.filter(
                Artifact.name.ilike(f"%{search_term}%")
            )

        # 4. Aplica o filtro pelo tipo
        if artifact_type and artifact_type.strip():
            selected_type = artifact_type.strip().upper()

            if selected_type not in ALLOWED_ARTIFACT_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail="Tipo inválido. Use PDF, MARKDOWN, PNG ou JPEG.",
                )

            query = query.filter(
                Artifact.artifact_type == selected_type
            )

        return query.all()

    except SQLAlchemyError:
        db.rollback()
        raise


# Download de artefatos
@router.get("/{artifact_id}/download")
def download_artifact(
    project_id: int,
    artifact_id: int,
    db: Session = Depends(get_db),
):
    try:
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

        file_path = Path(artifact.file_path)

        if not file_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Arquivo do artefato não encontrado",
            )

        return FileResponse(
            path=file_path,
            filename=artifact.name,
        )

    except HTTPException:
        raise

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível acessar o artefato",
        )

    except SQLAlchemyError:
        db.rollback()
        raise
