from typing import Any, Tuple

from services.api_client import ApiError
from services.chat_service import ChatService


class ChatController:
    """Контроллер, инкапсулирующий работу с ChatService для UI."""

    def __init__(self, chat_service: ChatService):
        self._service = chat_service

    def create_chat(self, user_id: int, title: str = "Новый чат") -> Tuple[bool, Any]:
        if not user_id:
            return False, "user_id обязателен"
        try:
            chat = self._service.create_chat(title)
            return True, chat
        except ApiError as exc:
            return False, exc.detail

    def list_user_chats(self, user_id: int) -> Tuple[bool, Any]:
        if not user_id:
            return False, "user_id обязателен"
        try:
            chats = self._service.list_chats()
            return True, chats
        except ApiError as exc:
            return False, exc.detail

    def rename_chat(self, user_id: int, chat_id: int, new_title: str) -> Tuple[bool, Any]:
        if not (user_id and chat_id and new_title):
            return False, "user_id, chat_id и new_title обязательны"
        try:
            chat = self._service.rename_chat(chat_id, new_title)
            return True, chat
        except ApiError as exc:
            return False, exc.detail

    def delete_chat(self, user_id: int, chat_id: int) -> Tuple[bool, Any]:
        if not (user_id and chat_id):
            return False, "user_id и chat_id обязательны"
        try:
            self._service.delete_chat(chat_id)
            return True, "Чат удалён"
        except ApiError as exc:
            return False, exc.detail

    def list_messages(self, user_id: int, chat_id: int) -> Tuple[bool, Any]:
        if not (user_id and chat_id):
            return False, "user_id и chat_id обязательны"
        try:
            messages = self._service.list_messages(chat_id)
            return True, messages
        except ApiError as exc:
            return False, exc.detail

    def add_message(self, user_id: int, chat_id: int, role: str, content: str) -> Tuple[bool, Any]:
        if not (user_id and chat_id and role and content):
            return False, "user_id, chat_id, role, content обязательны"
        try:
            message = self._service.add_message(chat_id, role, content)
            return True, message
        except ApiError as exc:
            return False, exc.detail
