import numpy as np
import sounddevice as sd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import librosa
import librosa.display

chords_dict = {
    "C": [130.81, 164.81, 196.00, 261.63, 329.63],  # C3, E3, G3, C4, E4
    "Cm": [130.81, 155.56, 196.00, 261.63, 311.13],  # C3, Eb3, G3, C4, Eb4
    "D": [146.83, 185.00, 220.00, 293.66, 369.99, 440.00],  # D3, F#3, A3, D4, F#4, A4
    "Dm": [146.83, 174.61, 220.00, 293.66, 349.23],  # D3, F3, A3, D4, F4
    "E": [82.41, 123.47, 164.81, 196.00, 329.63],  # E2, B2, E3, G#3, E4
    "Em": [82.41, 123.47, 164.81, 196.00, 329.63, 196.00],  # E2, B2, E3, G3, E4, G3
    "F": [87.31, 130.81, 174.61, 261.63],
    "G": [98.00, 123.47, 146.83, 196.00, 246.94, 392.00],
    "A": [110.00, 220.00, 277.18, 329.63],  # A2, A3, C#4, E4
    "Am": [110.00, 164.81, 220.00, 261.63, 329.63],  # A2, E3, A3, C4, E4
}

distinctive_notes = {
    "C": [196.00, 261.63],  # G3, C4 - ноты, характерные для C
    "Em": [196.00, 82.41],  # G3, E2 - ноты, характерные для Em
    "D": [146.83, 369.99],  # D3, F#4 - ноты, характерные для D
    "G": [98.00, 392.00],  # G2, G4 - ноты, характерные для G
}


def record_audio(duration=2, sample_rate=44100):
    """Записывает звук с микрофона."""
    print("Начало записи...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    print("Запись завершена.")
    return audio.flatten()


def compute_spectrum(audio, sample_rate):
    """Вычисляет спектр сигнала с помощью БПФ."""
    fft_data = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), d=1.0 / sample_rate)
    magnitudes = np.abs(fft_data)
    return freqs, magnitudes


def find_spectral_peaks(freqs, magnitudes, num_peaks=30):
    """Находит наиболее выраженные пики в спектре."""
    peak_indices, _ = find_peaks(magnitudes, height=0)
    sorted_peaks = peak_indices[np.argsort(magnitudes[peak_indices])[::-1]]
    top_peaks = sorted_peaks[:num_peaks]
    return freqs[top_peaks], magnitudes[top_peaks]


def compare_with_chords(peak_freqs, peak_mags, chords_dict, distinctive_notes, tolerance=8.0):
    """Сравнивает найденные частоты с частотами аккордов."""
    results = {}
    for chord_name, chord_freqs in chords_dict.items():
        matched_notes = 0
        weighted_match = 0
        matched_freqs = []

        for note_freq in chord_freqs:
            for i, peak in enumerate(peak_freqs):
                if abs(note_freq - peak) < tolerance:
                    matched_notes += 1
                    matched_freqs.append((note_freq, peak))
                    weighted_match += peak_mags[i]
                    break

        match_percent = (matched_notes / len(chord_freqs)) * 100 if len(chord_freqs) > 0 else 0
        results[chord_name] = {
            'matched': matched_notes,
            'total': len(chord_freqs),
            'percent': match_percent,
            'weighted': weighted_match,
            'matched_freqs': matched_freqs
        }

    # Добавляем бонусы за характерные ноты
    for chord_name, distinctive_freqs in distinctive_notes.items():
        if chord_name in results:
            distinctive_count = 0
            for note in distinctive_freqs:
                if any(abs(note - peak) < tolerance for peak in peak_freqs):
                    distinctive_count += 1
            results[chord_name]['weighted'] += distinctive_count * 30

    return results


def visualize_results(audio, duration, sample_rate, freqs, magnitudes, peak_freqs, peak_mags, results):
    """Визуализирует результаты анализа."""
    plt.figure(figsize=(14, 10))

    # Временной сигнал
    plt.subplot(3, 2, 1)
    plt.plot(np.linspace(0, duration, len(audio)), audio)
    plt.title("Временной сигнал")
    plt.xlabel("Время (с)")
    plt.ylabel("Амплитуда")

    # Спектр (БПФ)
    plt.subplot(3, 2, 2)
    plt.plot(freqs[:5000], magnitudes[:5000])
    plt.title("Спектр сигнала (БПФ)")
    plt.xlabel("Частота (Гц)")
    plt.ylabel("Амплитуда")
    plt.grid(True)

    # Основные пики
    plt.subplot(3, 2, 3)
    plt.stem(peak_freqs, peak_mags, linefmt='r-', markerfmt='ro', basefmt='b-')
    plt.title("Основные обнаруженные частотные пики")
    plt.xlabel("Частота (Гц)")
    plt.ylabel("Амплитуда")
    plt.xlim(0, 1000)
    plt.grid(True)

    # Спектрограмма
    plt.subplot(3, 2, 4)
    D = librosa.stft(audio)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    librosa.display.specshow(S_db, sr=sample_rate, x_axis='time', y_axis='hz')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Спектрограмма')

    # Процент схожести
    sorted_results = sorted(results.items(), key=lambda x: x[1]['weighted'], reverse=True)
    chords = [chord for chord, _ in sorted_results]
    percents = [data['percent'] for _, data in sorted_results]

    plt.subplot(3, 1, 3)
    bars = plt.bar(chords, percents, color=get_cmap('viridis')(np.linspace(0, 1, len(chords))))
    for bar, percent in zip(bars, percents):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f'{percent:.1f}%', ha='center', va='bottom')

    plt.title('Процент схожести с аккордами')
    plt.xlabel('Аккорд')
    plt.ylabel('Процент схожести (%)')
    plt.ylim(0, 110)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Выделение лучшего аккорда
    if results:
        best_chord = max(results, key=lambda x: results[x]['weighted'])
        best_idx = chords.index(best_chord)
        bars[best_idx].set_color('crimson')
        bars[best_idx].set_edgecolor('black')
        bars[best_idx].set_linewidth(1.5)

    plt.tight_layout()
    plt.savefig('chord_analysis.png', dpi=150)
    plt.show()


def print_results(results):
    """Выводит результаты анализа."""
    sorted_results = sorted(results.items(), key=lambda x: x[1]['weighted'], reverse=True)
    best_chord, best_match = sorted_results[0]

    if best_match['matched'] >= 2:
        print(f"Предположительно звучит аккорд {best_chord} "
              f"(совпало {best_match['matched']} из {best_match['total']} нот, "
              f"{best_match['percent']:.1f}% схожести).")
        print("Совпавшие частоты (ожидаемая → обнаруженная):")
        for expected, found in best_match['matched_freqs']:
            print(f"{expected:.2f} → {found:.2f} Гц")
        print("\nТоп-3 кандидата:")
        for chord, data in sorted_results[:3]:
            print(f"{chord}: {data['matched']} из {data['total']} нот, {data['percent']:.1f}% схожести")
    else:
        print("Не удалось однозначно определить аккорд.")


def record_and_recognize_chord(duration=2, sample_rate=44100):
    """Основная функция для записи и распознавания аккорда."""
    # Запись звука
    audio = record_audio(duration, sample_rate)

    # Вычисление спектра
    freqs, magnitudes = compute_spectrum(audio, sample_rate)

    # Поиск пиков
    peak_freqs, peak_mags = find_spectral_peaks(freqs, magnitudes)

    # Сравнение с аккордами
    results = compare_with_chords(peak_freqs, peak_mags, chords_dict, distinctive_notes)

    # Вывод результатов
    print_results(results)

    # Визуализация
    visualize_results(audio, duration, sample_rate, freqs, magnitudes, peak_freqs, peak_mags, results)


if __name__ == "__main__":
    record_and_recognize_chord()