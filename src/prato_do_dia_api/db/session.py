from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from prato_do_dia_api.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
database_url = settings.database_url

# Resolve caminhos relativos do SQLite para caminhos absolutos relativos à raiz do projeto
if database_url.startswith("sqlite:///./"):
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    db_relative_path = database_url.replace("sqlite:///./", "")
    db_absolute_path = (project_root / db_relative_path).resolve()
    # Garante que o diretório pai (data/) exista
    db_absolute_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{db_absolute_path}"

parsed_database_url = make_url(database_url)

connect_args: dict[str, object] = {}
if parsed_database_url.drivername.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all database tables automatically if they do not exist."""
    from prato_do_dia_api.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
