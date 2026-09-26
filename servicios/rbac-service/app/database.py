import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# En Docker Compose, estas variables ya vienen del .env (RBAC_DB_USER, etc.)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://rbac_user:rbac_pass@rbac-db:5432/rbac_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre y cierra la sesión por cada request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
