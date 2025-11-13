import os
from pathlib import Path
from typing import Callable, Dict

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivy.resources import resource_add_path, resource_find
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

APP_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = APP_DIR / "assets" / "icons"
resource_add_path(str(ASSETS_DIR))

ACCENT_ON = (1.00, 0.90, 0.40, 1)
ACCENT_OFF = (0.75, 0.75, 0.78, 1)
BAR_BG = (0.05, 0.05, 0.05, 1)
TAB_BG = (0.10, 0.10, 0.10, 1)

ICON: Dict[str, tuple[str, str]] = {
    "autotune": ("assets/icons/guitar.png", "assets/icons/autotune_active.png"),
    "chords": ("assets/icons/accord.png", "assets/icons/chords_active.png"),
    "assistant": ("assets/icons/gpt.png", "assets/icons/assistant_active.png"),
    "profile": ("assets/icons/profile.png", "assets/icons/profile_active.png"),
}


def _resolve_icon(path_str: str) -> str:
    if not path_str:
        return ""
    found = resource_find(path_str)
    if found and os.path.exists(found):
        return found
    candidate = (ASSETS_DIR / Path(path_str).name).as_posix()
    if os.path.exists(candidate):
        return candidate
    return ""


class TabButton(ButtonBehavior, BoxLayout):
    key = StringProperty("")
    text = StringProperty("")
    icon_src = StringProperty("")
    icon_src_active = StringProperty("")
    active = BooleanProperty(False)
    active_color = ListProperty(ACCENT_ON)
    inactive_color = ListProperty(ACCENT_OFF)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = 1
        self.padding = [0, 6, 0, 6]
        self.spacing = 2

        with self.canvas.before:
            Color(*TAB_BG)
            self._bg = RoundedRectangle(radius=[14, 14, 0, 0])

        self.img = Image(source="", size_hint_y=None, height=24, allow_stretch=True, keep_ratio=True)
        self.lbl_text = Label(text=self.text, font_size=12, color=self._color())

        with self.canvas.after:
            Color(*ACCENT_ON)
            self._underline = Rectangle(size=(0, 0), pos=(0, 0))

        self.add_widget(Widget(size_hint_y=None, height=2))
        self.add_widget(self.img)
        self.add_widget(self.lbl_text)
        self.add_widget(Widget(size_hint_y=None, height=2))

        self.bind(pos=self._update_bg, size=self._update_bg)
        self.bind(active=self._on_active)
        self._apply_icon()
        Clock.schedule_once(lambda *_: self._update_underline(), 0)

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._update_underline()

    def _update_underline(self):
        if self.active:
            self._underline.size = (self.width * 0.6, 3)
            self._underline.pos = (self.x + self.width * 0.2, self.y + 2)
        else:
            self._underline.size = (0, 0)

    def _color(self):
        return self.active_color if self.active else self.inactive_color

    def _on_active(self, *_):
        self.lbl_text.color = self._color()
        self._apply_icon()
        self._update_underline()

    def _apply_icon(self):
        src_active = _resolve_icon(self.icon_src_active)
        src_inactive = _resolve_icon(self.icon_src)
        if self.active:
            self.img.source = src_active or src_inactive or ""
        else:
            self.img.source = src_inactive or src_active or ""
        self.img.opacity = 1.0 if self.img.source else 0.0

    def on_press(self):
        self.img.opacity = 0.7
        self.lbl_text.opacity = 0.7

    def on_release(self):
        self.img.opacity = 1
        self.lbl_text.opacity = 1


class BottomNav(BoxLayout):
    on_tab_select = ObjectProperty(None)

    def __init__(self, on_tab_select: Callable[[str], None], **kwargs):
        super().__init__(**kwargs)
        self.on_tab_select = on_tab_select
        self.size_hint_y = None
        self.height = 72
        self.orientation = "horizontal"
        self.spacing = 10
        self.padding = [12, 8, 12, 10]

        with self.canvas.before:
            Color(*BAR_BG)
            self._bg = RoundedRectangle(radius=[16, 16, 0, 0])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self._tabs: Dict[str, TabButton] = {
            key: TabButton(key=key, text=text, icon_src=icons[0], icon_src_active=icons[1])
            for key, text, icons in [
                ("autotune", "АвтоТюн", ICON["autotune"]),
                ("chords", "Обучалка", ICON["chords"]),
                ("assistant", "Ассистент", ICON["assistant"]),
                ("profile", "Профиль", ICON["profile"]),
            ]
        }

        for key, tab in self._tabs.items():
            tab.bind(on_release=lambda _tab, tab_key=key: self._select(tab_key))
            self.add_widget(tab)

        self.set_active("autotune")

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _select(self, key: str) -> None:
        self.set_active(key)
        if self.on_tab_select:
            self.on_tab_select(key)

    def set_active(self, key: str) -> None:
        for tab_key, tab in self._tabs.items():
            tab.active = tab_key == key
