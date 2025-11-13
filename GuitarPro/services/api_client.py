from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class ApiError(RuntimeError):
    """Ошибка, возникающая при запросах к backend-серверу."""

    def __init__(self, detail: Any, status_code: Optional[int] = None):
        super().__init__(str(detail))
        self.detail = detail
        self.status_code = status_code


@dataclass
class ApiClient:
    """Небольшой HTTP-клиент для общения с FastAPI-сервером."""

    base_url: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    timeout: int = 15

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self._token: Optional[str] = None

    # --- токен ---
    def set_token(self, token: Optional[str]) -> None:
        self._token = token

    def clear_token(self) -> None:
        self._token = None

    # --- запросы ---
    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        headers: Dict[str, str] = kwargs.pop("headers", {})
        if self._token:
            headers.setdefault("Authorization", f"Bearer {self._token}")
        try:
            response = requests.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise ApiError(f"Не удалось подключиться к серверу: {exc}") from exc

        if response.status_code >= 400:
            try:
                payload = response.json()
                detail = payload.get("detail", payload)
            except ValueError:
                detail = response.text or response.reason
            raise ApiError(detail, status_code=response.status_code)

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except ValueError:
            return response.text
