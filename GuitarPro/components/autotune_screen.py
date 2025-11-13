# components/autotune_screen.py
import os
from pathlib import Path
import numpy as np

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.resources import resource_find, resource_add_path
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.core.window import Window

# ======= Режим правки расположения кнопок =======
EDIT_MODE = False

# ======= Пути =======
APP_DIR   = Path(__file__).resolve().parents[1]
IMG_DIR   = APP_DIR / "assets" / "img"
ICONS_DIR = APP_DIR / "assets" / "icons"
resource_add_path(str(IMG_DIR))
resource_add_path(str(ICONS_DIR))

HEAD_IMAGE = "assets/img/headstock.png"
HEAD_SCALE = 0.7  # уменьшение изображения, без апскейла

# ======= Иконки =======
ICON = {
    "start": ("assets/icons/start.png", "assets/icons/start_active.png"),
    "stop":  ("assets/icons/stop.png",  "assets/icons/stop_active.png"),
}

# ======= Частоты =======
TUNING_FREQUENCIES = {
    "E2": 82.41, "A2": 110.00, "D3": 146.83,
    "G3": 196.00, "B3": 246.94, "E4": 329.63
}

# ======= Аудио (по возможности) =======
_HAS_AUDIO = True
try:
    import sounddevice as sd
except Exception:
    _HAS_AUDIO = False
try:
    from scipy.fftpack import fft  # noqa: F401
except Exception:
    fft = None
    _HAS_AUDIO = False


def analyze_frequency(signal, sample_rate):
    n = len(signal)
    if n <= 0:
        return 0.0
    window = np.hanning(n).astype(np.float32)
    sig = (signal * window).astype(np.float32)
    spec = np.abs(np.fft.rfft(sig))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    idx = int(np.argmax(spec))
    if idx <= 0 or idx >= len(freqs):
        return 0.0
    return float(freqs[idx])


# ======= Круглая кнопка «колка» =======
class CirclePegToggle(ToggleButton):
    allow_drag = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.width = self.height = 44
        self.font_size = 14
        self.bold = True
        self.color = (1, 1, 1, 1)
        self.halign = "center"
        self.valign = "middle"
        self.text_size = (self.width, self.height)
        self.background_normal = ""
        self.background_down   = ""
        self.background_color  = (0, 0, 0, 0)

        with self.canvas.before:
            self._c_bg   = Color(0.15, 0.15, 0.18, 1)
            self._bg     = Ellipse(pos=self.pos, size=self.size)
            self._c_ring = Color(0.85, 0.85, 0.9, 0.18)
            self._ring   = Line(circle=(self.center_x, self.center_y, self.width/2 - 1), width=1.1)

        self.bind(pos=self._refresh, size=self._refresh, state=self._refresh)

        self._drag = False
        self._dx = 0
        self._dy = 0
        if self.allow_drag:
            self.disabled = True

    def _refresh(self, *_):
        side = min(self.width, self.height)
        cx, cy = self.center_x, self.center_y
        self._bg.pos = (cx - side/2, cy - side/2)
        self._bg.size = (side, side)
        self._ring.circle = (cx, cy, side/2 - 1)
        if self.state == "down":
            self._c_bg.rgba   = (0.05, 0.20, 0.30, 1)
            self._c_ring.rgba = (0.40, 0.85, 1.00, 0.85)
        else:
            self._c_bg.rgba   = (0.15, 0.15, 0.18, 1)
            self._c_ring.rgba = (0.85, 0.85, 0.9, 0.18)

    def on_touch_down(self, touch):
        if not self.allow_drag:
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self._drag = True
            self._dx = touch.x - self.x
            self._dy = touch.y - self.y
            return True
        return False

    def on_touch_move(self, touch):
        if not self.allow_drag or not self._drag:
            return super().on_touch_move(touch)
        self.pos = (touch.x - self._dx, touch.y - self._dy)
        host = self.parent
        if host and hasattr(host, "_img_rect"):
            rect = host._img_rect()
            if rect:
                draw_x, draw_y, draw_w, draw_h = rect
                rx = (self.center_x - draw_x) / draw_w
                ry = (self.center_y - draw_y) / draw_h
                print(f"[EDIT] {self.text}: rx={rx:.4f}, ry={ry:.4f}")
        return True

    def on_touch_up(self, touch):
        if not self.allow_drag or not self._drag:
            return super().on_touch_up(touch)
        self._drag = False
        return True


# ======= Панель =======
class AutoTunePanel(BoxLayout):
    current_string = StringProperty('E2')
    current_freq   = NumericProperty(0.0)
    target_freq    = NumericProperty(TUNING_FREQUENCIES['E2'])
    status_text    = StringProperty('Ожидание...')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [16, 16, 16, 16]
        self.spacing = 10

        self.sample_rate = 44100
        self.duration    = 0.4
        self._event      = None

        # --- Верх: headstock ---
        self.img_wrap = FloatLayout(size_hint=(1, 0.58))
        self.img_wrap._img_rect = self._img_draw_rect

        self.head_img = Image(
            source=self._resolve_img(HEAD_IMAGE),
            keep_ratio=True,
            allow_stretch=False,
            size_hint=(None, None),
        )
        self.img_wrap.add_widget(self.head_img)

        self.peg_centers = {
            "D3": (0.1893, 0.8510),
            "A2": (0.1856, 0.7011),
            "E4": (0.1820, 0.5381),
            "G3": (0.7924, 0.8594),
            "B3": (0.7960, 0.7011),
            "E2": (0.7924, 0.5381),
        }

        self._toggles = {}
        for name in ("D3", "A2", "E4", "G3", "B3", "E2"):
            t = CirclePegToggle(text=name, group="strings", allow_drag=EDIT_MODE)
            if not EDIT_MODE:
                t.bind(on_release=lambda btn, s=name: self._select_string(s))
            self._toggles[name] = t
            self.img_wrap.add_widget(t)

        self.img_wrap.bind(size=lambda *_: self._layout_image_and_pegs())
        self.head_img.bind(texture=lambda *_: self._layout_image_and_pegs())
        Window.bind(size=lambda *_: self._layout_image_and_pegs())
        Clock.schedule_once(lambda *_: self._layout_image_and_pegs(), 0)
        Clock.schedule_once(lambda *_: self._sync_toggle_state(), 0)

        # --- Центр: показания ---
        info = BoxLayout(orientation='vertical', size_hint=(1, 0.20), spacing=6)
        self.lbl_target  = Label(text=f"Цель: {self.target_freq:.2f} Hz", font_size='18sp', size_hint_y=None, height=28)
        self.lbl_current = Label(text=f"Текущая: — Hz",               font_size='32sp', size_hint_y=None, height=56)
        self.lbl_status  = Label(text=self.status_text,               font_size='18sp', size_hint_y=None, height=28)
        info.add_widget(self.lbl_target); info.add_widget(self.lbl_current); info.add_widget(self.lbl_status)

        # --- Низ: кнопки-пилюли с иконками ---
        controls = BoxLayout(size_hint_y=None, height=64, spacing=10)

        btn_start = self._make_pill_button(
            icon_key="start", text="Старт",
            base_rgba=(0.98, 0.78, 0.10, 1), down_rgba=(0.88, 0.68, 0.08, 1),
            text_color=(0.08, 0.08, 0.12, 1)  # тёмный текст на жёлтом
        )
        btn_stop = self._make_pill_button(
            icon_key="stop", text="Стоп",
            base_rgba=(0.05, 0.20, 0.30, 1), down_rgba=(0.04, 0.16, 0.26, 1),
            text_color=(1, 1, 1, 1)  # белый текст на синем
        )

        btn_start.bind(on_release=lambda *_: self.start_listen())
        btn_stop.bind(on_release=lambda *_: self.stop_listen())

        controls.add_widget(btn_start)
        controls.add_widget(btn_stop)

        # Сборка
        self.add_widget(self.img_wrap)
        self.add_widget(info)
        self.add_widget(controls)

        if not _HAS_AUDIO:
            self.lbl_status.text = ("Аудиозахват/FFT недоступны. "
                                    "На Android используйте AudioRecord (pyjnius) или установите sounddevice/scipy).")

    def _make_pill_button(self, icon_key: str, text: str, base_rgba, down_rgba, text_color=(1, 1, 1, 1)) -> Button:
        from kivy.uix.floatlayout import FloatLayout

        btn = Button(text="", font_size=18, bold=True)
        btn.background_normal = ""
        btn.background_down = ""
        btn.background_color = (0, 0, 0, 0)
        btn.size_hint_y = None
        btn.height = 56

        # ---- фон ----
        with btn.canvas.before:
            shadow_c = Color(0, 0, 0, 0.35);
            shadow = RoundedRectangle(radius=[28, 28, 28, 28])
            bg_c = Color(*base_rgba);
            bg = RoundedRectangle(radius=[28, 28, 28, 28])
            ring_c = Color(1, 1, 1, 0.08);
            ring = RoundedRectangle(radius=[28, 28, 28, 28])

        def _repaint(*_):
            shadow.pos = (btn.x, btn.y - 3);
            shadow.size = (btn.width, btn.height)
            bg.pos = btn.pos;
            bg.size = btn.size
            ring.pos = (btn.x + 1, btn.y + 1);
            ring.size = (btn.width - 2, btn.height - 2)

        def _state(*_):
            bg_c.rgba = down_rgba if btn.state == "down" else base_rgba
            ring_c.a = 0.14 if btn.state == "down" else 0.08

        btn.bind(pos=_repaint, size=_repaint, state=_state);
        _repaint();
        _state()

        # ---- слой контента ----
        layer = FloatLayout(size_hint=(None, None))

        def _sync_layer(*_):
            layer.pos = btn.pos
            layer.size = btn.size

        btn.bind(pos=_sync_layer, size=_sync_layer);
        _sync_layer()

        # ИКОНКА (слева, по центру по вертикали)
        def _res(p): return resource_find(p) or p

        normal, active = ICON.get(icon_key, ("", ""))
        img = Image(source=_res(normal), keep_ratio=True, allow_stretch=False, size_hint=(None, None))
        LEFT_PAD = 16

        def _place_icon(*_):
            side = int(layer.height * 0.55)
            img.size = (side, side)
            img.pos = (layer.x + LEFT_PAD, layer.center_y - side / 2)

        layer.bind(pos=_place_icon, size=_place_icon);
        _place_icon()

        def _swap_icon(*_):
            a = _res(active)
            img.source = a if (btn.state == "down" and a and os.path.exists(a)) else _res(normal)

        btn.bind(state=_swap_icon);
        _swap_icon()

        # ТЕКСТ (строго по центру всей кнопки)
        lbl = Label(text=text, font_size=18, color=text_color,
                    size_hint=(None, None), halign="center", valign="middle")

        def _place_label(*_):
            lbl.size = layer.size  # занимает всю кнопку
            lbl.center = layer.center  # центр в центре кнопки
            lbl.text_size = lbl.size  # дозволяет центровку

        layer.bind(pos=_place_label, size=_place_label);
        _place_label()

        layer.add_widget(lbl)  # сначала текст (во ВСЮ кнопку)
        layer.add_widget(img)  # сверху слева иконка (текст остаётся видим)
        btn.add_widget(layer)
        return btn

    # ---------- Геометрия ----------
    def _resolve_img(self, path_str: str) -> str:
        found = resource_find(path_str)
        if found and os.path.exists(found):
            return found
        candidate = (IMG_DIR / Path(path_str).name).as_posix()
        return candidate if os.path.exists(candidate) else ""

    def _img_draw_rect(self):
        tex = self.head_img.texture
        if not tex:
            return None
        area_w, area_h = self.img_wrap.width, self.img_wrap.height
        tex_w, tex_h = tex.size
        base_scale = min(area_w / tex_w, area_h / tex_h, 1.0)
        scale = base_scale * HEAD_SCALE
        draw_w, draw_h = tex_w * scale, tex_h * scale
        draw_x = self.img_wrap.center_x - draw_w/2
        draw_y = self.img_wrap.center_y - draw_h/2
        return draw_x, draw_y, draw_w, draw_h

    def _layout_image_and_pegs(self):
        rect = self._img_draw_rect()
        if not rect:
            return
        draw_x, draw_y, draw_w, draw_h = rect
        self.head_img.size = (draw_w, draw_h)
        self.head_img.pos  = (draw_x, draw_y)

        base_offset = 0.045 * min(draw_w, draw_h)
        for name, t in self._toggles.items():
            rx, ry = self.peg_centers[name]
            cx = draw_x + rx * draw_w
            cy = draw_y + ry * draw_h
            off_x = -base_offset if name in ("D3", "A2", "E4") else base_offset
            t.pos = (cx + off_x - t.width / 2, cy - t.height / 2)

    # ---------- Выбор струны ----------
    def _sync_toggle_state(self):
        for name, t in self._toggles.items():
            t.state = 'down' if name == self.current_string else 'normal'

    def _select_string(self, s):
        self.current_string = s
        self.target_freq = TUNING_FREQUENCIES[s]
        self.lbl_target.text = f"Цель: {self.target_freq:.2f} Hz"
        self._sync_toggle_state()

    # ---------- Аудио ----------
    def start_listen(self):
        if self._event:
            return
        if not _HAS_AUDIO:
            self.status_text = "Нет аудиодоступа"
            self.lbl_status.text = self.status_text
            return
        self.status_text = "Слушаю… Играйте открытую струну"
        self.lbl_status.text = self.status_text
        self.lbl_status.color = (1, 1, 1, 1)
        self._event = Clock.schedule_interval(self._tick_capture, self.duration + 0.05)

    def stop_listen(self):
        if self._event:
            self._event.cancel()
            self._event = None
        self.status_text = "Остановлено"
        self.lbl_status.text = self.status_text

    def on_leave_panel(self):
        self.stop_listen()

    def _tick_capture(self, *_):
        try:
            frames = int(self.duration * self.sample_rate)
            rec = sd.rec(frames, samplerate=self.sample_rate, channels=1, dtype='float32')
            sd.wait()
            sig = rec[:, 0]
            freq = analyze_frequency(sig, self.sample_rate)
            self.current_freq = float(freq)
            self.lbl_current.text = f"Текущая: {self.current_freq:.2f} Hz"

            delta = abs(self.current_freq - self.target_freq)
            if delta < 1.0:
                self.status_text = "Струна настроена ✅"
                self.lbl_status.color = (0.5, 1, 0.5, 1)
            elif self.current_freq < self.target_freq:
                self.status_text = "Подтяните струну (ниже цели)"
                self.lbl_status.color = (1, 1, 1, 1)
            else:
                self.status_text = "Ослабьте струну (выше цели)"
                self.lbl_status.color = (1, 1, 1, 1)
            self.lbl_status.text = self.status_text
        except Exception as e:
            self.status_text = f"Ошибка аудио: {e}"
            self.lbl_status.text = self.status_text
            self.lbl_status.color = (1, 0.6, 0.6, 1)
            self.stop_listen()
