# components/assistant_screen.py
import os
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.resources import resource_add_path, resource_find

# ---------- Конфиг ----------
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

# ---------- Цвета ----------
TEXT = (1, 1, 1, 1)
USER_BG = (0.20, 0.20, 0.20, 1)
BOT_BG = (0.13, 0.13, 0.13, 1)

# ---------- Встроенная база ----------
knowledge_base: Dict[str, str] = {
    "Как играть аккорд C?": "Аккорд C: x32010. Бой: D DU UDU. Песни: 'Кино - Пачка сигарет'.",
    "Как играть аккорд C на гитаре?": "Аккорд C: x32010. Бой: D DU UDU. Песни: 'Кино - Пачка сигарет'.",
    "Аккорд C": "Аккорд C: зажмите 2 струну на 1 ладу, 4 струну на 2 ладу, 5 струну на 3 ладу. x32010.",
    "Как взять аккорд C?": "Аккорд C: x32010. Первый палец - 2 струна 1 лад, второй - 4 струна 2 лад, третий - 5 струна 3 лад.",
    "Как играть бой шестёрку?": "Бой 'шестёрка': D DU UDU. Акцент на 2 и 4 доли. Подходит для многих песен.",
    "Что такое бой шестёрка?": "Бой 'шестёрка': вниз-вниз-вверх-вниз-вверх (D DU UDU). Основной ритмический рисунок.",
    "Бой шестерка": "Шестёрка: D-DU-UDU. Играйте равномерно, акцентируя 2 и 4 доли.",
    "Как играть аккорд Am?": "Аккорд Am: x02210. Простой минорный аккорд, часто используется с C и G.",
    "Аккорд Am": "Am: x02210. Первый палец - 2 струна 1 лад, второй - 3 струна 2 лад, третий - 4 струна 2 лад.",
    "Как играть аккорд G?": "Аккорд G: 320003 или 320033. Варианты: 3 пальца или 4 пальца.",
    "Аккорд G": "G: 320003. Первый палец - 5 струна 2 лад, второй - 6 струна 3 лад, третий - 1 струна 3 лад.",
    "Какие песни играть на Am, C, G?": "Песни: 'Цой - Кукушка', 'Сплин - Выхода нет', 'Кино - Группа крови'.",
    "Песни на аккорды Am C G": "Простые песни: 'Кино - Звезда', 'Сплин - Романс', 'ДДТ - Что такое осень'.",
    "Песни для начинающих": "На Am, C, G: 'Цой - Кукушка', 'Кино - Пачка сигарет', 'Сплин - Выхода нет'.",
    "Как настроить гитару?": "Стандартный строй: E A D G B e (Ми Ля Ре Соль Си ми). Используйте тюнер или приложение.",
    "Настройка гитары": "1 струна - E (ми), 2 - B (си), 3 - G (соль), 4 - D (ре), 5 - A (ля), 6 - E (ми).",
    "Как играть перебор?": "Простой перебор: 4-3-2-3-1-3-2-3. Большой палец играет басовые струны (4-5-6).",
    "Перебор на гитаре": "Перебор 'восьмёрка': 5-3-2-3-1-3-2-3. Практикуйте медленно, затем ускоряйтесь."
}

categories = {
    'аккорд': ['аккорд', 'аккорды', 'am', 'c', 'g', 'd', 'e', 'f'],
    'бой': ['бой', 'шестерк', 'восьмерк', 'ритм'],
    'перебор': ['перебор', 'перебирать'],
    'настройка': ['настройк', 'строй', 'тюнер'],
    'песни': ['песн', 'репертуар', 'играть что']
}

# ---------- NLP/FAISS (лениво) ----------
_embedder = None
_faiss = None
_questions: List[str] = []
_index_ready = False
_ollama_ok = True

def _lazy_init_index():
    global _embedder, _faiss, _questions, _index_ready
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        from sklearn.preprocessing import normalize
        _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        _questions = list(knowledge_base.keys())
        q_emb = _embedder.encode(_questions)
        q_emb = normalize(q_emb).astype('float32')
        _faiss = faiss.IndexFlatIP(q_emb.shape[1])
        _faiss.add(q_emb)
        _index_ready = True
    except Exception as e:
        _index_ready = False
        print(f"[AI Assistant] Индекс не инициализирован: {e}")

def _ensure_index_async(on_done=None):
    if _index_ready or _embedder is not None:
        if on_done:
            on_done()
        return
    def job():
        _lazy_init_index()
        if on_done:
            Clock.schedule_once(lambda *_: on_done(), 0)
    threading.Thread(target=job, daemon=True).start()

def _detect_category(clean_query: str):
    for cat, kws in categories.items():
        if any(k in clean_query for k in kws):
            return cat
    return None

def _answer_via_base(clean_query: str) -> Tuple[bool, Optional[str], float]:
    if not _index_ready:
        return False, None, 0.0
    try:
        from sklearn.preprocessing import normalize
        q_emb = _embedder.encode(clean_query)
        q_emb = normalize(q_emb.reshape(1, -1)).astype('float32')
        D, I = _faiss.search(q_emb, k=1)
        sim_percent = float((D[0][0] + 1.0) * 50.0)
        if sim_percent > 90:
            return True, knowledge_base[_questions[I[0][0]]], sim_percent
        return False, None, sim_percent
    except Exception as e:
        print(f"[AI Assistant] base-search err: {e}")
        return False, None, 0.0

def _answer_via_ollama(clean_query: str, detected_category: str) -> str:
    global _ollama_ok
    try:
        import ollama
        if OLLAMA_HOST:
            os.environ["OLLAMA_HOST"] = OLLAMA_HOST
        sys_prompt = (
            f"Ты гитарный эксперт. Отвечай на вопрос о {detected_category}. "
            "Будь конкретным, используй чёткие термины и краткие шаги. "
            "Если вопрос неясен, предложи уточнить или дай общий совет."
        )
        resp = ollama.chat(
            model=DEFAULT_OLLAMA_MODEL,
            messages=[{"role": "system", "content": sys_prompt},
                      {"role": "user", "content": clean_query}],
        )
        _ollama_ok = True
        return resp["message"]["content"]
    except Exception as e:
        _ollama_ok = False
        return (f"Не удалось обратиться к Ollama: {e}\n"
                f"Подсказка: установите Ollama и модель `{DEFAULT_OLLAMA_MODEL}`.\n"
                f"Если сервер на другой машине — установите переменную OLLAMA_HOST.")

# --- ассеты и иконки ---
APP_DIR   = Path(__file__).resolve().parents[1]
ICONS_DIR = APP_DIR / "assets" / "icons"
resource_add_path(str(ICONS_DIR))

ICON = {  # только базовые png
    "send":    "assets/icons/arrow.png",
    "newchat": "assets/icons/chat.png",
}

def _res(p: str) -> str:
    if not p:
        return ""
    found = resource_find(p)
    if found:
        return found
    cand = (ICONS_DIR / Path(p).name).as_posix()
    return cand

# ---------- Импорт контроллера чатов ----------
from controller.chat_controller import ChatController


class AssistantPanel(BoxLayout):
    """Экран ассистента без загрузочного спиннера."""
    user_id = NumericProperty(0)
    controller = ObjectProperty(None)

    def __init__(self, user_id: int = 0, chat_controller: Optional[ChatController] = None, **kwargs):
        super().__init__(**kwargs)
        if chat_controller is None:
            raise ValueError("AssistantPanel требует chat_controller для работы с API")
        self.user_id = int(user_id or 0)
        self.controller = chat_controller
        self.orientation = 'vertical'
        self.padding = [12, 12, 12, 8]
        self.spacing = 8

        # ----- Верхняя панель: выпадающий список чатов + "Новый чат" -----
        top = BoxLayout(size_hint_y=None, height=52, spacing=10, padding=[10, 6, 10, 6])

        self.chat_spinner = Spinner(
            text="Выберите чат",
            values=[],
            size_hint=(1, 1),
            background_color=(0.10, 0.10, 0.10, 1),
            color=TEXT,
            font_size=16,
        )
        self.chat_spinner.bind(text=self._on_chat_selected)

        new_btn = self._make_icon_pill(
            icon_key="newchat",
            text="Новый чат",
            bg_rgba=(0.20, 0.20, 0.20, 1),
            txt_rgba=TEXT,
            width=148,
            height=44
        )
        new_btn.bind(on_release=lambda *_: self._create_new_chat())

        top.add_widget(self.chat_spinner)
        top.add_widget(new_btn)

        # ----- История -----
        self.scroll = ScrollView(size_hint=(1, 1))
        self.msgs = GridLayout(cols=1, size_hint_y=None, spacing=8, padding=[0, 0, 0, 8])
        self.msgs.bind(minimum_height=self.msgs.setter('height'))
        self.scroll.add_widget(self.msgs)

        # ----- Нижняя панель ввода -----
        bottom = BoxLayout(size_hint_y=None, height=56, spacing=0, padding=[0, 0, 0, 0])
        input_wrap = RelativeLayout(size_hint=(1, 1))

        self.input = TextInput(
            hint_text="Спросите про аккорды, бой, настройку, перебор, песни…",
            multiline=False,
            write_tab=False,
            foreground_color=TEXT,
            background_color=(0.10, 0.10, 0.10, 1),
            cursor_color=TEXT,
            password=False,
            padding=(12, 16, 56, 16),  # запас справа под круг
        )
        self.input.bind(on_text_validate=lambda *_: self.on_send())

        send_wrap = RelativeLayout(size_hint=(None, None), width=56, height=56,
                                   pos_hint={'right': 1, 'center_y': 0.5})

        # Кнопка-круг
        from kivy.graphics import Color, RoundedRectangle
        send_btn = Button(
            text="",
            size_hint=(None, None),
            width=44, height=44,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_normal='', background_down='', background_color=(0, 0, 0, 0)
        )
        with send_btn.canvas.before:
            Color(0, 0, 0, 0.35); sh = RoundedRectangle(radius=[22, 22, 22, 22])
            Color(0.25, 0.25, 0.25, 1); bg = RoundedRectangle(radius=[22, 22, 22, 22])
        def _repaint(*_):
            sh.pos = (send_btn.x, send_btn.y - 2); sh.size = send_btn.size
            bg.pos = send_btn.pos;                bg.size = send_btn.size
        send_btn.bind(pos=_repaint, size=_repaint); _repaint()

        # Стрелка строго по центру (чуть выше на 1px)
        send_img = Image(source=_res(ICON["send"]), size_hint=(None, None), allow_stretch=False, keep_ratio=True)
        def _place_simg(*_):
            side = int(send_btn.height * 0.60)
            send_img.size = (side, side)
            send_img.center = (send_btn.center_x, send_btn.center_y + 1)
        send_btn.bind(pos=_place_simg, size=_place_simg); _place_simg()
        send_btn.add_widget(send_img)
        send_btn.bind(on_release=lambda *_: self.on_send())

        send_wrap.add_widget(send_btn)

        # сборка низа
        input_wrap.add_widget(self.input)
        input_wrap.add_widget(send_wrap)
        bottom.add_widget(input_wrap)

        # ----- Сборка экрана -----
        self.add_widget(top)
        self.add_widget(self.scroll)
        self.add_widget(bottom)

        # ----- Состояние -----
        self._current_chat_id: Optional[int] = None

        # Данные
        self._reload_chats_for_user(init_select=True)

        # Ленивая инициализация семантического индекса (без индикаторов загрузки)
        _ensure_index_async()

        # Фоновая проверка Ollama (без индикаторов)
        def _ping_ollama():
            _ = _answer_via_ollama("Проверка подключения.", "проверка")
        threading.Thread(target=_ping_ollama, daemon=True).start()

    # ---------- «Пилюля»-кнопка с единственной иконкой ----------
    def _make_icon_pill(self, icon_key: str, text: str,
                        bg_rgba=(0.25, 0.25, 0.25, 1), txt_rgba=(1, 1, 1, 1),
                        width: int = 160, height: int = 44) -> Button:
        from kivy.uix.floatlayout import FloatLayout
        from kivy.graphics import Color, RoundedRectangle

        btn = Button(text="", size_hint=(None, None), width=width, height=height,
                     background_normal="", background_down="", background_color=(0, 0, 0, 0))
        with btn.canvas.before:
            Color(0, 0, 0, 0.35); sh = RoundedRectangle(radius=[22, 22, 22, 22])
            bgc = Color(*bg_rgba); bg = RoundedRectangle(radius=[22, 22, 22, 22])
            Color(1, 1, 1, 0.08); ring = RoundedRectangle(radius=[22, 22, 22, 22])

        def _repaint(*_):
            sh.pos = (btn.x, btn.y - 2); sh.size = btn.size
            bg.pos = btn.pos;            bg.size = btn.size
            ring.pos = (btn.x + 1, btn.y + 1); ring.size = (btn.width - 2, btn.height - 2)
        btn.bind(pos=_repaint, size=_repaint); _repaint()

        layer = FloatLayout(size_hint=(None, None))
        def _sync(*_):
            layer.pos = btn.pos; layer.size = btn.size
        btn.bind(pos=_sync, size=_sync); _sync()

        img_path = ICON.get(icon_key, "")
        img = Image(source=_res(img_path), size_hint=(None, None), allow_stretch=False, keep_ratio=True)
        def _place_icon(*_):
            side = int(layer.height * 0.64)
            img.size = (side, side)
            img.pos = (layer.x + 12, layer.center_y - side / 2)
        layer.bind(pos=_place_icon, size=_place_icon); _place_icon()

        lbl = Label(text=text, color=txt_rgba, font_size=16, bold=True,
                    size_hint=(None, None), halign="left", valign="middle")
        def _place_lbl(*_):
            lbl.size = (layer.width - (img.width + 24), layer.height)
            lbl.pos = (img.right + 8, layer.y)
            lbl.text_size = lbl.size
        layer.bind(pos=_place_lbl, size=_place_lbl); _place_lbl()

        layer.add_widget(img)
        layer.add_widget(lbl)
        btn.add_widget(layer)
        return btn

    # ---------- Утилита: укорачивание длинных заголовков ----------
    def _shorten(self, s: str, max_len: int = 28) -> str:
        s = (s or "").strip()
        return s if len(s) <= max_len else (s[:max_len - 1] + "…")

    def set_user(self, user_id: int) -> None:
        new_id = int(user_id or 0)
        if new_id == self.user_id:
            return
        self.user_id = new_id
        self._current_chat_id = None
        self.msgs.clear_widgets()
        self._reload_chats_for_user(init_select=True)

    def _reload_chats_for_user(self, init_select=False):
        self.chat_spinner.values = []
        self._ids = []
        self._titles = []
        if not self.user_id:
            self.chat_spinner.text = "Выберите чат"
            return

        ok, payload = self.controller.list_user_chats(self.user_id)
        if not ok:
            self._push_bubble(f"Не удалось загрузить чаты: {payload}", me=False, save=False)
            return

        self._chats_cache: List[dict] = payload
        for c in payload:
            title = self._shorten(c.get("title") or "Без названия", 28)
            self._titles.append(title)
            self._ids.append(int(c["id"]))

        self.chat_spinner.values = self._titles

        if init_select:
            if self._titles:
                # выбираем первый (самый свежий из list_user_chats)
                self.chat_spinner.text = self._titles[0]
                self._switch_chat(self._ids[0])
            else:
                self._create_new_chat()
        elif not self._titles:
            self.chat_spinner.text = "Выберите чат"

    def _extract_id(self, spinner_text: str) -> Optional[int]:
        try:
            idx = self.chat_spinner.values.index(spinner_text)
            return self._ids[idx]
        except Exception:
            return None

    def _on_chat_selected(self, spinner, text):
        if not text:
            return
        chat_id = self._extract_id(text)
        if chat_id and (self._current_chat_id != chat_id):
            self._switch_chat(chat_id)

    def _switch_chat(self, chat_id: int):
        self._current_chat_id = chat_id
        self._render_history_from_db(chat_id)

    def _render_history_from_db(self, chat_id: int):
        self.msgs.clear_widgets()
        ok, msgs = self.controller.list_messages(self.user_id, chat_id)
        if not ok:
            self._push_bubble(f"Не удалось загрузить сообщения: {msgs}", me=False, save=False)
            return
        for m in msgs:
            self._push_bubble(m.get("content", ""), me=(m.get("role") == "user"), save=False)
        Clock.schedule_once(lambda *_: self._scroll_bottom(), 0)

    def _create_new_chat(self):
        if not self.user_id:
            self._push_bubble("Требуется авторизация пользователя.", me=False, save=False)
            return
        ok, payload = self.controller.create_chat(self.user_id, title="Новый чат")
        if not ok:
            self._push_bubble(f"Не удалось создать чат: {payload}", me=False, save=False)
            return
        self._reload_chats_for_user(init_select=False)
        new_id = payload["id"]
        # найти индекс нового id и выставить текст спиннера
        try:
            idx = self._ids.index(new_id)
            self.chat_spinner.text = self._titles[idx]
        except ValueError:
            pass
        self._switch_chat(new_id)

    def _update_title_if_needed(self, first_user_text: str):
        if not (self.user_id and self._current_chat_id):
            return
        meta = next((c for c in getattr(self, "_chats_cache", []) if c.get("id") == self._current_chat_id), None)
        if not meta:
            return
        if (meta.get("title") or "") not in ["", "Новый чат", "Без названия"]:
            return
        new_title = (first_user_text.strip().splitlines()[0][:32]) or "Новый чат"
        ok, payload = self.controller.rename_chat(self.user_id, self._current_chat_id, new_title)
        if ok:
            current = self.chat_spinner.text
            self._reload_chats_for_user(init_select=False)
            for item in self.chat_spinner.values:
                if item.endswith(f"· {self._current_chat_id}"):
                    self.chat_spinner.text = item; break

    # ---------- Визуальные помощники ----------
    def _push_bubble(self, text: str, me: bool, save: bool = False):
        row = AnchorLayout(size_hint_y=None, height=0, anchor_x=('right' if me else 'left'))
        col = BoxLayout(orientation='vertical', size_hint=(None, None), spacing=4)

        name = "Вы" if me else "Ассистент"
        name_lbl = Label(
            text=f"[color=AAAAAA]{name}[/color]",
            markup=True, size_hint=(None, None), height=16, width=100,
            halign='left', valign='middle', color=TEXT
        )
        name_lbl.bind(texture_size=lambda *_: setattr(name_lbl, "size", name_lbl.texture_size))

        bubble = BoxLayout(size_hint=(None, None), padding=[10, 8, 10, 8])
        bubble_lbl = Label(text=text, size_hint=(None, None), color=TEXT, halign='left', valign='top')
        bubble_lbl.bind(texture_size=lambda *_: setattr(bubble_lbl, "size", (bubble_lbl.texture_size[0], bubble_lbl.texture_size[1])))
        bubble.add_widget(bubble_lbl)

        from kivy.graphics import Color, RoundedRectangle
        with bubble.canvas.before:
            Color(*(USER_BG if me else BOT_BG))
            bubble._bg = RoundedRectangle(radius=[12, 12, 12, 12])

        def _upd_bg(*_):
            bubble._bg.pos = bubble.pos
            bubble._bg.size = bubble.size
        bubble.bind(pos=_upd_bg, size=_upd_bg)

        def _fix_sizes(*_):
            max_width = int(self.width * 0.85)
            bubble_lbl.text_size = (max_width - 24, None)
            Clock.schedule_once(lambda *_2: _recalc(), 0)

        def _recalc():
            w = min(int(self.width * 0.85), bubble_lbl.texture_size[0] + 20)
            h = max(28, bubble_lbl.texture_size[1] + 16)
            bubble.size = (w, h)
            col.size = (w, h + name_lbl.height + 2)
            row.height = col.height + 4

        self.bind(size=_fix_sizes)
        Clock.schedule_once(_fix_sizes, 0)

        col.add_widget(name_lbl)
        col.add_widget(bubble)
        row.add_widget(col)
        self.msgs.add_widget(row)
        Clock.schedule_once(lambda *_: self._scroll_bottom(), 0)

    def _scroll_bottom(self):
        self.scroll.scroll_y = 0

    # ---------- Отправка ----------
    def on_send(self):
        q = (self.input.text or "").strip()
        if not q or not self.user_id:
            return
        if not self._current_chat_id:
            self._create_new_chat()

        self.input.text = ""

        ok, payload = self.controller.add_message(self.user_id, self._current_chat_id, "user", q)
        if not ok:
            self._push_bubble(f"Не удалось сохранить сообщение: {payload}", me=False, save=False)
            return

        self._push_bubble(q, me=True)

        ok_list, msgs = self.controller.list_messages(self.user_id, self._current_chat_id)
        if ok_list and len([m for m in msgs if m.get("role") == "user"]) == 1:
            self._update_title_if_needed(q)

        def job():
            clean_query = ' '.join(q.lower().split())
            detected_category = _detect_category(clean_query)

            if not detected_category:
                base_hint = (
                    "Пожалуйста, уточните вопрос. Я умею:\n"
                    "— Объяснять про аккорды (Am, C, G)\n"
                    "— Показывать гитарные бои (шестёрка, восьмёрка)\n"
                    "— Рассказывать о переборах\n"
                    "— Помогать с настройкой гитары\n"
                    "— Рекомендовать песни для начинающих"
                )
                self.controller.add_message(self.user_id, self._current_chat_id, "assistant", base_hint)
                Clock.schedule_once(lambda *_: self._answer_bot(base_hint), 0)
                return

            okb, base_answer, sim = _answer_via_base(clean_query)
            if okb and base_answer:
                text = base_answer + f"\n\n(совпадение с базой: {sim:.1f}%)"
                self.controller.add_message(self.user_id, self._current_chat_id, "assistant", text)
                Clock.schedule_once(lambda *_: self._answer_bot(text), 0)
                return

            llm_text = _answer_via_ollama(clean_query, detected_category)
            self.controller.add_message(self.user_id, self._current_chat_id, "assistant", llm_text)
            Clock.schedule_once(lambda *_: self._answer_bot(llm_text), 0)

        threading.Thread(target=job, daemon=True).start()

    def _answer_bot(self, text: str):
        self._push_bubble(text, me=False)

    def on_leave_panel(self):
        pass
