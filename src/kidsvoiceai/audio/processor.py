# kidsvoiceai/audio/processor.py
"""
Moduł do przetwarzania audio w KidsVoiceAI.
"""

import numpy as np
import sounddevice as sd
import soundfile as sf
import os
from scipy import signal
import tempfile
from datetime import datetime


class AudioProcessor:
    """
    Klasa do nagrywania i przetwarzania dźwięku.
    """

    def __init__(self, sample_rate=16000, channels=1, record_seconds=5):
        """
        Inicjalizacja procesora audio.

        Args:
            sample_rate (int): Częstotliwość próbkowania w Hz.
            channels (int): Liczba kanałów (1 = mono, 2 = stereo).
            record_seconds (int): Domyślny czas nagrania w sekundach.
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.record_seconds = record_seconds
        self.recording = False
        self.audio_data = []

        # Utworzenie katalogu tymczasowego
        self.temp_dir = os.path.join(tempfile.gettempdir(), "kidsvoiceai")
        os.makedirs(self.temp_dir, exist_ok=True)

    def start_recording(self, duration=None):
        """
        Rozpocznij nagrywanie audio.

        Args:
            duration (int, optional): Czas nagrania w sekundach.
                                     Jeśli None, użyj domyślnego czasu.

        Returns:
            str: Ścieżka do pliku z przetworzonym dźwiękiem lub None w przypadku błędu.
        """
        if duration is None:
            duration = self.record_seconds

        self.recording = True
        print(f"Nagrywanie przez {duration} sekund...")

        try:
            self.audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                blocking=True
            )
            self.recording = False
            print("Nagrywanie zakończone.")
            return self.process_audio()

        except Exception as e:
            self.recording = False
            print(f"Błąd podczas nagrywania: {str(e)}")
            return None

    def process_audio(self):
        """
        Przetwórz nagranie (redukcja szumów, filtrowanie, normalizacja).

        Returns:
            str: Ścieżka do pliku z przetworzonym dźwiękiem lub None w przypadku błędu.
        """
        if len(self.audio_data) == 0:
            return None

        try:
            # Konwersja do mono jeśli stereo
            if self.channels == 2:
                audio_mono = np.mean(self.audio_data, axis=1)
            else:
                audio_mono = self.audio_data.flatten()

            # Normalizacja
            audio_norm = audio_mono / (np.max(np.abs(audio_mono)) + 1e-10)

            # Filtr górnoprzepustowy (usuwanie niskich częstotliwości)
            b, a = signal.butter(5, 100 / (self.sample_rate / 2), 'highpass')
            audio_filtered = signal.filtfilt(b, a, audio_norm)

            # Usuwanie szumu (prosta metoda - odcięcie cichych fragmentów)
            noise_gate = 0.01  # Próg względny
            audio_denoised = np.where(np.abs(audio_filtered) < noise_gate, 0, audio_filtered)

            # Zapisanie do pliku tymczasowego
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = os.path.join(self.temp_dir, f"processed_audio_{timestamp}.wav")
            sf.write(temp_file, audio_denoised, self.sample_rate)

            print(f"Dźwięk przetworzony i zapisany: {temp_file}")
            return temp_file

        except Exception as e:
            print(f"Błąd podczas przetwarzania dźwięku: {str(e)}")
            return None

    def play_audio(self, audio_file):
        """
        Odtwórz plik audio.

        Args:
            audio_file (str): Ścieżka do pliku audio.

        Returns:
            bool: True jeśli odtwarzanie zakończyło się sukcesem, False w przeciwnym razie.
        """
        try:
            data, fs = sf.read(audio_file)
            sd.play(data, fs)
            sd.wait()  # Czekaj na zakończenie odtwarzania
            return True
        except Exception as e:
            print(f"Błąd podczas odtwarzania dźwięku: {str(e)}")
            return False

    def cleanup(self):
        """
        Wyczyść pliki tymczasowe.
        """
        try:
            for file in os.listdir(self.temp_dir):
                if file.startswith("processed_audio_"):
                    os.remove(os.path.join(self.temp_dir, file))
            print("Pliki tymczasowe wyczyszczone.")
        except Exception as e:
            print(f"Błąd podczas czyszczenia plików tymczasowych: {str(e)}")