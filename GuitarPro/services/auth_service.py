from typing import Any, Dict, Optional

from .api_client import ApiClient, ApiError


class AuthService:
    """Высокоуровневый сервис для регистрации и аутентификации."""

    def __init__(self, client: ApiClient):
        self._client = client

    def register(self, email: str, password: str, username: Optional[str] = None) -> Dict[str, Any]:
        payload = {"email": email, "password": password, "username": username}
        return self._client.request("POST", "/auth/register", json=payload)

    def login(self, email: str, password: str) -> Dict[str, Any]:
        payload = {"email": email, "password": password}
        return self._client.request("POST", "/auth/login", json=payload)

    def logout(self) -> None:
        self._client.clear_token()


__all__ = ["AuthService", "ApiError"]
