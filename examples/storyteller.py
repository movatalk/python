#!/usr/bin/env python3
"""
Opowiadacz historii używający biblioteki movatalk.
Ten przykład pokazuje jak stworzyć interaktywnego opowiadacza historii,
który generuje i opowiada historie na podstawie podanych przez dziecko tematów.

Uruchomienie:
python storyteller.py
"""

import os
import signal
import sys
import time
import json
import random

from movatalk.audio import AudioProcessor, WhisperSTT, PiperTTS
from movatalk.api import SafeAPIConnector, CacheManager
from movatalk.safety import ParentalControl, ContentFilter
from movatalk.utils import Logger, ConfigManager

# Inicjalizacja loggera
logger = Logger(level=20, log_to_console=True)  # 20 = INFO


# Funkcja obsługi wyjścia
def handle_exit(sig, frame):
    logger.info("Zatrzymywanie opowiadacza historii...")
    sys.exit(0)


# Rejestracja obsługi sygnałów
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Szablon historii dla dzieci (krótsze i prostsze opowieści)
STORY_TEMPLATE = """
Stwórz krótką historię dla dzieci (maksymalnie 4-5 zdań) na następujący temat:
{topic}

Historia powinna być:
1. Pozytywna i pouczająca
2. Odpowiednia dla dzieci w wieku 5-8 lat
3. Prosta w zrozumieniu
4. Z jasnym początkiem i zakończeniem
5. Zawierać elementy z podanego tematu

Zacznij historię od zwrotu "Dawno, dawno temu..." lub podobnego.
"""

# Szablony pytań do interakcji
QUESTIONS = [
    "O czym chcesz usłyszeć dzisiaj historię?",
    "Jaki temat Cię interesuje? Opowiem Ci historię.",
    "Podaj bohaterów lub miejsce, a opowiem Ci ciekawą historię.",
    "O kim chciałbyś posłuchać dzisiaj?"
]


class StoryTeller:
    """Klasa implementująca interaktywnego opowiadacza historii."""

    def __init__(self):
        """Inicjalizacja opowiadacza historii."""
        logger.info("Inicjalizacja opowiadacza historii...")

        # Inicjalizacja komponentów
        self.audio = AudioProcessor()
        self.stt = WhisperSTT()
        self.tts = PiperTTS()
        self.api = SafeAPIConnector()
        self.parental = ParentalControl()
        self.content_filter = ContentFilter()
        self.cache = CacheManager()
        self.config = ConfigManager()

        # Katalog na zapisane historie
        self.stories_dir = os.path.expanduser("~/.movatalk/stories")
        os.makedirs(self.stories_dir, exist_ok=True)

        # Lista wcześniej opowiedzianych historii
        self.told_stories = []
        self.load_told_stories()

    def load_told_stories(self):
        """Wczytuje listę opowiedzianych historii z pliku."""
        stories_file = os.path.join(self.stories_dir, "told_stories.json")

        try:
            if os.path.exists(stories_file):
                with open(stories_file, 'r') as f:
                    self.told_stories = json.load(f)
        except Exception as e:
            logger.error(f"Błąd wczytywania historii: {str(e)}")
            self.told_stories = []

    def save_told_stories(self):
        """Zapisuje listę opowiedzianych historii do pliku."""
        stories_file = os.path.join(self.stories_dir, "told_stories.json")

        try:
            with open(stories_file, 'w') as f:
                json.dump(self.told_stories, f, indent=2)
        except Exception as e:
            logger.error(f"Błąd zapisywania historii: {str(e)}")

    def save_story(self, topic, story):
        """
        Zapisuje historię do pliku.

        Args:
            topic (str): Temat historii.
            story (str): Treść historii.
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.stories_dir, f"story_{timestamp}.txt")

        try:
            with open(filename, 'w') as f:
                f.write(f"Temat: {topic}\n\n")
                f.write(story)
            logger.info(f"Historia zapisana do pliku: {filename}")
        except Exception as e:
            logger.error(f"Błąd zapisywania historii do pliku: {str(e)}")

    def start(self):
        """Rozpocznij opowiadacza historii."""

        logger.info("Uruchamianie opowiadacza historii...")

        # Powitanie
        welcome_message = "Cześć! Jestem opowiadaczem historii. Mogę opowiedzieć Ci ciekawą historię na dowolny temat."
        logger.info(welcome_message)
        self.tts.speak(welcome_message)

        # Główna pętla
        while True:
            # Sprawdzenie ograniczeń rodzicielskich
            if not self.parental.check_time_restrictions():
                logger.warning("Poza dozwolonymi godzinami użytkowania.")
                self.tts.speak("Przepraszam, ale teraz jest czas odpoczynku. Porozmawiajmy później.")
                time.sleep(60)  # Czekaj minutę przed ponownym sprawdzeniem
                continue

            if not self.parental.check_usage_limit():
                logger.warning("Przekroczono dzienny limit czasu użytkowania.")
                self.tts.speak("Osiągnąłeś dzienny limit korzystania z urządzenia. Do zobaczenia jutro!")
                time.sleep(60)  # Czekaj minutę przed ponownym sprawdzeniem
                continue

            # Zapytaj o temat
            question = random.choice(QUESTIONS)
            logger.info(f"Pytanie: {question}")
            self.tts.speak(question)

            # Nagrywanie odpowiedzi
            logger.info("Czekam na odpowiedź...")
            audio_file = self.audio.start_recording(duration=7)  # Dłuższy czas na odpowiedź

            # Rozpoznanie odpowiedzi
            transcript = self.stt.transcribe(audio_file)
            if "Błąd" in transcript:
                logger.error(f"Błąd STT: {transcript}")
                self.tts.speak("Przepraszam, nie zrozumiałem. Spróbujmy jeszcze raz.")
                continue

            logger.info(f"Temat od użytkownika: '{transcript}'")

            # Filtrowanie treści
            filtered_input, filter_message = self.parental.filter_input(transcript)
            if not filtered_input:
                logger.warning(f"Treść odfiltrowana: {filter_message}")
                self.tts.speak(filter_message)
                continue

            # Sprawdź czy to żądanie zakończenia
            if any(word in transcript.lower() for word in ["koniec", "zakończ", "wyjdź", "pa", "do widzenia"]):
                self.tts.speak("Do widzenia! Mam nadzieję, że spodobały Ci się moje historie.")
                logger.info("Zakończenie na żądanie użytkownika.")
                break

            # Aktualizacja statystyk użycia
            self.parental.update_usage(minutes=2)  # Historie są dłuższe, więc więcej czasu

            # Generowanie historii
            logger.info("Generowanie historii...")
            self.tts.speak("Dobrze, wymyślam historię. Daj mi chwilkę.")

            try:
                # Sprawdź czy historia dla tego tematu jest w pamięci podręcznej
                cache_key = f"story_{filtered_input.lower()}"
                story = self.cache.get(cache_key)

                if not story:
                    # Generowanie nowej historii
                    prompt = STORY_TEMPLATE.format(topic=filtered_input)
                    story = self.api.query_llm(prompt)

                    # Filtrowanie treści historii
                    story = self.content_filter.sanitize_content(story, age_group="5-8")

                    # Zapisz do pamięci podręcznej
                    self.cache.set(cache_key, story)

                logger.info(f"Wygenerowana historia: '{story}'")

                # Dodaj do opowiedzianych
                self.told_stories.append({
                    "timestamp": time.time(),
                    "topic": filtered_input,
                    "story": story
                })
                self.save_told_stories()

                # Zapisz historię
                self.save_story(filtered_input, story)

                # Opowiedz historię
                logger.info("Opowiadanie historii...")
                self.tts.speak(story)

                # Zapytaj czy podobała się historia
                time.sleep(1)
                self.tts.speak("Czy podobała Ci się ta historia?")

                # Nagrywanie odpowiedzi
                audio_file = self.audio.start_recording(duration=3)
                feedback = self.stt.transcribe(audio_file)

                if "tak" in feedback.lower() or "podoba" in feedback.lower():
                    self.tts.speak("Cieszę się! Chcesz usłyszeć kolejną historię?")
                else:
                    self.tts.speak("Następnym razem postaram się lepiej. Chcesz usłyszeć inną historię?")

                # Nagrywanie odpowiedzi
                audio_file = self.audio.start_recording(duration=3)
                continue_response = self.stt.transcribe(audio_file)

                if "nie" in continue_response.lower() or "koniec" in continue_response.lower():
                    self.tts.speak("Dobrze, dziękuję za wspólny czas. Do widzenia!")
                    break

                # Jeśli chce kontynuować, przechodzimy do następnej iteracji pętli

            except Exception as e:
                logger.error(f"Błąd generowania historii: {str(e)}")
                self.tts.speak("Przepraszam, miałem problem z wymyśleniem historii. Spróbujmy jeszcze raz.")
                continue

            # Przerwa między historiami
            time.sleep(2)


def main():
    """Główna funkcja programu."""
    storyteller = StoryTeller()
    storyteller.start()


if __name__ == "__main__":
    main()