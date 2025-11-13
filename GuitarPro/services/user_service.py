from typing import Any, Dict

from .api_client import ApiClient


class UserService:
    """Получение информации о пользователе через API."""

    def __init__(self, client: ApiClient):
        self._client = client

    def me(self) -> Dict[str, Any]:
        return self._client.request("GET", "/auth/me")
