from fastapi import FastAPI

from app.database import Base, engine
from app.models import Artifact, Project
from app.routers.artifacts import router as artifacts_router
from app.routers.projects import router as projects_router
from app.routers.versions import router as versions_router

from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Artifact Service",
    description="Módulo de ingestão e organização de artefatos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(artifacts_router)
app.include_router(versions_router)

@app.get("/")
def root():
    return {
        "message": "Artifact Service is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }