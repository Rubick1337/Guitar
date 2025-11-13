from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import inspect, text
from typing import List, Optional, Tuple, Any

from GuitarPro.database.models import User, Chat, ChatMessage, MessageRole
from GuitarPro.config.database import create_database_connection, Base



class DatabaseHandler:
    def __init__(self):
        self.engine, self.SessionLocal = create_database_connection()
        if self.engine:
            self.create_tables()
        else:
            print("❌ Не удалось подключиться к БД")

    # --------------------------- БАЗОВОЕ ---------------------------

    def create_tables(self):
        """Создает таблицы если они не существуют."""
        if not self.engine:
            print("❌ Нет подключения к БД")
            return False

        try:
            # ВАЖНО: импортируй все модели до create_all
            # Если используешь модули, просто оставь импорт сверху
            print("🔄 Создаем таблицы...")

            Base.metadata.create_all(bind=self.engine)

            print("✅ Таблицы созданы/проверены успешно")

            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            print(f"📊 Таблицы в БД: {tables}")

            return True

        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            import traceback
            traceback.print_exc()
            return False

    def close_connection(self):
        """Закрытие соединения с БД."""
        if self.engine:
            self.engine.dispose()
            print("🔌 Соединение с БД закрыто")

    def test_connection(self):
        """Тестовый метод для проверки работы БД."""
        if not self.SessionLocal:
            return "❌ Нет подключения к БД"
        db = self.SessionLocal()
        try:
            result = db.execute(text("SELECT version();"))
            version = result.fetchone()
            return f"✅ PostgreSQL версия: {version[0]}"
        except Exception as e:
            return f"❌ Ошибка теста: {e}"
        finally:
            db.close()

    # --------------------------- ПОЛЬЗОВАТЕЛИ ---------------------------
    def get_user_by_id(self, user_id: int):
        """Вернуть ORM-объект User по id (или None)."""
        if not self.SessionLocal:
            return None
        db = self.SessionLocal()
        try:
            # SQLAlchemy 2.x: session.get
            return db.get(User, int(user_id))
        except Exception as e:
            print(f"get_user_by_id error: {e}")
            return None
        finally:
            db.close()

    def register_user(self, email: str, password: str, username: str = "") -> Tuple[bool, str]:
        """Регистрация нового пользователя."""
        if not self.SessionLocal:
            return False, "Нет подключения к БД"

        db = self.SessionLocal()
        try:
            # Проверка существования
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return False, "Пользователь с таким email уже существует"

            new_user = User(
                email=email.strip().lower(),
                password=password,  # !!! Продумай хэширование
                username=username if username else email.split('@')[0]
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return True, f"Пользователь создан с ID: {new_user.id}"

        except IntegrityError:
            db.rollback()
            return False, "Пользователь с таким email уже существует"
        except Exception as e:
            db.rollback()
            return False, f"Ошибка регистрации: {e}"
        finally:
            db.close()

    def login_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Аутентификация пользователя (без хэша — только для прототипа)."""
        if not self.SessionLocal:
            return False, "Нет подключения к БД"

        db = self.SessionLocal()
        try:
            email = email.strip().lower()
            print(f"🔐 Попытка входа: email='{email}', password='{password}'")

            all_users = db.query(User).all()
            print(f"👥 Все пользователи в БД ({len(all_users)}):")
            for user in all_users:
                print(f"   - '{user.email}' -> '{user.password}'")

            user = db.query(User).filter(User.email == email).first()
            if user:
                print(f"✅ Пользователь найден: ID={user.id}, Email='{user.email}'")
                print(f"🔑 Сравнение паролей: '{password}' vs '{user.password}'")
                if user.password == password:
                    return True, f"Добро пожаловать, {user.username or user.email}! (ID: {user.id})"
                else:
                    return False, "Неверный пароль"
            else:
                print(f"❌ Пользователь с email '{email}' не найден")
                return False, "Пользователь с таким email не найден"

        except Exception as e:
            print(f"❌ Ошибка входа: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Ошибка входа: {e}"
        finally:
            db.close()

    # --------------------------- ЧАТЫ ---------------------------

    def create_chat(self, user_id: int, title: str = "Новый чат") -> Optional[Chat]:
        """Создать чат для пользователя."""
        if not self.SessionLocal:
            return None
        db = self.SessionLocal()
        try:
            chat = Chat(user_id=user_id, title=(title or "Новый чат").strip())
            db.add(chat)
            db.commit()
            db.refresh(chat)
            return chat
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ create_chat: {e}")
            return None
        finally:
            db.close()

    def get_chats_by_user(self, user_id: int) -> List[Chat]:
        """Список чатов конкретного пользователя (сортировка по дате создания, новые сверху)."""
        if not self.SessionLocal:
            return []
        db = self.SessionLocal()
        try:
            return (
                db.query(Chat)
                .filter(Chat.user_id == user_id)
                .order_by(Chat.created_at.desc())
                .all()
            )
        except SQLAlchemyError as e:
            print(f"❌ get_chats_by_user: {e}")
            return []
        finally:
            db.close()

    def get_chat_by_id(self, chat_id: int) -> Optional[Chat]:
        """Получить чат по id (без проверки владельца)."""
        if not self.SessionLocal:
            return None
        db = self.SessionLocal()
        try:
            return db.query(Chat).filter(Chat.id == chat_id).first()
        except SQLAlchemyError as e:
            print(f"❌ get_chat_by_id: {e}")
            return None
        finally:
            db.close()

    def rename_chat(self, chat_id: int, title: str) -> Optional[Chat]:
        """Переименовать чат."""
        if not self.SessionLocal:
            return None
        db = self.SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return None
            chat.title = (title or "Новый чат").strip()
            db.commit()
            db.refresh(chat)
            return chat
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ rename_chat: {e}")
            return None
        finally:
            db.close()

    def delete_chat(self, chat_id: int) -> bool:
        """Удалить чат (сообщения удалятся каскадно)."""
        if not self.SessionLocal:
            return False
        db = self.SessionLocal()
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return False
            db.delete(chat)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ delete_chat: {e}")
            return False
        finally:
            db.close()

    # --------------------------- СООБЩЕНИЯ ---------------------------

    def get_messages_by_chat(self, chat_id: int) -> List[ChatMessage]:
        """Сообщения чата по возрастанию id (как в модели)."""
        if not self.SessionLocal:
            return []
        db = self.SessionLocal()
        try:
            return (
                db.query(ChatMessage)
                .filter(ChatMessage.chat_id == chat_id)
                .order_by(ChatMessage.id.asc())
                .all()
            )
        except SQLAlchemyError as e:
            print(f"❌ get_messages_by_chat: {e}")
            return []
        finally:
            db.close()

    def add_message(self, chat_id: int, role: MessageRole, content: str) -> Optional[ChatMessage]:
        """Добавить сообщение в чат."""
        if not self.SessionLocal:
            return None
        db = self.SessionLocal()
        try:
            # проверим, что чат существует
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return None

            msg = ChatMessage(chat_id=chat_id, role=role, content=(content or "").strip())
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ add_message: {e}")
            return None
        finally:
            db.close()
