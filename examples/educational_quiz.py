#!/usr/bin/env python3
"""
Quiz edukacyjny używający biblioteki movatalk.
Ten przykład pokazuje jak stworzyć interaktywny quiz edukacyjny
dla dzieci, który wykorzystuje lokalne przetwarzanie STT/TTS i API.

Uruchomienie:
python educational_quiz.py [kategoria]

Dostępne kategorie: matematyka, przyroda, historia, języki
"""

import argparse
import random
import signal
import sys
import time

from movatalk.audio import AudioProcessor, WhisperSTT, PiperTTS
from movatalk.api import SafeAPIConnector, CacheManager
from movatalk.safety import ParentalControl
from movatalk.utils import Logger

# Kategorie quizu i przykładowe pytania
QUIZ_CATEGORIES = {
    "matematyka": [
        {"pytanie": "Ile to jest 5 plus 3?", "odpowiedź": "8"},
        {"pytanie": "Ile boków ma trójkąt?", "odpowiedź": "3"},
        {"pytanie": "Co jest większe: 15 czy 51?", "odpowiedź": "51"},
        {"pytanie": "Ile to jest 4 razy 2?", "odpowiedź": "8"},
        {"pytanie": "Ile to jest 10 minus 4?", "odpowiedź": "6"}
    ],
    "przyroda": [
        {"pytanie": "Jakiego koloru jest trawa?", "odpowiedź": "zielona"},
        {"pytanie": "Jaki owoc jest czerwony i rośnie na drzewie?", "odpowiedź": "jabłko"},
        {"pytanie": "Ile nóg ma pająk?", "odpowiedź": "8"},
        {"pytanie": "Jak nazywa się miejsce, gdzie mieszkają zwierzęta w zoo?", "odpowiedź": "wybieg"},
        {"pytanie": "Jaki ptak nie lata, ale świetnie pływa?", "odpowiedź": "pingwin"}
    ],
    "historia": [
        {"pytanie": "Kto był pierwszym królem Polski?", "odpowiedź": "Bolesław Chrobry"},
        {"pytanie": "Co to jest zamek?", "odpowiedź": "budowla"},
        {"pytanie": "Jak nazywa się nasza planeta?", "odpowiedź": "Ziemia"},
        {"pytanie": "Jak nazywa się stolica Polski?", "odpowiedź": "Warszawa"},
        {"pytanie": "Kto maluje obrazy?", "odpowiedź": "malarz"}
    ],
    "języki": [
        {"pytanie": "Jak po angielsku jest 'pies'?", "odpowiedź": "dog"},
        {"pytanie": "Jak po angielsku jest 'kot'?", "odpowiedź": "cat"},
        {"pytanie": "Jak po angielsku jest 'dom'?", "odpowiedź": "house"},
        {"pytanie": "Jak po angielsku jest 'szkoła'?", "odpowiedź": "school"},
        {"pytanie": "Jak po angielsku jest 'jabłko'?", "odpowiedź": "apple"}
    ]
}

# Inicjalizacja loggera
logger = Logger(level=20, log_to_console=True)  # 20 = INFO


# Funkcja obsługi wyjścia
def handle_exit(sig, frame):
    logger.info("Zatrzymywanie quizu...")
    sys.exit(0)


# Rejestracja obsługi sygnałów
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


class EducationalQuiz:
    """Klasa implementująca quiz edukacyjny."""

    def __init__(self, category="matematyka"):
        """
        Inicjalizacja quizu.

        Args:
            category (str): Kategoria quizu (matematyka, przyroda, historia, języki).
        """
        self.category = category.lower()

        if self.category not in QUIZ_CATEGORIES:
            logger.warning(f"Nieznana kategoria: {category}. Używam domyślnej: matematyka")
            self.category = "matematyka"

        logger.info(f"Inicjalizacja quizu - kategoria: {self.category}")

        # Pytania i odpowiedzi
        self.questions = QUIZ_CATEGORIES[self.category]
        random.shuffle(self.questions)  # Losowa kolejność pytań

        # Liczniki
        self.score = 0
        self.question_index = 0

        # Inicjalizacja komponentów
        self.audio = AudioProcessor()
        self.stt = WhisperSTT()
        self.tts = PiperTTS()
        self.api = SafeAPIConnector()
        self.parental = ParentalControl()
        self.cache = CacheManager()

        # Flaga działania
        self.running = True

    def start(self):
        """Rozpocznij quiz."""

        logger.info("Rozpoczynanie quizu...")

        # Powitanie
        welcome_message = f"Witaj w quizie z kategorii {self.category}! Zadam Ci 5 pytań. Gotowy?"
        logger.info(welcome_message)
        self.tts.speak(welcome_message)
        time.sleep(1)

        # Główna pętla quizu
        while self.running and self.question_index < len(self.questions):
            if not self.ask_question():
                logger.warning("Przerwanie quizu.")
                break

            # Przerwa między pytaniami
            time.sleep(2)

        # Podsumowanie
        if self.question_index >= len(self.questions):
            summary = f"Koniec quizu! Zdobyłeś {self.score} punktów na {len(self.questions)} możliwych. Dobra robota!"
            logger.info(summary)
            self.tts.speak(summary)

    def ask_question(self):
        """
        Zadaj jedno pytanie i przetwórz odpowiedź.

        Returns:
            bool: True jeśli można kontynuować, False jeśli należy przerwać quiz.
        """
        # Pobierz aktualne pytanie
        question_data = self.questions[self.question_index]
        question_text = question_data["pytanie"]
        correct_answer = question_data["odpowiedź"].lower()

        # Zadaj pytanie
        logger.info(f"Pytanie {self.question_index + 1}: {question_text}")
        self.tts.speak(f"Pytanie numer {self.question_index + 1}. {question_text}")

        # Nagrywanie odpowiedzi
        logger.info("Czekam na odpowiedź...")
        audio_file = self.audio.start_recording(duration=5)

        # Rozpoznanie odpowiedzi
        transcript = self.stt.transcribe(audio_file)
        if "Błąd" in transcript:
            logger.error(f"Błąd STT: {transcript}")
            self.tts.speak("Przepraszam, nie zrozumiałem. Spróbujmy jeszcze raz.")
            return True

        logger.info(f"Odpowiedź użytkownika: '{transcript}'")

        # Filtrowanie treści
        filtered_input, filter_message = self.parental.filter_input(transcript)
        if not filtered_input:
            logger.warning(f"Treść odfiltrowana: {filter_message}")
            self.tts.speak(filter_message)
            return True

        # Sprawdzenie czy odpowiedź jest poprawna
        user_answer = filtered_input.lower()

        # Elastyczne sprawdzanie odpowiedzi (za pomocą API)
        is_correct = self.verify_answer(user_answer, correct_answer, question_text)

        # Zwiększenie indeksu pytania
        self.question_index += 1

        if is_correct:
            self.score += 1
            response = f"Brawo! Twoja odpowiedź jest poprawna. Masz już {self.score} punktów."
            logger.info(f"Odpowiedź poprawna: {user_answer} = {correct_answer}")
        else:
            response = f"Niestety, to nie jest poprawna odpowiedź. Prawidłowa odpowiedź to: {correct_answer}."
            logger.info(f"Odpowiedź niepoprawna: {user_answer} != {correct_answer}")

        # Powiedz wynik
        self.tts.speak(response)

        return True

    def verify_answer(self, user_answer, correct_answer, question):
        """
        Sprawdza, czy odpowiedź użytkownika jest poprawna.
        Używa prostego porównania lub elastycznego sprawdzenia przez API.

        Args:
            user_answer (str): Odpowiedź użytkownika.
            correct_answer (str): Poprawna odpowiedź.
            question (str): Pytanie.

        Returns:
            bool: True jeśli odpowiedź jest poprawna, False w przeciwnym razie.
        """
        # Prosta weryfikacja - dokładne dopasowanie lub zawieranie
        if user_answer == correct_answer or correct_answer in user_answer:
            return True

        # Elastyczna weryfikacja - sprawdzamy przez API czy odpowiedź jest semantycznie poprawna
        try:
            # Stwórzmy klucz pamięci podręcznej
            cache_key = f"quiz_verify_{user_answer}_{correct_answer}"
            cached_result = self.cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            # Pytanie do API
            prompt = (
                f"PYTANIE: {question}\n"
                f"POPRAWNA ODPOWIEDŹ: {correct_answer}\n"
                f"ODPOWIEDŹ DZIECKA: {user_answer}\n"
                f"Czy odpowiedź dziecka jest poprawna? Odpowiedz tylko TAK lub NIE."
            )

            response = self.api.query_llm(prompt)

            # Interpretacja odpowiedzi
            is_correct = "TAK" in response.upper() and "NIE" not in response.upper()

            # Zapisz wynik w pamięci podręcznej
            self.cache.set(cache_key, is_correct)

            return is_correct

        except Exception as e:
            logger.error(f"Błąd weryfikacji przez API: {str(e)}")
            # W przypadku błędu, wracamy do prostego porównania
            return user_answer == correct_answer


def main():
    """Główna funkcja programu."""

    # Parsowanie argumentów
    parser = argparse.ArgumentParser(description="Quiz edukacyjny dla dzieci")
    parser.add_argument("category", nargs="?", default="matematyka",
                        help="Kategoria quizu (matematyka, przyroda, historia, języki)")
    args = parser.parse_args()

    # Inicjalizacja i uruchomienie quizu
    quiz = EducationalQuiz(category=args.category)
    quiz.start()


if __name__ == "__main__":
    main()