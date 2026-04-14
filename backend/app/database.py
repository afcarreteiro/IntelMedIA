from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.session import Base


engine = create_engine(
    settings.database_url.replace("sqlite+aiosqlite", "sqlite"),
    echo=settings.debug,
    future=True,
)

session_maker = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = session_maker()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
