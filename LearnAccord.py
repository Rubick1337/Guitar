import numpy as np
import sounddevice as sd
from scipy.signal import find_peaks
import librosa
import matplotlib.pyplot as plt

# Настройки анализа
SAMPLE_RATE = 44100
DURATION = 3
MIN_PEAK_HEIGHT_PERCENTILE = 85
PEAK_DISTANCE = 100
FREQ_TOLERANCE = 25
MIN_AMPLITUDE = 0.02
MIN_NOTES_FOR_CHORD = 3

# Частоты открытых струн гитары (6-я → 1-я)
OPEN_STRING_FREQS = {
    6: 82.41,  # Ми
    5: 110.00,  # Ля
    4: 146.83,  # Ре
    3: 196.00,  # Соль
    2: 246.94,  # Си
    1: 329.63  # Ми
}

# Цвета для разных струн на графике
STRING_COLORS = {
    6: '#FF0000',  # Красный
    5: '#FFA500',  # Оранжевый
    4: '#FFFF00',  # Желтый
    3: '#00FF00',  # Зеленый
    2: '#0000FF',  # Синий
    1: '#800080'  # Фиолетовый
}


def get_fretted_freq(string_num, fret):
    """Вычисляет частоту для зажатой струны на указанном ладу"""
    return OPEN_STRING_FREQS[string_num] * (2 ** (fret / 12))


CHORDS = {
    "Em": {
        "freqs": [82.41, 123.47, 164.81, 196.00, 329.63],
        "tabs": ["0", "2", "2", "0", "0", "0"],
        "description": "E минор (Em)",
        "string_checks": {
            6: {"type": "open", "freq": 82.41},
            5: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(5, 2)},
            4: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(4, 2)},
            3: {"type": "open", "freq": 196.00},
            2: {"type": "open", "freq": 246.94},
            1: {"type": "open", "freq": 329.63}
        }
    },
    "Am": {
        "freqs": [110.00, 164.81, 220.00, 261.63, 329.63],
        "tabs": ["0", "1", "2", "2", "0", "0"],
        "description": "A минор (Am)",
        "string_checks": {
            5: {"type": "open", "freq": 110.00},
            4: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(4, 2)},
            3: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(3, 2)},
            2: {"type": "open", "freq": 246.94},
            1: {"type": "open", "freq": 329.63}
        }
    },
    "C": {
        "freqs": [130.81, 164.81, 196.00, 261.63, 329.63],
        "tabs": ["X", "3", "2", "0", "1", "0"],
        "description": "До мажор (C)",
        "string_checks": {
            5: {"type": "fretted", "fret": 3, "freq": get_fretted_freq(5, 3)},
            4: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(4, 2)},
            3: {"type": "open", "freq": 196.00},
            2: {"type": "fretted", "fret": 1, "freq": get_fretted_freq(2, 1)},
            1: {"type": "open", "freq": 329.63}
        }
    },
    "G": {
        "freqs": [98.00, 123.47, 196.00, 246.94, 392.00],
        "tabs": ["3", "2", "0", "0", "3", "3"],
        "description": "Соль мажор (G)",
        "string_checks": {
            6: {"type": "fretted", "fret": 3, "freq": get_fretted_freq(6, 3)},
            5: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(5, 2)},
            4: {"type": "open", "freq": 196.00},
            3: {"type": "open", "freq": 246.94},
            2: {"type": "fretted", "fret": 3, "freq": get_fretted_freq(2, 3)},
            1: {"type": "fretted", "fret": 3, "freq": get_fretted_freq(1, 3)}
        }
    },
    "D": {
        "freqs": [146.83, 185.00, 220.00, 293.66],
        "tabs": ["X", "X", "0", "2", "3", "2"],
        "description": "Ре мажор (D)",
        "string_checks": {
            4: {"type": "open", "freq": 146.83},
            3: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(3, 2)},
            2: {"type": "fretted", "fret": 3, "freq": get_fretted_freq(2, 3)},
            1: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(1, 2)}
        }
    },
    "A": {
        "freqs": [110.00, 164.81, 220.00, 277.18, 329.63],
        "tabs": ["X", "0", "2", "2", "2", "0"],
        "description": "Ля мажор (A)",
        "string_checks": {
            5: {"type": "open", "freq": 110.00},
            4: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(4, 2)},
            3: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(3, 2)},
            2: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(2, 2)},
            1: {"type": "open", "freq": 329.63}
        }
    },
    "E": {
        "freqs": [82.41, 123.47, 164.81, 207.65, 329.63],
        "tabs": ["0", "2", "2", "1", "0", "0"],
        "description": "Ми мажор (E)",
        "string_checks": {
            6: {"type": "open", "freq": 82.41},
            5: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(5, 2)},
            4: {"type": "fretted", "fret": 2, "freq": get_fretted_freq(4, 2)},
            3: {"type": "fretted", "fret": 1, "freq": get_fretted_freq(3, 1)},
            2: {"type": "open", "freq": 246.94},
            1: {"type": "open", "freq": 329.63}
        }
    }
}


def show_chord_tab(chord_name):
    """Показывает аппликатуру аккорда с подсказками"""
    chord = CHORDS.get(chord_name)
    if not chord:
        print("Аккорд не найден!")
        return

    print(f"\n{chord['description']} — аппликатура (6-я → 1-я струна):")
    for i, tab in enumerate(chord["tabs"]):
        string_num = 6 - i
        if tab == "X":
            print(f"Струна {string_num}: не играть")
        else:
            print(f"Струна {string_num}: {tab} лад" if tab != "0" else f"Струна {string_num}: открытая")


def plot_spectrum(freqs, fft, peaks, chord_info):
    plt.figure(figsize=(14, 7))

    # Основной график спектра
    plt.plot(freqs, fft, label='Спектр', color='gray', alpha=0.6, linewidth=1)
    plt.plot(freqs[peaks], fft[peaks], "x", label='Обнаруженные пики', color='black', markersize=8)

    # Добавляем подписи для струн
    for string_num, string_info in chord_info["string_checks"].items():
        target_freq = string_info["freq"]
        color = STRING_COLORS.get(string_num, '#FF0000')

        # Находим ближайший пик к целевой частоте
        closest_peak = None
        min_diff = float('inf')
        closest_peak_amp = 0

        for i, f in enumerate(freqs[peaks]):
            diff = abs(f - target_freq)
            if diff < min_diff:
                closest_peak = f
                closest_peak_amp = fft[peaks][i]
                min_diff = diff

        # Если нашли достаточно близкий пик
        if closest_peak and min_diff < FREQ_TOLERANCE * 1.5:
            label = f"{string_num} стр. ({target_freq:.1f} Гц)"
            if string_info["type"] == "fretted":
                label += f" лад {string_info['fret']}"

            plt.scatter(closest_peak, closest_peak_amp, color=color, s=150,
                        edgecolors='black', zorder=5)
            plt.text(closest_peak, closest_peak_amp * 1.15, label,
                     color=color, ha='center', va='bottom',
                     fontsize=10, weight='bold', bbox=dict(facecolor='white', alpha=0.7))

        # Вертикальная линия для целевой частоты
        plt.axvline(x=target_freq, color=color, linestyle='--', alpha=0.4, linewidth=1.5)

    plt.xlabel('Частота (Гц)', fontsize=12)
    plt.ylabel('Амплитуда', fontsize=12)
    plt.title(f'Спектр звука: {chord_info["description"]}', fontsize=14, pad=20)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.show()


def get_closest_freq(freq, target_freq, tolerance=FREQ_TOLERANCE):
    """Проверяет, соответствует ли частота целевой с учетом допуска"""
    return abs(freq - target_freq) < tolerance


def find_string_freq(freqs, mags, string_num, fret=None):
    """
    Находит частоту струны с учетом лада
    Возвращает (найденная_частота, амплитуда)
    """
    if fret is None or fret == 0:  # Открытая струна
        target_freq = OPEN_STRING_FREQS[string_num]
    else:  # Зажатая струна
        target_freq = get_fretted_freq(string_num, fret)

    # Ищем основной тон и гармоники (учитываем октавы)
    found_freqs = []
    for oct_mult in [0.5, 1, 2, 3]:  # Проверяем октавы
        octave_freq = target_freq * oct_mult
        for f, m in zip(freqs, mags):
            if get_closest_freq(f, octave_freq, FREQ_TOLERANCE * (1 + oct_mult)):
                # Взвешиваем амплитуду в зависимости от октавы
                weighted_mag = m / (oct_mult ** 0.5)
                found_freqs.append((f, weighted_mag))

    if not found_freqs:
        return None, 0

    # Возвращаем наиболее близкую к целевой частоте с наибольшей взвешенной амплитудой
    best_freq, best_mag = max(found_freqs, key=lambda x: (-abs(x[0] - target_freq), x[1]))
    return best_freq, best_mag


def check_chord_accuracy(audio, sample_rate, target_chord):
    try:
        # Нормализация и проверка громкости
        audio = librosa.util.normalize(audio.flatten())
        max_amplitude = np.max(np.abs(audio))

        if max_amplitude < MIN_AMPLITUDE:
            return False, ["Звук не обнаружен. Проверьте микрофон и громкость."]

        # Быстрое преобразование Фурье
        fft = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1 / sample_rate)

        # Фильтрация частот
        min_freq = 60
        max_freq = 500
        valid_mask = (freqs >= min_freq) & (freqs <= max_freq)
        freqs = freqs[valid_mask]
        fft = fft[valid_mask]

        # Поиск пиков
        min_peak_height = np.percentile(fft, MIN_PEAK_HEIGHT_PERCENTILE)
        peaks, properties = find_peaks(fft, height=min_peak_height, distance=PEAK_DISTANCE)

        # Проверка количества обнаруженных нот
        if len(peaks) < MIN_NOTES_FOR_CHORD:
            return False, [f"Обнаружено только {len(peaks)} нот. Для аккорда нужно минимум {MIN_NOTES_FOR_CHORD}."]

        peak_freqs = freqs[peaks]
        peak_mags = fft[peaks]

        chord_info = CHORDS.get(target_chord)
        if not chord_info:
            return False, [f"Аккорд {target_chord} не найден в базе."]

        # Визуализация спектра
        plot_spectrum(freqs, fft, peaks, chord_info)

        # Проверка каждой струны
        results = {}
        detected_notes = 0
        correct_fretted = 0
        required_fretted = 0
        total_errors = 0

        for string_num, string_info in chord_info["string_checks"].items():
            played_freq, played_mag = find_string_freq(peak_freqs, peak_mags,
                                                       string_num,
                                                       string_info.get("fret"))

            if string_info["type"] == "fretted":
                required_fretted += 1

            if played_freq is not None:
                detected_notes += 1
                is_correct = get_closest_freq(played_freq, string_info["freq"])
                results[string_num] = {
                    "correct": is_correct,
                    "played": played_freq,
                    "expected": string_info["freq"],
                    "type": string_info["type"],
                    "error": None if is_correct else "wrong_freq"
                }

                if is_correct and string_info["type"] == "fretted":
                    correct_fretted += 1
                elif not is_correct:
                    total_errors += 1
            else:
                results[string_num] = {
                    "correct": False,
                    "type": string_info["type"],
                    "error": "no_sound",
                    "expected": string_info["freq"]
                }
                if string_info["type"] == "fretted":
                    total_errors += 1
                else:
                    total_errors += 0.5  # Меньший вес ошибкам на открытых струнах

        # Основной критерий успеха: все зажатые струны правильные и не более 2 ошибок
        success = (correct_fretted == required_fretted) and (total_errors <= 2)

        # Формирование отчета
        all_errors = []
        tuning_suggestions = []
        fingering_suggestions = []
        technique_suggestions = []

        for string_num, result in results.items():
            string_info = chord_info["string_checks"][string_num]

            if not result["correct"]:
                if result["error"] == "no_sound":
                    error_msg = f"Струна {string_num} не обнаружена (должна быть {string_info['type']} "
                    if string_info["type"] == "fretted":
                        error_msg += f"на {string_info['fret']} ладу - {string_info['freq']:.1f} Гц)"
                        fingering_suggestions.append(
                            f"• Проверьте зажатие {string_num}-й струны на {string_info['fret']} ладу")
                    else:
                        error_msg += f"- {string_info['freq']:.1f} Гц)"
                        technique_suggestions.append(f"• Убедитесь, что вы ударяете по {string_num}-й струне")

                    all_errors.append(error_msg)
                else:
                    diff = abs(result["played"] - result["expected"])
                    if string_info["type"] == "open":
                        tuning_suggestions.append(
                            f"• Подстройте {string_num}-ю струну: сейчас {result['played']:.1f} Гц, должно быть {result['expected']:.1f} Гц")
                    else:
                        fingering_suggestions.append(
                            f"• Улучшите зажатие {string_num}-й струны на {string_info['fret']} ладу (сейчас {result['played']:.1f} Гц)")
            else:
                print(f"Струна {string_num}: OK ({result['played']:.1f} Гц)")

        if success:
            if total_errors == 0:
                return True, ["Отлично! Аккорд сыгран идеально!"]
            else:
                messages = ["Аккорд засчитан как правильно сыгранный, но есть небольшие неточности:"]
                if tuning_suggestions:
                    messages.append("\nРекомендации по настройке:")
                    messages.extend(tuning_suggestions)
                if fingering_suggestions:
                    messages.append("\nРекомендации по постановке пальцев:")
                    messages.extend(fingering_suggestions)
                return True, messages
        else:
            messages = ["Обнаружены проблемы с аккордом:"] + all_errors

            if correct_fretted < required_fretted:
                messages.append(
                    f"\nОшибка: Не все нужные струны правильно зажаты ({correct_fretted} из {required_fretted})")

            if tuning_suggestions:
                messages.append("\nРекомендации по настройке:")
                messages.extend(tuning_suggestions)

            if fingering_suggestions:
                messages.append("\nРекомендации по постановке пальцев:")
                messages.extend(fingering_suggestions)

            if technique_suggestions:
                messages.append("\nТехнические рекомендации:")
                messages.extend(technique_suggestions)

            messages.append("\nОбщие советы:")
            messages.append("• Убедитесь, что пальцы зажимают струны близко к ладу (но не на самом ладу)")
            messages.append("• Проверьте, что не задеваете соседние струны")
            messages.append("• Играйте аккорд четко, ударяя по всем нужным струнам одновременно")
            messages.append("• При дребезжании: сильнее прижмите струну или проверьте высоту струн")
            messages.append("• Для лучшего распознавания играйте ближе к звукоснимателю (если электрогитара)")

            return False, messages

    except Exception as e:
        return False, [f"Произошла ошибка при анализе: {str(e)}"]


def record_and_check_chord(target_chord):
    """Записывает и проверяет аккорд с улучшенной диагностикой"""
    chord = CHORDS.get(target_chord)
    if not chord:
        print("Неизвестный аккорд!")
        return

    print(f"\n=== Проверка аккорда {chord['description']} ===")
    show_chord_tab(target_chord)

    print("\nСоветы для лучшего распознавания:")
    print("- Играйте аккорд ближе к звукоснимателю (если электрогитара)")
    print("- Убедитесь, что все струны звучат четко")
    print("- Избегайте посторонних шумов во время записи")
    input("\nНажмите Enter, когда будете готовы играть...")

    print("\nЗаписываем звук... (играйте аккорд)")
    try:
        audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()

        print("Анализируем запись...")
        is_correct, messages = check_chord_accuracy(audio, SAMPLE_RATE, target_chord)

        print("\n=== Результат проверки ===")
        for msg in messages:
            print(msg)

        if not is_correct:
            print("\n=== Подсказка по исправлению ===")
            show_chord_tab(target_chord)
        else:
            print("\n=== Отличная работа! ===")
            print("Аккорд звучит правильно!")
    except Exception as e:
        print(f"\nОшибка: {str(e)}")
        print("Проверьте подключение микрофона и попробуйте еще раз")


def main():

    while True:
        print("\nВыберите аккорд для тренировки:")
        print("1 - Em (E минор)")
        print("2 - Am (A минор)")
        print("3 - C (До мажор)")
        print("4 - G (Соль мажор)")
        print("5 - D (Ре мажор)")
        print("6 - A (Ля мажор)")
        print("7 - E (Ми мажор)")
        print("0 - Выход")

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            record_and_check_chord("Em")
        elif choice == "2":
            record_and_check_chord("Am")
        elif choice == "3":
            record_and_check_chord("C")
        elif choice == "4":
            record_and_check_chord("G")
        elif choice == "5":
            record_and_check_chord("D")
        elif choice == "6":
            record_and_check_chord("A")
        elif choice == "7":
            record_and_check_chord("E")
        elif choice == "0":
            print("\nДо свидания! Успешных занятий!")
            print("======================================")
            break
        else:
            print("Некорректный ввод. Попробуйте ещё раз.")


if __name__ == "__main__":
    main()