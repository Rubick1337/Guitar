from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image  # Добавляем импорт Image
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty


# Кастомная кнопка с закругленными углами
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


# Приветственный экран
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = get_color_from_hex('#00000')

        # Главный контейнер
        main_layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        # Изображение гитары (ЗАМЕНА эмодзи на картинку)
        guitar_image = Image(
            source='guitar.png',  # Путь к вашему изображению
            size_hint=(1, 0.4),
        )
        main_layout.add_widget(guitar_image)

        # Заголовок
        title_label = Label(
            text="GuitarPro",
            font_size=42,
            size_hint=(1, 0.1),
            color=get_color_from_hex('#FFFFFF'),
            bold=True
        )
        main_layout.add_widget(title_label)

        # Подзаголовок
        subtitle_label = Label(
            text="Ваш проводник в мире гитары",
            font_size=18,
            size_hint=(1, 0.05),
            color=get_color_from_hex('#E0E0E0')
        )
        main_layout.add_widget(subtitle_label)

        # Контейнер для кнопок с отступами
        button_container = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint=(1, 0.4),
            padding=[20, 0, 20, 0]
        )

        # Вопрос для существующих пользователей
        existing_user_label = Label(
            text="Уже есть аккаунт?",
            font_size=16,
            size_hint=(1, 0.2),
            color=get_color_from_hex('#E0E0E0')
        )
        button_container.add_widget(existing_user_label)

        # Кнопка входа
        btn_login = RoundedButton(
            text="ВХОД",
            size_hint=(1, 0.3),
            color=get_color_from_hex('#FFFFFF'),
            font_size=20,
            bg_color=get_color_from_hex('#6A4CA4'),
            bold=True
        )
        btn_login.bind(on_press=self.show_login_message)
        button_container.add_widget(btn_login)

        # Отступ между кнопками
        spacer = BoxLayout(size_hint=(1, 0.1))
        button_container.add_widget(spacer)

        # Вопрос для новых пользователей
        new_user_label = Label(
            text="Впервые в GuitarPro?",
            font_size=16,
            size_hint=(1, 0.2),
            color=get_color_from_hex('#E0E0E0')
        )
        button_container.add_widget(new_user_label)

        # Кнопка регистрации
        btn_register = RoundedButton(
            text="НАЧАТЬ",
            size_hint=(1, 0.3),
            color=get_color_from_hex('#FFFFFF'),
            font_size=20,
            bg_color=get_color_from_hex('#4A90A4'),
            bold=True
        )
        btn_register.bind(on_press=self.show_register_message)
        button_container.add_widget(btn_register)

        main_layout.add_widget(button_container)
        self.add_widget(main_layout)

    def show_login_message(self, instance):
        print("Кнопка 'ВХОД' нажата - переход на экран авторизации")

    def show_register_message(self, instance):
        print("Кнопка 'НАЧАТЬ' нажата - переход на экран регистрации")


class GuitarProApp(App):
    def build(self):
        # Устанавливаем цвет окна
        Window.clearcolor = get_color_from_hex('#1E3A5F')

        # Создаем менеджер экранов
        sm = ScreenManager()

        # Добавляем только WelcomeScreen
        sm.add_widget(WelcomeScreen(name='welcome'))

        return sm


if __name__ == '__main__':
    GuitarProApp().run()