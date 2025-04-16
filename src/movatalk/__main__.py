# Punkt wejścia dla modułu
"""
__main__.py
"""

"""
Moduł uruchamiający dla movatalk.
Pozwala na uruchomienie movatalk jako aplikacji z linii poleceń.
"""

import argparse
import os
import sys
import time
import json
import signal

from movatalk.audio import AudioProcessor, WhisperSTT, PiperTTS
from movatalk.api import SafeAPIConnector
from movatalk.hardware import HardwareInterface, PowerManager
from movatalk.safety import ParentalControl
from movatalk.utils import ConfigManager


class VoiceAIAssistant:
    """Główna klasa asystenta głosowego dla movatalk."""

    def __init__(self, config_path=None):
        """Inicjalizacja asystenta głosowego."""
        print("Inicjalizacja movatalk...")

        # Wczytanie konfiguracji
        self.config_manager = ConfigManager(config_path)
        self.system_config = self.config_manager.get_system_config()

        # Inicjalizacja komponentów
        self.audio = AudioProcessor(**self.system_config["audio"])
        self.stt = WhisperSTT(**self.system_config["stt"])
        self.tts = PiperTTS(**self.system_config["tts"])
        self.api = SafeAPIConnector()
        self.parental = ParentalControl()

        # Opcjonalna inicjalizacja komponentów sprzętowych
        if self.system_config.get("use_hardware_interface", True):
            self.hardware = HardwareInterface(**self.system_config["hardware"])
            self.hardware.set_record_callback(self.process_interaction)
            self.hardware.start_monitoring()
        else:
            self.hardware = None

        if self.system_config.get("use_power_manager", True):
            self.power = PowerManager()
            self.power.start_monitoring()
        else:
            self.power = None

        # Stan aplikacji
        self.running = True
        self.conversation_context = []

        # Rejestracja obsługi sygnałów
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        print("System gotowy!")
        self.tts.speak("Witaj! Jestem gotowy do rozmowy.")

    def signal_handler(self, sig, frame):
        """Obsługa sygnałów wyjścia."""
        print("Otrzymano sygnał zatrzymania. Zamykanie aplikacji...")
        self.running = False
        self.tts.speak("Do widzenia!")
        if self.hardware:
            self.hardware.cleanup()
        sys.exit(0)

    def process_interaction(self):
        """Przetwórz pojedynczą interakcję głosową."""
        # Sprawdź ograniczenia rodzicielskie
        if not self.parental.check_time_restrictions():
            self.tts.speak("Przepraszam, ale teraz jest czas odpoczynku. Porozmawiajmy później.")
            return False

        if not self.parental.check_usage_limit():
            self.tts.speak("Osiągnąłeś dzienny limit korzystania z urządzenia. Do zobaczenia jutro!")
            return False

        try:
            # Powiadom o gotowości do słuchania
            if self.hardware:
                self.hardware.set_recording_led(True)
            self.tts.speak("Słucham cię.")

            # Nagrywanie i przetwarzanie dźwięku
            audio_file = self.audio.start_recording()
            if self.hardware:
                self.hardware.set_recording_led(False)
                self.hardware.set_thinking_led(True)

            if not audio_file:
                print("Błąd nagrywania dźwięku")
                return False

            # Transkrypcja
            print("Transkrypcja mowy...")
            transcript = self.stt.transcribe(audio_file)
            if "Błąd" in transcript:
                print(transcript)
                self.tts.speak("Przepraszam, nie zrozumiałem. Czy możesz powtórzyć?")
                if self.hardware:
                    self.hardware.set_thinking_led(False)
                return False

            print(f"Rozpoznany tekst: {transcript}")

            # Filtrowanie treści wejściowej
            filtered_input, filter_message = self.parental.filter_input(transcript)
            if not filtered_input:
                print(f"Treść odfiltrowana: {filter_message}")
                self.tts.speak(filter_message)
                if self.hardware:
                    self.hardware.set_thinking_led(False)
                return False

            # Sprawdzenie stanu energii
            if self.power and self.power.get_status()['critical_power']:
                self.tts.speak("Niski poziom baterii. Proszę o podłączenie ładowarki.")
                if self.hardware:
                    self.hardware.set_thinking_led(False)
                return False

            # Aktualizacja statystyk użycia
            self.parental.update_usage(minutes=1)

            # Zapisanie kontekstu rozmowy (ostatnie 10 interakcji)
            self.conversation_context.append({"role": "user", "content": filtered_input})
            if len(self.conversation_context) > 10:
                self.conversation_context = self.conversation_context[-10:]

            # Zapytanie do API
            context_text = " ".join([item["content"] for item in self.conversation_context])
            response = self.api.query_llm(filtered_input, context=context_text)

            # Filtrowanie odpowiedzi
            filtered_response = self.parental.filter_output(response)
            print(f"Odpowiedź: {filtered_response}")

            # Zapisanie odpowiedzi do kontekstu
            self.conversation_context.append({"role": "assistant", "content": filtered_response})

            # Wyłączenie diody myślenia
            if self.hardware:
                self.hardware.set_thinking_led(False)

            # Synteza mowy
            self.tts.speak(filtered_response)
            return True

        except Exception as e:
            print(f"Błąd podczas interakcji: {str(e)}")
            if self.hardware:
                self.hardware.set_thinking_led(False)
            self.tts.speak("Przepraszam, wystąpił błąd. Spróbujmy jeszcze raz.")
            return False

    def run(self):
        """Uruchom główną pętlę asystenta."""
        print("Uruchomienie movatalk")

        if not self.hardware:
            print("Tryb konsolowy: Naciśnij Enter, aby rozpocząć interakcję lub 'q', aby wyjść.")

        while self.running:
            if not self.hardware:
                # Tryb konsolowy (bez interfejsu sprzętowego)
                try:
                    user_input = input("> ")
                    if user_input.lower() == 'q':
                        self.running = False
                        break
                    self.process_interaction()
                except EOFError:
                    break
            else:
                # Tryb sprzętowy - interakcje są obsługiwane przez callbacki przycisków
                time.sleep(1)

                # Sprawdzenie stanu baterii (co 5 minut)
                if self.power and int(time.time()) % 300 == 0:
                    power_status = self.power.get_status()
                    if power_status['battery_level'] < 15 and not power_status['is_charging']:
                        self.hardware.blink_led(self.hardware.LED_POWER, duration=3, interval=0.1)

        print("movatalk zakończył pracę.")


def main():
    """Funkcja główna uruchamiana z linii poleceń."""
    parser = argparse.ArgumentParser(description="movatalk - Bezpieczny interfejs głosowy AI dla dzieci")
    parser.add_argument("--config", help="Ścieżka do pliku konfiguracyjnego")
    parser.add_argument("--console", action="store_true",
                        help="Uruchom w trybie konsolowym (bez interfejsu sprzętowego)")
    args = parser.parse_args()

    # Nadpisanie konfiguracji jeśli wybrany tryb