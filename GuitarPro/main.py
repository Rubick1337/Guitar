# main.py
import os
import sys
from typing import Any, Dict, Optional

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import get_color_from_hex

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.main_menu import MainMenuScreen
from components.login_screen import LoginScreen
from components.register_screen import RegisterScreen
from components.welcome_screen import WelcomeScreen
from controller.chat_controller import ChatController
from services.api_client import ApiClient
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.user_service import UserService


class GuitarProApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_client = ApiClient()
        self.auth_service = AuthService(self.api_client)
        self.user_service = UserService(self.api_client)
        self.chat_service = ChatService(self.api_client)
        self.chat_controller = ChatController(self.chat_service)

        self.current_user: Dict[str, Any] = {}
        self.current_user_id: Optional[int] = None

    def build(self):
        Window.clearcolor = get_color_from_hex('#000000')
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(LoginScreen(name='login', auth_service=self.auth_service))
        sm.add_widget(RegisterScreen(name='register', auth_service=self.auth_service))
        return sm

    def handle_login(self, response: Dict[str, Any]):
        token = response.get('access_token')
        user = response.get('user') or {}
        if token:
            self.api_client.set_token(token)
        self.current_user = user
        self.current_user_id = user.get('id') if isinstance(user, dict) else None
        self.open_main_menu()

    def open_main_menu(self):
        sm: ScreenManager = self.root
        user_id = int(self.current_user_id or 0)
        if not sm.has_screen('menu'):
            menu = MainMenuScreen(
                name='menu',
                chat_controller=self.chat_controller,
                user_service=self.user_service,
                user_id=user_id,
                user_data=self.current_user,
            )
            sm.add_widget(menu)
        else:
            menu = sm.get_screen('menu')
            menu.set_user(user_id, self.current_user)
        sm.current = 'menu'

    def handle_logout(self):
        self.auth_service.logout()
        self.api_client.clear_token()
        self.current_user = {}
        self.current_user_id = None
        sm: ScreenManager = self.root
        if sm.has_screen('menu'):
            menu = sm.get_screen('menu')
            menu.set_user(0, {})
        if sm.has_screen('welcome'):
            sm.current = 'welcome'


if __name__ == '__main__':
    GuitarProApp().run()
