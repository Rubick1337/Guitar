import numpy as np
import sounddevice as sd
from scipy.fftpack import fft

# Частоты нот для стандартного строя гитары (E2, A2, D3, G3, B3, E4)
TUNING_FREQUENCIES = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63
}
def record_audio(duration, sample_rate):
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return recording

def analyze_frequency(signal, sample_rate):
    n = len(signal)
    freq = np.fft.fftfreq(n, d=1/sample_rate)
    fft_values = np.abs(fft(signal))
    dominant_freq = freq[np.argmax(fft_values)]
    return abs(dominant_freq)

def print_tuning_status(current_freq, target_freq):
    print(f"Текущая частота: {current_freq:.2f} Hz | Целевая частота: {target_freq:.2f} Hz")

    if abs(current_freq - target_freq) < 1.0:
        print("Струна настроена!")
    else:
        if current_freq < target_freq:
            print("Подтяните струну.")
        else:
            print("Ослабьте струну.")

def select_string():
    print("Выберите струну для настройки:")
    for string, freq in TUNING_FREQUENCIES.items():
        print(f"{string}: {freq:.2f} Hz")
    selected_string = input("Введите название струны (например, E2): ").strip().upper()
    return selected_string

def tune_guitar():
    """Основная функция для настройки гитары."""
    sample_rate = 44100  # Частота дискретизации
    duration = 0.5  # Длительность записи в секундах (меньше для более быстрого обновления)

    # Выбор струны
    selected_string = select_string()
    if selected_string not in TUNING_FREQUENCIES:
        print("Ошибка: выбрана неверная струна.")
        return

    target_freq = TUNING_FREQUENCIES[selected_string]

    print(f"Настройка струны {selected_string} ({target_freq:.2f} Hz). Нажмите Ctrl+C для выхода.")

    try:
        while True:
            # Запись аудио
            recording = record_audio(duration, sample_rate)

            # Анализ частоты
            current_freq = analyze_frequency(recording[:, 0], sample_rate)

            # Вывод текущего статуса
            print_tuning_status(current_freq, target_freq)

    except KeyboardInterrupt:
        print("Настройка завершена.")

if __name__ == "__main__":
    tune_guitar()