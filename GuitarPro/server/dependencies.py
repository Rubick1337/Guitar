from typing import Generator, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config.database import Base, create_database_connection

_engine, _SessionLocal = create_database_connection()


def init_database() -> None:
    """Создает таблицы при старте приложения, если подключение доступно."""
    if _engine is None:
        raise RuntimeError("База данных недоступна. Проверьте переменные окружения подключения.")
    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency для получения SQLAlchemy-сессии."""
    if _SessionLocal is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="База данных не настроена")
    db: Optional[Session] = None
    try:
        db = _SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()
