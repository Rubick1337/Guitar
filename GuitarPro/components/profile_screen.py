from pathlib import Path
from typing import Any, Dict, Optional
import os

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import DictProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.resources import resource_add_path, resource_find
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import get_color_from_hex

from services.api_client import ApiError
from services.user_service import UserService

APP_DIR = Path(__file__).resolve().parents[1]
ICONS_DIR = APP_DIR / "assets" / "icons"
resource_add_path(str(ICONS_DIR))

PROFILE_ICON_PATH = "assets/icons/profile.png"


class ProfilePanel(BoxLayout):
    user_id = NumericProperty(0)
    user_service = ObjectProperty(None)

    user_name = StringProperty("Пользователь")
    user_email = StringProperty("email не указан")
    user_data = DictProperty({})

    def __init__(self, user_id: int = 0, user_service: Optional[UserService] = None,
                 user_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [16, 16, 16, 16]
        self.spacing = 12

        self.user_id = int(user_id or 0)
        self.user_service = user_service
        if user_data:
            self.user_data = user_data
        self._apply_user_data(self.user_data)

        root_center = AnchorLayout(anchor_x="center", anchor_y="center")
        column = BoxLayout(orientation="vertical", spacing=16,
                           size_hint=(None, None), width=420)
        root_center.add_widget(column)

        avatar_holder = AnchorLayout(size_hint=(1, None), height=140)
        avatar_bg = AnchorLayout(size_hint=(None, None), width=120, height=120)

        with avatar_bg.canvas.before:
            self._av_bg_c = Color(1, 1, 1, 0.08)
            self._av_bg = RoundedRectangle(radius=[60, 60, 60, 60])

        def _paint_av_bg(*_):
            self._av_bg.pos = avatar_bg.pos
            self._av_bg.size = avatar_bg.size
        avatar_bg.bind(pos=_paint_av_bg, size=_paint_av_bg)

        self.avatar = Image(
            source=self._resolve_img(PROFILE_ICON_PATH),
            allow_stretch=False, keep_ratio=True,
            size_hint=(None, None)
        )

        def _fit_avatar(*_):
            side = max(1, min(avatar_bg.width, avatar_bg.height) - 12)
            self.avatar.size = (side, side)
        avatar_bg.bind(size=_fit_avatar)
        _fit_avatar()

        avatar_bg.add_widget(self.avatar)
        avatar_holder.add_widget(avatar_bg)
        column.add_widget(avatar_holder)

        self.lbl_name = Label(
            text=self.user_name,
            font_size=24, bold=True,
            color=get_color_from_hex("#FFFFFF"),
            halign="center", valign="middle",
            size_hint=(1, None), height=34
        )
        self.lbl_email = Label(
            text=self.user_email,
            font_size=16,
            color=get_color_from_hex("#BBBBBB"),
            halign="center", valign="middle",
            size_hint=(1, None), height=26
        )
        self.lbl_name.bind(size=lambda *_: setattr(self.lbl_name, "text_size", self.lbl_name.size))
        self.lbl_email.bind(size=lambda *_: setattr(self.lbl_email, "text_size", self.lbl_email.size))
        column.add_widget(self.lbl_name)
        column.add_widget(self.lbl_email)

        self.btn_logout = Button(
            text="Выйти из аккаунта",
            font_size=18, bold=True,
            size_hint=(1, None), height=56,
            background_normal="", background_down="", background_color=(0, 0, 0, 0),
            color=get_color_from_hex("#FFFFFF")
        )
        with self.btn_logout.canvas.before:
            self._sh_c = Color(0, 0, 0, 0.35)
            self._sh = RoundedRectangle(radius=[28, 28, 28, 28])
            self._bg_c = Color(*get_color_from_hex("#6A1B9A"))
            self._bg = RoundedRectangle(radius=[28, 28, 28, 28])
            self._ring_c = Color(1, 1, 1, 0.08)
            self._ring = RoundedRectangle(radius=[28, 28, 28, 28])

        def _repaint_btn(*_):
            self._sh.pos = (self.btn_logout.x, self.btn_logout.y - 3)
            self._sh.size = (self.btn_logout.width, self.btn_logout.height)
            self._bg.pos = self.btn_logout.pos
            self._bg.size = self.btn_logout.size
            self._ring.pos = (self.btn_logout.x + 1, self.btn_logout.y + 1)
            self._ring.size = (self.btn_logout.width - 2, self.btn_logout.height - 2)

        def _state_btn(*_):
            self._bg_c.rgba = get_color_from_hex("#5A1784") if self.btn_logout.state == "down" else get_color_from_hex("#6A1B9A")
            self._ring_c.a = 0.14 if self.btn_logout.state == "down" else 0.08

        self.btn_logout.bind(pos=_repaint_btn, size=_repaint_btn, state=_state_btn)
        _repaint_btn(); _state_btn()

        self.btn_logout.bind(on_release=lambda *_: self._logout())
        column.add_widget(self.btn_logout)

        self.add_widget(root_center)
        self._refresh_labels()

        if not self.user_data and self.user_service and self.user_id:
            self.refresh_from_api()

    def update_user_data(self, user_data: Optional[Dict[str, Any]] = None, fetch_remote: bool = False) -> None:
        if user_data is not None:
            self.user_data = user_data or {}
            self._apply_user_data(self.user_data)
            self._refresh_labels()
        if fetch_remote and self.user_service and self.user_id:
            self.refresh_from_api()

    def refresh_from_api(self) -> None:
        if not (self.user_service and self.user_id):
            return
        try:
            data = self.user_service.me()
        except ApiError as exc:
            print(f"[ProfilePanel] Не удалось обновить профиль: {exc.detail}")
            return
        self.user_data = data or {}
        self._apply_user_data(self.user_data)
        self._refresh_labels()

    def _resolve_img(self, path_str: str) -> str:
        found = resource_find(path_str)
        if found and os.path.exists(found):
            return found
        fallback = (ICONS_DIR / Path(path_str).name).as_posix()
        return fallback if os.path.exists(fallback) else ""

    def _apply_user_data(self, data: Dict[str, Any]) -> None:
        self.user_name = data.get("username") or data.get("name") or "Пользователь"
        self.user_email = data.get("email") or "email не указан"

    def _refresh_labels(self):
        self.lbl_name.text = self.user_name
        self.lbl_email.text = self.user_email

    def _logout(self):
        app = App.get_running_app()
        if hasattr(app, "handle_logout"):
            app.handle_logout()
