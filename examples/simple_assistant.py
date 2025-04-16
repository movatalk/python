#!/usr/bin/env python3
"""
Prosty asystent głosowy używający biblioteki movatalk.
Ten przykład pokazuje podstawową interakcję z użyciem lokalnego
przetwarzania STT/TTS i opcjonalnego API.

Uruchomienie:
python simple_assistant.py
"""

import time
import signal
import sys

from movatalk.audio import AudioProcessor, WhisperSTT, PiperTTS
from movatalk.api import SafeAPIConnector
from movatalk.safety import ParentalControl
from movatalk.utils import Logger

# Inicjalizacja loggera
logger = Logger(level=20, log_to_console=True)  # 20 = INFO


# Funkcja obsługi wyjścia
def handle_exit(sig, frame):
    logger.info("Zatrzymywanie asystenta...")
    sys.exit(0)


# Rejestracja obsługi sygnałów
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


def main():
    """Główna funkcja asystenta."""

    logger.info("Inicjalizacja komponentów...")

    # Inicjalizacja komponentów
    audio = AudioProcessor()
    stt = WhisperSTT()
    tts = PiperTTS()
    api = SafeAPIConnector()
    parental = ParentalControl()

    logger.info("Asystent gotowy! Naciśnij Ctrl+C, aby zakończyć.")
    tts.speak("Witaj! Jestem gotowy do rozmowy. Jak mogę Ci pomóc?")

    try:
        while True:
            # Sprawdzenie ograniczeń rodzicielskich
            if not parental.check_time_restrictions():
                logger.warning("Poza dozwolonymi godzinami użytkowania.")
                tts.speak("Przepraszam, ale teraz jest czas odpoczynku. Porozmawiajmy później.")
                time.sleep(60)  # Czekaj minutę przed ponownym sprawdzeniem
                continue

            if not parental.check_usage_limit():
                logger.warning("Przekroczono dzienny limit czasu użytkowania.")
                tts.speak("Osiągnąłeś dzienny limit korzystania z urządzenia. Do zobaczenia jutro!")
                time.sleep(60)  # Czekaj minutę przed ponownym sprawdzeniem
                continue

            # Komunikat o słuchaniu
            logger.info("Słucham...")
            tts.speak("Słucham Cię.")

            # Nagrywanie i rozpoznawanie mowy
            audio_file = audio.start_recording(duration=5)
            logger.info("Przetwarzanie nagrania...")

            transcript = stt.transcribe(audio_file)
            if "Błąd" in transcript:
                logger.error(f"Błąd STT: {transcript}")
                tts.speak("Przepraszam, nie zrozumiałem. Czy możesz powtórzyć?")
                continue

            logger.info(f"Rozpoznano: '{transcript}'")

            # Filtrowanie treści
            filtered_input, filter_message = parental.filter_input(transcript)
            if not filtered_input:
                logger.warning(f"Treść odfiltrowana: {filter_message}")
                tts.speak(filter_message)
                continue

            # Aktualizacja statystyk użycia
            parental.update_usage(minutes=1)

            # Sprawdź czy to żądanie zakończenia
            if any(word in transcript.lower() for word in ["koniec", "zakończ", "wyjdź", "pa", "do widzenia"]):
                tts.speak("Do widzenia! Miło było z Tobą rozmawiać.")
                logger.info("Zakończenie na żądanie użytkownika.")
                break

            # Zapytanie do API
            logger.info("Wysyłanie zapytania do API...")

            try:
                response = api.query_llm(filtered_input)
                filtered_response = parental.filter_output(response)
                logger.info(f"Odpowiedź: '{filtered_response}'")

                # Synteza mowy
                tts.speak(filtered_response)

            except Exception as e:
                logger.error(f"Błąd API: {str(e)}")
                tts.speak("Przepraszam, wystąpił problem z uzyskaniem odpowiedzi. Spróbujmy ponownie.")

            # Przerwa między interakcjami
            time.sleep(1)

    except Exception as e:
        logger.critical(f"Krytyczny błąd: {str(e)}")
        tts.speak("Wystąpił błąd. Zamykam aplikację.")
    finally:
        # Czyszczenie
        logger.info("Czyszczenie zasobów...")
        audio.cleanup()
        tts.cleanup()


if __name__ == "__main__":
    main()