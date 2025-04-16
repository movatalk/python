# movatalk/audio/stt.py
"""
Moduł do rozpoznawania mowy (Speech-to-Text) w movatalk.
"""

import os
import subprocess
import tempfile
import shutil
import platform


class WhisperSTT:
    """
    Klasa do transkrypcji audio na tekst za pomocą Whisper.cpp.
    """

    def __init__(self, model_path=None, language="auto"):
        """
        Inicjalizacja rozpoznawania mowy Whisper.

        Args:
            model_path (str): Ścieżka do modelu Whisper.
            language (str): Język (kod ISO 639-1, np. "pl") lub "auto" dla autodetekcji.
        """
        # Ustalenie ścieżek
        self.home_dir = os.path.expanduser("~")
        self.default_model_dir = os.path.join(self.home_dir, ".movatalk", "models", "stt")

        # Jeśli nie podano ścieżki, użyj domyślnej
        if model_path is None:
            self.model_path = os.path.join(self.default_model_dir, "models", "ggml-tiny.bin")
        else:
            self.model_path = os.path.expanduser(model_path)

        # Sprawdzenie czy model istnieje
        if not os.path.exists(self.model_path):
            print(f"Ostrzeżenie: Model {self.model_path} nie istnieje!")
            print(f"Proszę uruchomić skrypt 'install_models.sh' lub ręcznie pobrać model.")

        # Lokalizacja whisper.cpp
        if platform.system() == "Windows":
            self.whisper_bin = os.path.join(self.default_model_dir, "main.exe")
        else:
            self.whisper_bin = os.path.join(self.default_model_dir, "main")

        # Sprawdzenie czy binary istnieje
        if not os.path.exists(self.whisper_bin):
            print(f"Ostrzeżenie: Whisper {self.whisper_bin} nie istnieje!")
            print(f"Proszę uruchomić skrypt 'install_models.sh' lub ręcznie skompilować Whisper.cpp.")

        self.language = language

    def transcribe(self, audio_file):
        """
        Transkrypcja audio na tekst.

        Args:
            audio_file (str): Ścieżka do pliku audio.

        Returns:
            str: Rozpoznany tekst lub komunikat błędu.
        """
        if not os.path.exists(audio_file):
            return "Błąd: Nie znaleziono pliku audio"

        if not os.path.exists(self.whisper_bin):
            return "Błąd: Nie znaleziono binarki Whisper"

        if not os.path.exists(self.model_path):
            return "Błąd: Nie znaleziono modelu Whisper"

        # Wywołanie Whisper.cpp do transkrypcji
        try:
            cmd = [
                self.whisper_bin,
                "-m", self.model_path,
                "-f", audio_file
            ]

            # Dodaj język jeśli nie jest auto
            if self.language != "auto":
                cmd.extend(["-l", self.language])

            # Wykonaj komendę
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # Przetworzenie wyniku
            if result.returncode == 0:
                # Wyciągnij tekst z wyjścia (pomijając informacje o czasie itp.)
                lines = result.stdout.strip().split('\n')
                transcript = ""

                for line in lines:
                    # Whisper zwykle daje wyjście w formacie "[czas] tekst"
                    if "]" in line:
                        transcript += line.split("]", 1)[1].strip() + " "
                    else:
                        # Jeśli nie ma formatu czasowego, dodaj cały tekst
                        transcript += line.strip() + " "

                return transcript.strip()
            else:
                return f"Błąd transkrypcji: {result.stderr}"

        except Exception as e:
            return f"Błąd wykonania: {str(e)}"