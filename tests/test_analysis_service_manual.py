from app.database import SessionLocal
from app.services.analysis_service import analyze_artifact_version


# Informe o ID de uma versão existente no banco.
ARTIFACT_VERSION_ID = 1


db = SessionLocal()

try:
    analysis = analyze_artifact_version(
        db=db,
        artifact_version_id=ARTIFACT_VERSION_ID,
    )

    print("\nResultado da análise")
    print("--------------------")
    print(f"ID: {analysis.id}")
    print(f"Versão: {analysis.artifact_version_id}")
    print(f"Status: {analysis.status}")
    print(f"Classificação: {analysis.classification}")
    print(f"Confiança: {analysis.confidence}")
    print(f"Justificativa: {analysis.classification_reason}")
    print(f"Evidências: {analysis.classification_evidence}")
    print(f"Erro: {analysis.error_message}")

finally:
    db.close()
