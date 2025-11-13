# components/chords_screen.py
import sys
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
from kivy.uix.image import Image

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.resources import resource_find, resource_add_path
from kivy.graphics import Color, RoundedRectangle
from pathlib import Path

# --- опциональные зависимости ---
_HAS_SD = True
try:
    import sounddevice as sd
except Exception:
    _HAS_SD = False

_HAS_SCIPY = True
try:
    from scipy.signal import find_peaks
except Exception:
    _HAS_SCIPY = False

_HAS_MPL = True
try:
    import matplotlib.pyplot as plt
except Exception:
    _HAS_MPL = False

# --- пути к ассетам (чтобы Kivy находил файлы в assets/*) ---
APP_DIR   = Path(__file__).resolve().parents[1]
ICONS_DIR = APP_DIR / "assets" / "icons"
resource_add_path(str(ICONS_DIR))

# --- иконки ---
ICON = {
    "start": ("assets/icons/start.png"),
    "note":  ("assets/icons/note.png")
}

# --- константы анализа ---
SAMPLE_RATE = 44100
DURATION = 3.0
MIN_PEAK_HEIGHT_PERCENTILE = 85
PEAK_DISTANCE = 100
FREQ_TOLERANCE = 25
MIN_AMPLITUDE = 0.02
MIN_NOTES_FOR_CHORD = 3

# открытые струны (6 -> 1)
OPEN_STRING_FREQS = {6: 82.41, 5: 110.00, 4: 146.83, 3: 196.00, 2: 246.94, 1: 329.63}

# цвета
OK_COLOR = (0.6, 1.0, 0.6, 1)
WARN_COLOR = (1.0, 0.9, 0.6, 1)
ERR_COLOR = (1.0, 0.7, 0.7, 1)
TEXT_COLOR = (1, 1, 1, 1)


def get_fretted_freq(string_num: int, fret: int) -> float:
    return OPEN_STRING_FREQS[string_num] * (2 ** (fret / 12))


# --- база аккордов (сокр. для примера, можно расширять) ---
def _f(s, f): return get_fretted_freq(s, f)

CHORDS: Dict[str, Dict] = {
    "Em": {
        "tabs": ["0", "2", "2", "0", "0", "0"],
        "description": "E минор (Em)",
        "string_checks": {
            6: {"type": "open", "freq": 82.41},
            5: {"type": "fretted", "fret": 2, "freq": _f(5, 2)},
            4: {"type": "fretted", "fret": 2, "freq": _f(4, 2)},
            3: {"type": "open", "freq": 196.00},
            2: {"type": "open", "freq": 246.94},
            1: {"type": "open", "freq": 329.63},
        },
    },
    "Am": {
        "tabs": ["0", "1", "2", "2", "0", "0"],
        "description": "A минор (Am)",
        "string_checks": {
            5: {"type": "open", "freq": 110.00},
            4: {"type": "fretted", "fret": 2, "freq": _f(4, 2)},
            3: {"type": "fretted", "fret": 2, "freq": _f(3, 2)},
            2: {"type": "open", "freq": 246.94},
            1: {"type": "open", "freq": 329.63},
        },
    },
    "C": {
        "tabs": ["X", "3", "2", "0", "1", "0"],
        "description": "До мажор (C)",
        "string_checks": {
            5: {"type": "fretted", "fret": 3, "freq": _f(5, 3)},
            4: {"type": "fretted", "fret": 2, "freq": _f(4, 2)},
            3: {"type": "open", "freq": 196.00},
            2: {"type": "fretted", "fret": 1, "freq": _f(2, 1)},
            1: {"type": "open", "freq": 329.63},
        },
    },
    "G": {
        "tabs": ["3", "2", "0", "0", "3", "3"],
        "description": "Соль мажор (G)",
        "string_checks": {
            6: {"type": "fretted", "fret": 3, "freq": _f(6, 3)},
            5: {"type": "fretted", "fret": 2, "freq": _f(5, 2)},
            4: {"type": "open", "freq": 196.00},
            3: {"type": "open", "freq": 246.94},
            2: {"type": "fretted", "fret": 3, "freq": _f(2, 3)},
            1: {"type": "fretted", "fret": 3, "freq": _f(1, 3)},
        },
    },
    "D": {
        "tabs": ["X", "X", "0", "2", "3", "2"],
        "description": "Ре мажор (D)",
        "string_checks": {
            4: {"type": "open", "freq": 146.83},
            3: {"type": "fretted", "fret": 2, "freq": _f(3, 2)},
            2: {"type": "fretted", "fret": 3, "freq": _f(2, 3)},
            1: {"type": "fretted", "fret": 2, "freq": _f(1, 2)},
        },
    },
    "A": {
        "tabs": ["X", "0", "2", "2", "2", "0"],
        "description": "Ля мажор (A)",
        "string_checks": {
            5: {"type": "open", "freq": 110.00},
            4: {"type": "fretted", "fret": 2, "freq": _f(4, 2)},
            3: {"type": "fretted", "fret": 2, "freq": _f(3, 2)},
            2: {"type": "fretted", "fret": 2, "freq": _f(2, 2)},
            1: {"type": "open", "freq": 329.63},
        },
    },
    "E": {
        "tabs": ["0", "2", "2", "1", "0", "0"],
        "description": "Ми мажор (E)",
        "string_checks": {
            6: {"type": "open", "freq": 82.41},
            5: {"type": "fretted", "fret": 2, "freq": _f(5, 2)},
            4: {"type": "fretted", "fret": 2, "freq": _f(4, 2)},
            3: {"type": "fretted", "fret": 1, "freq": _f(3, 1)},
            2: {"type": "open", "freq": 246.94},
            1: {"type": "open", "freq": 329.63},
        },
    },
}


def _normalize(audio: np.ndarray) -> np.ndarray:
    audio = audio.astype(np.float32).flatten()
    maxv = np.max(np.abs(audio)) if audio.size else 0.0
    return audio / maxv if maxv > 0 else audio


def _find_peaks_numpy(mag: np.ndarray, distance: int, min_height: float) -> np.ndarray:
    n = mag.size
    peaks = []
    half = max(1, distance // 2)
    for i in range(half, n - half):
        m = mag[i]
        if m < min_height:
            continue
        if m == mag[i - 1] == mag[i + 1]:
            continue
        if (m > mag[i - half:i]).all() and (m > mag[i + 1:i + 1 + half]).all():
            peaks.append(i)
    return np.array(peaks, dtype=int)


def get_closest_freq(freq: float, target_freq: float, tolerance: float = FREQ_TOLERANCE) -> bool:
    return abs(freq - target_freq) < tolerance


def find_string_freq(freqs: np.ndarray, mags: np.ndarray, string_num: int, fret: Optional[int]) -> Tuple[Optional[float], float]:
    target = OPEN_STRING_FREQS[string_num] if fret in (None, 0) else get_fretted_freq(string_num, fret)
    found: List[Tuple[float, float]] = []
    for mult in [0.5, 1, 2, 3]:
        f0 = target * mult
        tol = FREQ_TOLERANCE * (1 + mult)
        mask = (freqs >= (f0 - tol)) & (freqs <= (f0 + tol))
        if not mask.any():
            continue
        idx = np.argmax(mags[mask])
        f_candidate = freqs[mask][idx]
        m_candidate = mags[mask][idx] / (mult ** 0.5)
        found.append((f_candidate, m_candidate))
    if not found:
        return None, 0.0
    best = max(found, key=lambda x: (-abs(x[0] - target), x[1]))
    return best[0], best[1]


def plot_spectrum(freqs: np.ndarray, mag: np.ndarray, peaks: np.ndarray, chord_name: str):
    if not _HAS_MPL:
        return
    desc = CHORDS[chord_name]["description"]
    plt.figure(figsize=(12, 6))
    plt.plot(freqs, mag, alpha=0.7, linewidth=1)
    plt.plot(freqs[peaks], mag[peaks], "x")
    plt.title(f"Спектр: {desc}")
    plt.xlabel("Частота, Гц")
    plt.ylabel("Амплитуда")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


@dataclass
class ChordCheckResult:
    success: bool
    messages: List[str]
    per_string: Dict[int, Dict]


def check_chord_accuracy(audio: np.ndarray, sample_rate: int, target_chord: str) -> ChordCheckResult:
    audio = _normalize(audio)
    if audio.size == 0 or np.max(np.abs(audio)) < MIN_AMPLITUDE:
        return ChordCheckResult(False, ["Звук не обнаружен. Проверьте микрофон и громкость."], {})

    mag_full = np.abs(np.fft.rfft(audio))
    freqs_full = np.fft.rfftfreq(len(audio), 1 / sample_rate)

    min_f, max_f = 60, 500
    mask = (freqs_full >= min_f) & (freqs_full <= max_f)
    freqs = freqs_full[mask]
    mag = mag_full[mask]

    min_h = float(np.percentile(mag, MIN_PEAK_HEIGHT_PERCENTILE))
    if _HAS_SCIPY:
        peaks, _ = find_peaks(mag, height=min_h, distance=PEAK_DISTANCE)
    else:
        peaks = _find_peaks_numpy(mag, distance=PEAK_DISTANCE, min_height=min_h)

    if peaks.size < MIN_NOTES_FOR_CHORD:
        return ChordCheckResult(False, [f"Обнаружено {peaks.size} нот(ы). Нужно ≥ {MIN_NOTES_FOR_CHORD}."], {})

    chord = CHORDS.get(target_chord)
    if not chord:
        return ChordCheckResult(False, [f"Аккорд {target_chord} не найден."], {})

    try:
        if _HAS_MPL and sys.platform in ("win32", "darwin", "linux"):
            plot_spectrum(freqs, mag, peaks, target_chord)
    except Exception:
        pass

    peak_freqs = freqs[peaks]
    peak_mags = mag[peaks]

    results = {}
    detected, correct_fretted, required_fretted, total_errors = 0, 0, 0, 0
    for s_num, info in chord["string_checks"].items():
        played_f, played_m = find_string_freq(peak_freqs, peak_mags, s_num, info.get("fret"))
        if info["type"] == "fretted":
            required_fretted += 1

        if played_f is not None:
            detected += 1
            is_ok = get_closest_freq(played_f, info["freq"])
            results[s_num] = {"correct": is_ok, "played": played_f, "expected": info["freq"],
                              "type": info["type"], "fret": info.get("fret")}
            if is_ok and info["type"] == "fretted":
                correct_fretted += 1
            elif not is_ok:
                total_errors += 1
        else:
            results[s_num] = {"correct": False, "played": None, "expected": info["freq"],
                              "type": info["type"], "fret": info.get("fret"), "error": "no_sound"}
            total_errors += 1 if info["type"] == "fretted" else 0.5

    success = (correct_fretted == required_fretted) and (total_errors <= 2)

    messages: List[str] = []
    if success:
        messages.append("Аккорд засчитан ✅" if total_errors else "Отлично! Аккорд сыгран идеально! ✅")
    else:
        messages.append("Есть проблемы с аккордом.")

    tuning, fingering, technique = [], [], []
    for s_num, res in results.items():
        info = chord["string_checks"][s_num]
        if not res["correct"]:
            if res.get("error") == "no_sound":
                msg = f"Струна {s_num} не обнаружена (ждём ~ {info['freq']:.1f} Гц)"
                if info["type"] == "fretted":
                    msg += f", лад {info['fret']}"
                    fingering.append(f"• Прижмите {s_num}-ю струну на {info['fret']} ладу")
                else:
                    technique.append(f"• Ударьте по {s_num}-й струне ровнее/сильнее")
                messages.append(msg)
            else:
                if info["type"] == "open":
                    tuning.append(f"• Подстройте {s_num}-ю: сейчас {res['played']:.1f} Гц, нужно {res['expected']:.1f} Гц")
                else:
                    fingering.append(f"• Точнее зажмите {s_num}-ю на {info['fret']} ладу (сейчас {res['played']:.1f} Гц)")

    if tuning:
        messages.append("\nРекомендации по настройке:"); messages.extend(tuning)
    if fingering:
        messages.append("\nПостановка пальцев:"); messages.extend(fingering)
    if technique:
        messages.append("\nТехника извлечения:"); messages.extend(technique)
    if not success:
        messages += ["\nОбщие советы:",
                     "• Прижимайте ближе к ладу (но не по самому ладу).",
                     "• Следите, чтобы пальцы не глушили соседние струны.",
                     "• Снимайте звук всеми нужными струнами."]

    return ChordCheckResult(success, messages, results)


def show_chord_tab(chord_name: str) -> List[str]:
    chord = CHORDS.get(chord_name)
    if not chord:
        return ["Аккорд не найден."]
    lines = [f"{chord['description']} — аппликатура (6→1):"]
    for i, tab in enumerate(chord["tabs"]):
        s_num = 6 - i
        if tab == "X":
            lines.append(f"Струна {s_num}: не играть")
        elif tab == "0":
            lines.append(f"Струна {s_num}: открытая")
        else:
            lines.append(f"Струна {s_num}: {tab} лад")
    return lines


# ============ UI панель с адаптивной таблицей (горизонтальный скролл) ============
class ChordsPanel(BoxLayout):
    current_chord = StringProperty("Em")
    status_text = StringProperty("Готово к записи")
    msg_area = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [16, 16, 16, 12]
        self.spacing = 10

        # ---- верх: выбор аккорда + действия (пилюли) ----
        header = BoxLayout(size_hint_y=None, height=64, spacing=10)

        self.dd = DropDown()
        for name in CHORDS.keys():
            b = Button(text=name, size_hint_y=None, height=44)
            b.bind(on_release=lambda btn: self._select_chord(btn.text))
            self.dd.add_widget(b)

        self.btn_chord = Button(text=f"Аккорд: {self.current_chord}",
                                size_hint=(None, None), height=56, width=180)
        self.btn_chord.bind(on_release=self.dd.open)
        self.dd.bind(on_select=lambda inst, x: setattr(self.btn_chord, 'text', f"Аккорд: {x}"))
        header.add_widget(self.btn_chord)

        # жёлтая «Записать» (start.png)
        btn_rec = self._make_pill_button(
            icon_key="start", text="",
            base_rgba=(0.98, 0.78, 0.10, 1), down_rgba=(0.88, 0.68, 0.08, 1),
            text_color=(0.08, 0.08, 0.12, 1)
        )
        btn_rec.bind(on_release=lambda *_: self.record_once())
        header.add_widget(btn_rec)

        # синяя «Аппликатура» (note.png) — цвет как «Стоп»
        btn_tabs = self._make_pill_button(
            icon_key="note", text="",
            base_rgba=(0.05, 0.20, 0.30, 1), down_rgba=(0.04, 0.16, 0.26, 1),
            text_color=(1, 1, 1, 1)
        )
        btn_tabs.bind(on_release=lambda *_: self._print_tabs())
        header.add_widget(btn_tabs)

        # ---- статус ----
        self.lbl_status = Label(text=self.status_text, size_hint_y=None, height=28, color=TEXT_COLOR)

        # ---- таблица результатов: горизонтальный скролл ----
        self.table_cols = 4
        self.col_widths = [90, 150, 150, 200]

        self.table_scroller = ScrollView(size_hint=(1, None), height=220,
                                         do_scroll_x=True, do_scroll_y=True, bar_width=8)
        self.grid = GridLayout(cols=self.table_cols, spacing=6,
                               size_hint=(None, None))
        self.grid.bind(minimum_height=self.grid.setter('height'),
                       minimum_width=self.grid.setter('width'))
        self.table_scroller.add_widget(self.grid)

        # ---- сообщения ----
        self.msg_scroller = ScrollView(size_hint=(1, 1), do_scroll_y=True, bar_width=8)
        self.msg_box = GridLayout(cols=1, size_hint_y=None, spacing=4, padding=[2, 2, 2, 8])
        self.msg_box.bind(minimum_height=self.msg_box.setter('height'))
        self.msg_scroller.add_widget(self.msg_box)

        # сборка
        self.add_widget(header)
        self.add_widget(self.lbl_status)
        self.add_widget(Label(text="Результаты по струнам:", size_hint_y=None, height=24, color=TEXT_COLOR))
        self._setup_grid_header()
        self.add_widget(self.table_scroller)
        self.add_widget(Label(text="Сообщения:", size_hint_y=None, height=24, color=TEXT_COLOR))
        self.add_widget(self.msg_scroller)

        Window.bind(size=lambda *_: self._recalc_col_widths())

        if not _HAS_SD:
            self._push_msg("⚠️ Микрофон (sounddevice) недоступен. На Android используйте AudioRecord через pyjnius.",
                           color=WARN_COLOR)

    # ---------- фабрика «пилюли» с иконкой слева и центровкой текста ----------
    def _make_pill_button(self, icon_key: str, text: str, base_rgba, down_rgba, text_color=(1, 1, 1, 1)) -> Button:
        btn = Button(text="", font_size=18, bold=True)
        btn.background_normal = ""
        btn.background_down   = ""
        btn.background_color  = (0, 0, 0, 0)
        btn.size_hint_y = None
        btn.height = 56

        # фон
        with btn.canvas.before:
            shadow_c = Color(0, 0, 0, 0.35); shadow = RoundedRectangle(radius=[28, 28, 28, 28])
            bg_c     = Color(*base_rgba);     bg     = RoundedRectangle(radius=[28, 28, 28, 28])
            ring_c   = Color(1, 1, 1, 0.08);  ring   = RoundedRectangle(radius=[28, 28, 28, 28])
        def _repaint(*_):
            shadow.pos=(btn.x, btn.y-3); shadow.size=(btn.width, btn.height)
            bg.pos=btn.pos; bg.size=btn.size
            ring.pos=(btn.x+1, btn.y+1); ring.size=(btn.width-2, btn.height-2)
        def _state(*_):
            bg_c.rgba = down_rgba if btn.state=="down" else base_rgba
            ring_c.a  = 0.14 if btn.state=="down" else 0.08
        btn.bind(pos=_repaint, size=_repaint, state=_state); _repaint(); _state()

        # слой контента
        layer = FloatLayout(size_hint=(None, None))
        def _sync_layer(*_):
            layer.pos = btn.pos
            layer.size = btn.size
        btn.bind(pos=_sync_layer, size=_sync_layer); _sync_layer()

        def _res(p): return resource_find(p) or p

        def _icon_pair(key):
            val = ICON.get(key, ("", ""))
            if isinstance(val, (tuple, list)):
                if len(val) == 1:
                    return val[0], val[0]
                return val[0], val[1]
            if isinstance(val, str):
                return val, val
            return "", ""

        normal, active = _icon_pair(icon_key)

        # иконка (слева, центр по вертикали)
        img = Image(source=_res(normal), keep_ratio=True, allow_stretch=False, size_hint=(None, None))
        LEFT_PAD = 16
        def _place_icon(*_):
            side = int(layer.height * 0.55)
            img.size = (side, side)
            img.pos  = (layer.x + LEFT_PAD, layer.center_y - side/2)
        layer.bind(pos=_place_icon, size=_place_icon); _place_icon()

        def _swap_icon(*_):
            a = _res(active)
            img.source = a if (btn.state == "down" and a) else _res(normal)
        btn.bind(state=_swap_icon); _swap_icon()

        # текст (строго по центру)
        lbl = Label(text=text, font_size=18, color=text_color,
                    size_hint=(None, None), halign="center", valign="middle")
        def _place_label(*_):
            lbl.size = layer.size
            lbl.center = layer.center
            lbl.text_size = lbl.size
        layer.bind(pos=_place_label, size=_place_label); _place_label()

        layer.add_widget(lbl)
        layer.add_widget(img)
        btn.add_widget(layer)
        return btn

    # ---------- адаптив: ширины колонок ----------
    def _recalc_col_widths(self):
        w = Window.width
        if w < 520:
            self.col_widths = [70, 120, 120, 160]
        elif w < 800:
            self.col_widths = [80, 140, 140, 180]
        else:
            self.col_widths = [90, 160, 160, 220]
        self._apply_col_widths()

    def _apply_col_widths(self):
        for idx, child in enumerate(reversed(self.grid.children)):
            col = (self.table_cols - 1) - (idx % self.table_cols)
            child.size_hint_x = None
            child.width = self.col_widths[col]
            child.text_size = (child.width, child.height)
        self.grid.width = sum(self.col_widths) + (self.table_cols - 1) * self.grid.spacing[0]

    # ---------- построение шапки таблицы ----------
    def _setup_grid_header(self):
        self.grid.clear_widgets()
        for head in ("Струна", "Ожидаемая, Гц", "Обнаружено, Гц", "Статус"):
            l = Label(text=f"[b]{head}[/b]", markup=True, size_hint_y=None, height=28, color=TEXT_COLOR)
            self.grid.add_widget(l)
        Clock.schedule_once(lambda *_: (self._recalc_col_widths(), None), 0)

    # ---------- вспомогательные ----------
    def _select_chord(self, name: str):
        self.current_chord = name
        self.dd.select(name)

    def _push_msg(self, text: str, color=TEXT_COLOR):
        self.msg_box.add_widget(Label(text=text, size_hint_y=None, height=22, color=color,
                                      halign='left', valign='middle', text_size=(Window.width - 48, None)))
        Clock.schedule_once(lambda *_: self._scroll_to_end(), 0)

    def _scroll_to_end(self):
        self.msg_scroller.scroll_y = 0

    def _print_tabs(self):
        self._push_msg(f"[b]{self.current_chord}[/b] — аппликатура", color=TEXT_COLOR)
        for line in show_chord_tab(self.current_chord):
            self._push_msg(line, color=TEXT_COLOR)

    # ---------- запись и анализ ----------
    def record_once(self):
        if not _HAS_SD:
            self.status_text = "Нет доступа к аудио"
            self.lbl_status.text = self.status_text
            self.lbl_status.color = ERR_COLOR
            return

        self.status_text = "Запись… Играйте аккорд"
        self.lbl_status.text = self.status_text
        self.lbl_status.color = TEXT_COLOR
        self._setup_grid_header()

        Clock.schedule_once(lambda *_: self._do_record_and_check(), 0)

    def _do_record_and_check(self):
        try:
            frames = int(DURATION * SAMPLE_RATE)
            audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype='float32')
            sd.wait()
        except Exception as e:
            self.status_text = f"Ошибка аудио: {e}"
            self.lbl_status.text = self.status_text
            self.lbl_status.color = ERR_COLOR
            return

        self.status_text = "Анализ…"
        self.lbl_status.text = self.status_text

        result = check_chord_accuracy(audio, SAMPLE_RATE, self.current_chord)

        chord = CHORDS[self.current_chord]
        for s_num in [6, 5, 4, 3, 2, 1]:
            info = chord["string_checks"].get(s_num)
            if not info:
                continue
            expected = info["freq"]
            res = result.per_string.get(s_num, {"correct": False, "played": None})
            played = res["played"]
            status = "OK" if res.get("correct") else ("нет звука" if played is None else "нужна корректировка")
            col = OK_COLOR if res.get("correct") else ERR_COLOR

            self.grid.add_widget(Label(text=str(s_num), size_hint_y=None, height=26, color=TEXT_COLOR))
            self.grid.add_widget(Label(text=f"{expected:.1f}", size_hint_y=None, height=26, color=TEXT_COLOR))
            self.grid.add_widget(Label(text=("-" if played is None else f"{played:.1f}"),
                                       size_hint_y=None, height=26, color=TEXT_COLOR))
            self.grid.add_widget(Label(text=status, size_hint_y=None, height=26, color=col))

        self._apply_col_widths()

        self._push_msg("—" * 30, color=TEXT_COLOR)
        for line in result.messages:
            self._push_msg(line, color=(OK_COLOR if result.success else TEXT_COLOR))

        if result.success:
            self.status_text = "Готово: аккорд распознан ✅"
            self.lbl_status.color = OK_COLOR
        else:
            self.status_text = "Готово: есть замечания"
            self.lbl_status.color = WARN_COLOR
        self.lbl_status.text = self.status_text

    def on_leave_panel(self):
        pass
