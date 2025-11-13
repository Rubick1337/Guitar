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

from services.api_client import ApiError
from services.auth_service import AuthService


class RoundedButton(Button):
    bg_color = ListProperty([0.2, 0.6, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.bind(bg_color=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[25])


class RegisterScreen(Screen):
    auth_service = ObjectProperty(None)

    def __init__(self, auth_service: AuthService, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = auth_service

        Window.clearcolor = get_color_from_hex('#000000')

        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        back_button = Button(
            text="Назад",
            size_hint=(None, None),
            size=(80, 35),
            background_color=(0, 0, 0, 0),
            color=get_color_from_hex('#FFFFFF'),
            bold=True
        )
        back_button.bind(on_press=self.go_back)

        back_container = BoxLayout(size_hint=(1, 0.08))
        back_container.add_widget(back_button)
        back_container.add_widget(Label())

        main_layout.add_widget(back_container)

        guitar_image = Image(
            source='guitar.png',
            size_hint=(1, 0.2),
            allow_stretch=True,
            keep_ratio=True
        )
        main_layout.add_widget(guitar_image)

        title_label = Label(
            text="Регистрация",
            font_size=28,
            size_hint=(1, 0.08),
            color=get_color_from_hex('#FFFFFF'),
            bold=True
        )
        main_layout.add_widget(title_label)

        form_container = BoxLayout(
            orientation='vertical',
            spacing=8,
            size_hint=(1, 0.64),
            padding=[40, 10, 40, 10]
        )

        username_label = Label(
            text="Имя пользователя",
            font_size=14,
            size_hint=(1, 0.12),
            color=get_color_from_hex('#E0E0E0'),
            halign='left'
        )
        form_container.add_widget(username_label)

        self.username_input = TextInput(
            hint_text="Ваше имя",
            size_hint=(1, 0.25),
            multiline=False,
            font_size=11,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[12, 8],
            cursor_color=(0, 0, 0, 1)
        )
        form_container.add_widget(self.username_input)

        form_container.add_widget(BoxLayout(size_hint=(1, 0.02)))

        email_label = Label(
            text="Электронная почта",
            font_size=14,
            size_hint=(1, 0.12),
            color=get_color_from_hex('#E0E0E0'),
            halign='left'
        )
        form_container.add_widget(email_label)

        self.email_input = TextInput(
            hint_text="example@mail.com",
            size_hint=(1, 0.25),
            multiline=False,
            font_size=11,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[12, 8],
            cursor_color=(0, 0, 0, 1)
        )
        form_container.add_widget(self.email_input)

        form_container.add_widget(BoxLayout(size_hint=(1, 0.02)))

        password_label = Label(
            text="Пароль",
            font_size=12,
            size_hint=(1, 0.12),
            color=get_color_from_hex('#E0E0E0'),
            halign='left'
        )
        form_container.add_widget(password_label)

        self.password_input = TextInput(
            hint_text="Придумайте пароль",
            size_hint=(1, 0.25),
            password=True,
            multiline=False,
            font_size=11,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[12, 8],
            cursor_color=(0, 0, 0, 1)
        )
        form_container.add_widget(self.password_input)

        form_container.add_widget(BoxLayout(size_hint=(1, 0.02)))

        confirm_password_label = Label(
            text="Подтвердите пароль",
            font_size=12,
            size_hint=(1, 0.12),
            color=get_color_from_hex('#E0E0E0'),
            halign='left'
        )
        form_container.add_widget(confirm_password_label)

        self.confirm_password_input = TextInput(
            hint_text="Повторите пароль",
            size_hint=(1, 0.25),
            password=True,
            multiline=False,
            font_size=11,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[12, 8],
            cursor_color=(0, 0, 0, 1)
        )
        form_container.add_widget(self.confirm_password_input)

        form_container.add_widget(BoxLayout(size_hint=(1, 0.04)))

        btn_register = RoundedButton(
            text="ЗАРЕГИСТРИРОВАТЬСЯ",
            size_hint=(1, 0.3),
            color=get_color_from_hex('#FFFFFF'),
            font_size=18,
            bg_color=get_color_from_hex('#4A90A4'),
            bold=True
        )
        btn_register.bind(on_press=self.perform_register)
        form_container.add_widget(btn_register)

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

    def perform_register(self, _instance):
        username = (self.username_input.text or "").strip()
        email = (self.email_input.text or "").strip().lower()
        password = self.password_input.text or ""
        confirm_password = self.confirm_password_input.text or ""

        if not email or not password:
            self.show_message("Ошибка", "Email и пароль обязательны")
            return

        if password != confirm_password:
            self.show_message("Ошибка", "Пароли не совпадают")
            return

        if not self.auth_service:
            self.show_message("Ошибка", "Сервис регистрации недоступен")
            return

        try:
            self.auth_service.register(email, password, username=username or None)
        except ApiError as exc:
            self.show_message("Ошибка", str(exc.detail or exc))
            return

        self.show_message("Успех", "Регистрация прошла успешно. Теперь можно войти")
        self.manager.current = 'login'
