from typing import Any, Dict, List, Optional

from .api_client import ApiClient


class ChatService:
    """Обертка над REST API для работы с чатами."""

    def __init__(self, client: ApiClient):
        self._client = client

    def list_chats(self) -> List[Dict[str, Any]]:
        data = self._client.request("GET", "/chats/")
        return list(data or [])

    def create_chat(self, title: Optional[str] = None) -> Dict[str, Any]:
        payload = {"title": title}
        return self._client.request("POST", "/chats/", json=payload)

    def rename_chat(self, chat_id: int, title: str) -> Dict[str, Any]:
        payload = {"title": title}
        return self._client.request("PUT", f"/chats/{chat_id}", json=payload)

    def delete_chat(self, chat_id: int) -> None:
        self._client.request("DELETE", f"/chats/{chat_id}")

    def list_messages(self, chat_id: int) -> List[Dict[str, Any]]:
        data = self._client.request("GET", f"/chats/{chat_id}/messages")
        return list(data or [])

    def add_message(self, chat_id: int, role: str, content: str) -> Dict[str, Any]:
        payload = {"role": role, "content": content}
        return self._client.request("POST", f"/chats/{chat_id}/messages", json=payload)
