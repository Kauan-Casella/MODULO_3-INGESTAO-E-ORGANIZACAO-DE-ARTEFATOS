import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://artifact_user:artifact_password@localhost:5432/artifact_db",
)

# Em produção deixe SQL_ECHO ausente ou "false" para não encher os logs.
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"


engine = create_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
