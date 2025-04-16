# kidsvoiceai/audio/tts.py
"""
Moduł do syntezy mowy (Text-to-Speech) w KidsVoiceAI.
"""

import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
from datetime import datetime
import importlib.util
import sys


class PiperTTS:
    """
    Klasa do syntezy mowy za pomocą Piper TTS.
    """

    def __init__(self, voice_path=None):
        """
        Inicjalizacja syntezy mowy Piper.

        Args:
            voice_path (str): Ścieżka do modelu głosu Piper.
        """
        self.home_dir = os.path.expanduser("~")

        # Domyślna ścieżka do modelu głosu
        if voice_path is None:
            self.voice_path = os.path.join(
                self.home_dir,
                ".local/share/piper/voices/pl/krzysztof/low/pl_krzysztof_low.onnx"
            )
        else:
            self.voice_path = os.path.expanduser(voice_path)

        # Ścieżka do konfiguracji modelu
        self.config_path = os.path.join(os.path.dirname(self.voice_path), "config.json")

        # Sprawdzenie czy model istnieje
        if not os.path.exists(self.voice_path):
            print(f"Ostrzeżenie: Model głosu {self.voice_path} nie istnieje!")
            print(f"Proszę uruchomić skrypt 'install_models.sh' lub ręcznie pobrać model głosu.")

        # Sprawdzenie czy piper jest zainstalowany
        if importlib.util.find_spec("piper") is None:
            print("Ostrzeżenie: Biblioteka Piper nie jest zainstalowana!")
            print("Proszę zainstalować Piper: pip install piper-tts")
            return

        # Inicjalizacja Piper (lazy loading)
        self.voice = None
        self.sample_rate = 22050  # Standardowa częstotliwość dla Piper

        # Katalog tymczasowy na pliki audio
        self.temp_dir = os.path.join(tempfile.gettempdir(), "kidsvoiceai", "tts")
        os.makedirs(self.temp_dir, exist_ok=True)

    def _load_voice(self):
        """
        Załaduj model głosu (lazy loading).

        Returns:
            bool: True jeśli załadowano pomyślnie, False w przeciwnym razie.
        """
        if self.voice is not None:
            return True

        try:
            from piper import PiperVoice

            if not os.path.exists(self.voice_path) or not os.path.exists(self.config_path):
                print(f"Błąd: Nie znaleziono modelu głosu lub konfiguracji.")
                return False

            self.voice = PiperVoice.load(self.voice_path, self.config_path)
            return True

        except Exception as e:
            print(f"Błąd podczas ładowania modelu głosu: {str(e)}")
            return False

    def speak(self, text):
        """
        Syntezuj mowę i odtwórz ją.

        Args:
            text (str): Tekst do syntezy.

        Returns:
            bool: True jeśli synteza i odtwarzanie zakończyły się sukcesem,
                  False w przeciwnym razie.
        """
        if not self._load_voice():
            print("Nie można załadować modelu głosu.")
            return False

        try:
            # Synteza mowy
            print(f"Syntezowanie: '{text}'")
            audio_data = self.voice.synthesize(text)

            # Normalizacja
            audio_norm = audio_data / (np.max(np.abs(audio_data)) + 1e-10)

            # Zapisanie do pliku tymczasowego (opcjonalne)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = os.path.join(self.temp_dir, f"synthesized_{timestamp}.wav")
            sf.write(temp_file, audio_norm, self.sample_rate)

            # Odtworzenie audio
            sd.play(audio_norm, self.sample_rate)
            sd.wait()  # Czekaj na zakończenie odtwarzania

            return True

        except Exception as e:
            print(f"Błąd syntezy mowy: {str(e)}")
            return False

    def save_to_file(self, text, output_file):
        """
        Syntezuj mowę i zapisz do pliku.

        Args:
            text (str): Tekst do syntezy.
            output_file (str): Ścieżka do pliku wyjściowego.

        Returns:
            bool: True jeśli synteza zakończyła się sukcesem, False w przeciwnym razie.
        """
        if not self._load_voice():
            return False

        try:
            # Synteza mowy
            audio_data = self.voice.synthesize(text)

            # Normalizacja
            audio_norm = audio_data / (np.max(np.abs(audio_data)) + 1e-10)

            # Zapisanie do pliku
            sf.write(output_file, audio_norm, self.sample_rate)
            print(f"Synteza zapisana do pliku: {output_file}")

            return True

        except Exception as e:
            print(f"Błąd syntezy mowy: {str(e)}")
            return False

    def cleanup(self):
        """
        Wyczyść pliki tymczasowe.
        """
        try:
            for file in os.listdir(self.temp_dir):
                if file.startswith("synthesized_"):
                    os.remove(os.path.join(self.temp_dir, file))
            print("Pliki tymczasowe TTS wyczyszczone.")
        except Exception as e:
            print(f"Błąd podczas czyszczenia plików tymczasowych TTS: {str(e)}")
