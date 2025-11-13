from typing import Any, Dict, Optional

from kivy.clock import Clock
from kivy.properties import DictProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from components.assistant_screen import AssistantPanel
from components.autotune_screen import AutoTunePanel
from components.chords_screen import ChordsPanel
from components.profile_screen import ProfilePanel
from controller.chat_controller import ChatController
from services.user_service import UserService

from .navigation import BottomNav


class MainMenuScreen(Screen):
    user_id = NumericProperty(0)
    chat_controller = ObjectProperty(None)
    user_service = ObjectProperty(None)
    user_data = DictProperty({})

    def __init__(self, chat_controller: ChatController, user_service: UserService,
                 user_id: int = 0, user_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.chat_controller = chat_controller
        self.user_service = user_service
        self.user_id = int(user_id or 0)
        if user_data:
            self.user_data = user_data

        root = BoxLayout(orientation='vertical', spacing=0, padding=0)
        self.content = BoxLayout(orientation='vertical')
        root.add_widget(self.content)

        self.navbar = BottomNav(on_tab_select=self.on_tab_select)
        root.add_widget(self.navbar)

        self.add_widget(root)

        self._panels: Dict[str, Optional[object]] = {
            'autotune': None,
            'chords': None,
            'assistant': None,
            'profile': None,
        }

        Clock.schedule_once(lambda *_: self.on_tab_select('autotune'), 0)

    def set_user(self, user_id: int, user_data: Optional[Dict[str, Any]] = None) -> None:
        self.user_id = int(user_id or 0)
        if user_data is not None:
            self.user_data = user_data
        assistant = self._panels.get('assistant')
        if assistant is not None and hasattr(assistant, 'set_user'):
            assistant.set_user(self.user_id)
        profile = self._panels.get('profile')
        if profile is not None and hasattr(profile, 'update_user_data'):
            profile.update_user_data(self.user_data)

    def on_tab_select(self, key: str):
        self.content.clear_widgets()

        for panel in self._panels.values():
            if panel and hasattr(panel, 'on_leave_panel'):
                try:
                    panel.on_leave_panel()
                except Exception:
                    pass

        if key == 'autotune':
            if self._panels['autotune'] is None:
                self._panels['autotune'] = AutoTunePanel()
            self.content.add_widget(self._panels['autotune'])

        elif key == 'chords':
            if self._panels['chords'] is None:
                self._panels['chords'] = ChordsPanel()
            self.content.add_widget(self._panels['chords'])

        elif key == 'assistant':
            if self._panels['assistant'] is None:
                self._panels['assistant'] = AssistantPanel(user_id=self.user_id, chat_controller=self.chat_controller)
            else:
                self._panels['assistant'].set_user(self.user_id)
            self.content.add_widget(self._panels['assistant'])

        elif key == 'profile':
            if self._panels['profile'] is None:
                self._panels['profile'] = ProfilePanel(user_id=self.user_id, user_service=self.user_service,
                                                       user_data=self.user_data)
            else:
                self._panels['profile'].update_user_data(self.user_data)
            self.content.add_widget(self._panels['profile'])

        self.navbar.set_active(key)
