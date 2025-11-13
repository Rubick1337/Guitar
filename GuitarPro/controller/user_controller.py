"""Контроллер пользователей оставлен для обратной совместимости.

Основная работа с пользователями теперь выполняется через REST API
(см. services.auth_service и services.user_service)."""

from services.auth_service import AuthService
from services.user_service import UserService


class UserController:
    def __init__(self, auth_service: AuthService, user_service: UserService):
        self.auth_service = auth_service
        self.user_service = user_service

    def register_user(self, email: str, password: str, username: str = ""):
        return self.auth_service.register(email=email, password=password, username=username or None)

    def login_user(self, email: str, password: str):
        return self.auth_service.login(email=email, password=password)

    def current_user(self):
        return self.user_service.me()
