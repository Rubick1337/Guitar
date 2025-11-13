# GuitarPro

Русскоязычное описание архитектуры проекта и шагов установки.

## Архитектура

Проект разделён на два слоя:

- **Kivy-клиент** (`GuitarPro/`): графический интерфейс приложения. Экран входа, регистрации,
  основное меню и тематические панели находятся в каталоге `GuitarPro/components`. Работа с
  удалённым API инкапсулирована в контроллерах (`GuitarPro/controller`) и сервисах
  (`GuitarPro/services`).
- **FastAPI-сервер** (`GuitarPro/server/`): REST API с аутентификацией по JWT. Сервер использует
  SQLAlchemy-модели из `GuitarPro/database`, зависимость от PostgreSQL описана в
  `GuitarPro/config/database.py`.

Дополнительные модули:

- `GuitarPro/services/api_client.py` — общий HTTP-клиент с поддержкой Bearer-токена.
- `GuitarPro/services/auth_service.py`, `user_service.py`, `chat_service.py` — высокоуровневые
  обёртки над API для экранов Kivy.
- `GuitarPro/components/main_menu/` — разбитая на подмодули реализация главного меню.

## Подготовка окружения

1. Создайте и активируйте виртуальное окружение Python 3.11+.
2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Настройте переменные окружения для подключения к PostgreSQL (пример `.env`):

   ```env
   DB_NAME=guitarpro_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432

   JWT_SECRET=замените-на-секрет
   JWT_EXPIRE_MINUTES=120
   API_BASE_URL=http://127.0.0.1:8000
   ```

4. (Опционально) Для работы ИИ-ассистента установите и запустите Ollama, а также модель,
   которую укажете в `OLLAMA_MODEL`.

## Запуск сервера

```bash
uvicorn server.main:app --reload
```

При старте сервер создаст таблицы в БД и будет доступен по `http://127.0.0.1:8000`.

## Запуск клиента

```bash
python -m GuitarPro.main
```

Клиент использует `API_BASE_URL` для обращения к серверу, поэтому убедитесь, что сервер
запущен перед авторизацией. После успешного входа токен сохраняется в памяти приложения и
передаётся вместе с запросами.

## Тестирование API

- Регистрация: `POST /auth/register`
- Логин: `POST /auth/login`
- Текущий пользователь: `GET /auth/me`
- Работа с чатами: `GET/POST /chats/`, `PUT/DELETE /chats/{id}`, `GET/POST /chats/{id}/messages`

Все защищённые маршруты требуют заголовка `Authorization: Bearer <token>`.

## Полезно знать

- При выходе из аккаунта (`Профиль → Выйти`) токен и локальные данные удаляются, пользователь
  возвращается на приветственный экран.
- Панели главного меню загружаются лениво и повторно используют созданные контроллеры, что
  упрощает поддержку и расширение интерфейса.
