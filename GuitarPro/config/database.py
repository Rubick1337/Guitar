import os
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv

# Находим корень проекта (папка Guitar)
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

# Явно загружаем .env из корня проекта
load_dotenv(dotenv_path=ENV_PATH)

Base = declarative_base()


def create_database_connection() -> Tuple[Optional["Engine"], Optional[sessionmaker]]:
    """Создает и возвращает подключение к базе данных."""
    db_name = os.getenv("DB_NAME", "guitarpro")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "170573")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    print(f"DB_USER raw = {db_user!r}")
    print(f"DB_PASSWORD raw = {db_password!r}")
    print(f"DB_NAME raw = {db_name!r}")

    database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    safe_url = f"postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}"
    print(f"🔗 Подключаемся к: {safe_url!r}")

    try:
        engine = create_engine(
            database_url,
            echo=True,
            future=True,
            connect_args={"options": "-c client_encoding=utf8"},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("✅ Подключение к PostgreSQL установлено")

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, SessionLocal

    except SQLAlchemyError as e:
        print(f"❌ Ошибка подключения к БД: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка подключения к БД: {e!r}")

    return None, None
