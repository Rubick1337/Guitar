from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.popup import Popup
from kivy.app import App

from services.api_client import ApiError
from services.auth_service import AuthService


class RoundedButton(Button):
    bg_color = ListProperty([0.2, 0.6, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.bind(pos=self._update_canvas, size=self._update_canvas, bg_color=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[25])


class LoginScreen(Screen):
    auth_service = ObjectProperty(None)

    def __init__(self, auth_service: AuthService, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = auth_service

        Window.clearcolor = get_color_from_hex('#000000')

        main_layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        back_button = Button(
            text="Назад",
            size_hint=(None, None),
            size=(100, 40),
            background_color=(0, 0, 0, 0),
            color=get_color_from_hex('#FFFFFF'),
            bold=True
        )
        back_button.bind(on_press=self.go_back)

        back_container = BoxLayout(size_hint=(1, 0.1))
        back_container.add_widget(back_button)
        back_container.add_widget(Label())
        main_layout.add_widget(back_container)

        guitar_image = Image(
            source='guitar.png',
            size_hint=(1, 0.3),
            allow_stretch=True,
            keep_ratio=True
        )
        main_layout.add_widget(guitar_image)

        title_label = Label(
            text="Введите данные",
            font_size=32,
            size_hint=(1, 0.1),
            color=get_color_from_hex('#FFFFFF'),
            bold=True
        )
        main_layout.add_widget(title_label)

        form_container = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint=(1, 0.5),
            padding=[50, 0, 50, 0]
        )

        email_label = Label(
            text="Введите почту",
            font_size=16,
            size_hint=(1, 0.2),
            color=get_color_from_hex('#E0E0E0'),
            halign='left'
        )
        form_container.add_widget(email_label)

        self.email_input = TextInput(
            hint_text="example@mail.com",
            size_hint=(1, 0.7),
            multiline=False,
            font_size=16,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[15, 10],
            cursor_color=(0, 0, 0, 1)
        )
        form_container.add_widget(self.email_input)

        form_container.add_widget(BoxLayout(size_hint=(1, 0.1)))

        password_label = Label(
            text="Введите пароль",
            font_size=16,
            size_hint=(1, 0.2),
            color=get_color_from_hex('#E0E0E0'),
            halign='left'
        )
        form_container.add_widget(password_label)

        self.password_input = TextInput(
            hint_text="Ваш пароль",
            size_hint=(1, 0.7),
            password=True,
            multiline=False,
            font_size=16,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[15, 10],
            cursor_color=(0, 0, 0, 1)
        )
        form_container.add_widget(self.password_input)

        form_container.add_widget(BoxLayout(size_hint=(1, 0.2)))

        btn_login = RoundedButton(
            text="ВХОД",
            size_hint=(1, 0.6),
            color=get_color_from_hex('#FFFFFF'),
            font_size=20,
            bg_color=get_color_from_hex('#6A4CA4'),
            bold=True
        )
        btn_login.bind(on_press=self.perform_login)
        form_container.add_widget(btn_login)

        main_layout.add_widget(form_container)
        self.add_widget(main_layout)

    def go_back(self, _instance):
        self.manager.current = 'welcome'

    def show_message(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        btn_ok = Button(text='OK', size_hint_y=None, height=40)
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn_ok.bind(on_press=popup.dismiss)
        content.add_widget(btn_ok)
        popup.open()

    def perform_login(self, _instance):
        email = (self.email_input.text or "").strip().lower()
        password = self.password_input.text or ""
        if not email or not password:
            self.show_message("Ошибка", "Заполните все поля")
            return

        if not self.auth_service:
            self.show_message("Ошибка", "Сервис авторизации недоступен")
            return

        try:
            response = self.auth_service.login(email, password)
        except ApiError as exc:
            self.show_message("Ошибка", str(exc.detail or exc))
            return

        app = App.get_running_app()
        if hasattr(app, "handle_login"):
            app.handle_login(response)
        else:
            self.show_message("Ошибка", "Приложение не поддерживает авторизацию")
