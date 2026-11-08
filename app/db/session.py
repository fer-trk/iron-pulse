from sqlmodel import Session, create_engine
from app.core.config import settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.get_database_url(),
            echo=settings.DEBUG,
            hide_parameters=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session():
    """
    Dependencia FastAPI. Uso:
        session: Session = Depends(get_session)
    """
    with Session(get_engine()) as session:
        yield session
