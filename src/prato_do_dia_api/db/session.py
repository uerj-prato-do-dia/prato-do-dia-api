from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from prato_do_dia_api.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
database_url = settings.database_url
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

