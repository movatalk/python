# movatalk/pipeline/components.py
"""
Definicje komponentów do wykorzystania w pipelinach dla movatalk.
"""

from abc import ABC, abstractmethod
import os
import json
import importlib
import inspect
import pkgutil
import sys

from movatalk.audio import AudioProcessor, WhisperSTT, PiperTTS
from movatalk.api import SafeAPIConnector, LocalLLMConnector, CacheManager
from movatalk.safety import ParentalControl, ContentFilter
from movatalk.utils import Logger


class Component(ABC):
    """
    Bazowa klasa abstrakcyjna dla wszystkich komponentów pipeline'a.
    """

    def __init__(self, name, description=None):
        """
        Inicjalizacja komponentu.

        Args:
            name (str): Nazwa komponentu.
            description (str, optional): Opis komponentu.
        """
        self.name = name
        self.description = description or "Brak opisu"

    @abstractmethod
    def execute(self, params, context):
        """
        Wykonaj zadanie komponentu.

        Args:
            params (dict): Parametry dla komponentu.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        pass

    def validate_params(self, params, required_params=None):
        """
        Sprawdź, czy wszystkie wymagane parametry są obecne.

        Args:
            params (dict): Parametry przekazane do komponentu.
            required_params (list): Lista wymaganych parametrów.

        Returns:
            bool: True jeśli wszystkie wymagane parametry są obecne.

        Raises:
            ValueError: Jeśli brakuje wymaganych parametrów.
        """
        if required_params is None:
            return True

        missing_params = [p for p in required_params if p not in params]
        if missing_params:
            raise ValueError(f"Brakujące parametry dla komponentu {self.name}: {', '.join(missing_params)}")

        return True

    def get_param(self, params, name, default=None):
        """
        Pobierz parametr z podanej nazwy, z opcjonalną wartością domyślną.

        Args:
            params (dict): Parametry przekazane do komponentu.
            name (str): Nazwa parametru.
            default (Any, optional): Domyślna wartość, jeśli parametr nie istnieje.

        Returns:
            Any: Wartość parametru lub wartość domyślna.
        """
        return params.get(name, default)


class ComponentRegistry:
    """
    Rejestr wszystkich dostępnych komponentów.
    """

    def __init__(self):
        """
        Inicjalizacja rejestru komponentów.
        """
        self.components = {}
        self.load_components()

    def register(self, component):
        """
        Zarejestruj nowy komponent.

        Args:
            component (Component): Komponent do zarejestrowania.

        Returns:
            bool: True, jeśli rejestracja się powiodła.
        """
        if not isinstance(component, Component):
            raise TypeError("Komponent musi dziedziczyć po klasie Component")

        self.components[component.name] = component
        return True

    def get_component(self, name):
        """
        Pobierz komponent o podanej nazwie.

        Args:
            name (str): Nazwa komponentu.

        Returns:
            Component or None: Komponent o podanej nazwie lub None, jeśli nie znaleziono.
        """
        return self.components.get(name)

    def get_all_components(self):
        """
        Pobierz wszystkie zarejestrowane komponenty.

        Returns:
            dict: Słownik wszystkich komponentów.
        """
        return self.components

    def load_components(self):
        """
        Załaduj wszystkie zdefiniowane komponenty.
        """
        # Rejestracja wbudowanych komponentów
        self.register(AudioRecordComponent())
        self.register(SpeechToTextComponent())
        self.register(TextToSpeechComponent())
        self.register(LLMQueryComponent())
        self.register(LocalLLMQueryComponent())
        self.register(ParentalControlComponent())
        self.register(ContentFilterComponent())
        self.register(CacheComponent())
        self.register(LoggerComponent())
        self.register(VariableSetComponent())
        self.register(ConditionComponent())
        self.register(LoopComponent())
        self.register(TimerComponent())

        # Można tu dodać automatyczne skanowanie katalogu z niestandardowymi komponentami
        # self._load_custom_components()

    def _load_custom_components(self, package_name='custom_components'):
        """
        Załaduj niestandardowe komponenty z podanego pakietu.

        Args:
            package_name (str): Nazwa pakietu zawierającego niestandardowe komponenty.
        """
        try:
            package = importlib.import_module(package_name)
            for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
                if not is_pkg:
                    module = importlib.import_module(f"{package_name}.{name}")
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        if (inspect.isclass(item) and
                                issubclass(item, Component) and
                                item is not Component):
                            self.register(item())
        except (ImportError, AttributeError) as e:
            print(f"Błąd ładowania niestandardowych komponentów: {str(e)}")


class AudioRecordComponent(Component):
    """
    Komponent do nagrywania dźwięku.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu nagrywania dźwięku.
        """
        super().__init__("audio_record", "Nagrywa dźwięk z mikrofonu")

    def execute(self, params, context):
        """
        Wykonaj nagrywanie dźwięku.

        Args:
            params (dict): Parametry komponentu.
                - duration (int): Czas nagrywania w sekundach.
                - output_var (str): Nazwa zmiennej wyjściowej.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["output_var"])

            duration = self.get_param(params, "duration", 5)
            output_var = params["output_var"]

            # Inicjalizacja procesora audio
            audio = AudioProcessor()

            # Powiadomienie użytkownika o rozpoczęciu nagrywania
            if "tts" in context and self.get_param(params, "announce", True):
                message = self.get_param(params, "announce_message", "Słucham...")
                context["tts"].speak(message)

            # Nagrywanie
            audio_file = audio.start_recording(duration=duration)

            if not audio_file:
                return False, {"error": "Błąd nagrywania dźwięku"}

            # Zapisanie ścieżki pliku audio w kontekście
            if "results" not in context:
                context["results"] = {}

            context["results"][output_var] = audio_file

            return True, {"audio_file": audio_file}

        except Exception as e:
            return False, {"error": f"Błąd nagrywania: {str(e)}"}


class SpeechToTextComponent(Component):
    """
    Komponent do zamiany mowy na tekst.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu STT.
        """
        super().__init__("speech_to_text", "Konwertuje mowę na tekst")

    def execute(self, params, context):
        """
        Wykonaj konwersję mowy na tekst.

        Args:
            params (dict): Parametry komponentu.
                - audio_path (str): Ścieżka do pliku audio lub zmienna zawierająca ścieżkę.
                - output_var (str): Nazwa zmiennej wyjściowej.
                - model_path (str, optional): Ścieżka do modelu STT.
                - language (str, optional): Język rozpoznawania (domyślnie: pl).
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["audio_path", "output_var"])

            audio_path = params["audio_path"]
            output_var = params["output_var"]
            model_path = self.get_param(params, "model_path")
            language = self.get_param(params, "language", "pl")

            # Sprawdź, czy audio_path jest zmienną w kontekście
            if audio_path.startswith("${") and audio_path.endswith("}"):
                var_name = audio_path[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    audio_path = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Inicjalizacja komponentu STT
            stt = WhisperSTT(model_path=model_path) if model_path else WhisperSTT()
            stt.language = language

            # Konwersja mowy na tekst
            transcript = stt.transcribe(audio_path)

            if "Błąd" in transcript:
                return False, {"error": transcript}

            # Zapisanie transkrypcji w kontekście
            if "results" not in context:
                context["results"] = {}

            context["results"][output_var] = transcript

            if "state" not in context:
                context["state"] = {}

            context["state"]["last_transcript"] = transcript

            return True, {"transcript": transcript}

        except Exception as e:
            return False, {"error": f"Błąd konwersji mowy na tekst: {str(e)}"}


class TextToSpeechComponent(Component):
    """
    Komponent do zamiany tekstu na mowę.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu TTS.
        """
        super().__init__("text_to_speech", "Konwertuje tekst na mowę")

    def execute(self, params, context):
        """
        Wykonaj konwersję tekstu na mowę.

        Args:
            params (dict): Parametry komponentu.
                - text (str): Tekst do wypowiedzenia lub zmienna zawierająca tekst.
                - voice_path (str, optional): Ścieżka do modelu głosu.
                - save_to (str, optional): Ścieżka do zapisu pliku audio.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["text"])

            text = params["text"]
            voice_path = self.get_param(params, "voice_path")
            save_to = self.get_param(params, "save_to")

            # Sprawdź, czy text jest zmienną w kontekście
            if text.startswith("${") and text.endswith("}"):
                var_name = text[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    text = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Inicjalizacja komponentu TTS
            tts = PiperTTS(voice_path=voice_path) if voice_path else PiperTTS()

            # Zapisz obiekt TTS w kontekście dla innych komponentów
            context["tts"] = tts

            # Konwersja tekstu na mowę
            if save_to:
                success = tts.save_to_file(text, save_to)
                result = {"file_path": save_to} if success else {"error": "Nie udało się zapisać pliku audio"}
            else:
                success = tts.speak(text)
                result = {"success": success}

            return success, result

        except Exception as e:
            return False, {"error": f"Błąd konwersji tekstu na mowę: {str(e)}"}


class LLMQueryComponent(Component):
    """
    Komponent do zapytań do zewnętrznych modeli językowych.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu LLM.
        """
        super().__init__("llm_query", "Wysyła zapytania do zewnętrznych modeli językowych (np. GPT)")

    def execute(self, params, context):
        """
        Wykonaj zapytanie do modelu językowego.

        Args:
            params (dict): Parametry komponentu.
                - text (str): Zapytanie lub zmienna zawierająca zapytanie.
                - output_var (str): Nazwa zmiennej wyjściowej.
                - context (str, optional): Kontekst rozmowy.
                - api_config (str, optional): Ścieżka do pliku konfiguracyjnego API.
                - use_cache (bool, optional): Czy używać pamięci podręcznej (domyślnie: True).
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["text", "output_var"])

            text = params["text"]
            output_var = params["output_var"]
            conversation_context = self.get_param(params, "context")
            api_config = self.get_param(params, "api_config")
            use_cache = self.get_param(params, "use_cache", True)

            # Sprawdź, czy text jest zmienną w kontekście
            if text.startswith("${") and text.endswith("}"):
                var_name = text[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    text = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Inicjalizacja LLM API
            api = SafeAPIConnector(config_file=api_config) if api_config else SafeAPIConnector()

            # Zapisz API w kontekście dla innych komponentów
            context["api"] = api

            # Inicjalizacja cache jeśli potrzebne
            if use_cache and "cache" not in context:
                context["cache"] = CacheManager()

            # Wysłanie zapytania
            if use_cache and "cache" in context:
                response = api.query_llm(text, context=conversation_context, cache=context["cache"])
            else:
                response = api.query_llm(text, context=conversation_context)

            # Zapisanie odpowiedzi w kontekście
            if "results" not in context:
                context["results"] = {}

            context["results"][output_var] = response

            if "state" not in context:
                context["state"] = {}

            context["state"]["last_response"] = response

            return True, {"response": response}

        except Exception as e:
            return False, {"error": f"Błąd zapytania do API: {str(e)}"}


class LocalLLMQueryComponent(Component):
    """
    Komponent do zapytań do lokalnych modeli językowych (np. Ollama).
    """

    def __init__(self):
        """
        Inicjalizacja komponentu lokalnego LLM.
        """
        super().__init__("local_llm", "Wysyła zapytania do lokalnych modeli językowych")

    def execute(self, params, context):
        """
        Wykonaj zapytanie do lokalnego modelu językowego.

        Args:
            params (dict): Parametry komponentu.
                - text (str): Zapytanie lub zmienna zawierająca zapytanie.
                - output_var (str): Nazwa zmiennej wyjściowej.
                - context (str, optional): Kontekst rozmowy.
                - config_file (str, optional): Ścieżka do pliku konfiguracyjnego.
                - fallback_to_api (bool, optional): Czy przejść na API w razie błędu (domyślnie: True).
                - use_cache (bool, optional): Czy używać pamięci podręcznej (domyślnie: True).
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["text", "output_var"])

            text = params["text"]
            output_var = params["output_var"]
            conversation_context = self.get_param(params, "context")
            config_file = self.get_param(params, "config_file")
            fallback_to_api = self.get_param(params, "fallback_to_api", True)
            use_cache = self.get_param(params, "use_cache", True)

            # Sprawdź, czy text jest zmienną w kontekście
            if isinstance(text, str) and text.startswith("${") and text.endswith("}"):
                var_name = text[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    text = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Inicjalizacja lokalnego LLM
            local_llm = LocalLLMConnector(config_file=config_file) if config_file else LocalLLMConnector()

            # Zapisz lokalny LLM w kontekście dla innych komponentów
            context["local_llm"] = local_llm

            # Inicjalizacja API jako fallback
            api = None
            if fallback_to_api:
                api = context.get("api")
                if not api:
                    api = SafeAPIConnector()
                    context["api"] = api

            # Inicjalizacja cache jeśli potrzebne
            if use_cache and "cache" not in context:
                context["cache"] = CacheManager()

            # Wysłanie zapytania
            response = local_llm.query_llm(text, context=conversation_context,
                                           api_connector=api if fallback_to_api else None)

            # Zapisanie odpowiedzi w kontekście
            if "results" not in context:
                context["results"] = {}

            context["results"][output_var] = response

            if "state" not in context:
                context["state"] = {}

            context["state"]["last_response"] = response

            return True, {"response": response}

        except Exception as e:
            return False, {"error": f"Błąd zapytania do lokalnego modelu: {str(e)}"}


class ParentalControlComponent(Component):
    """
    Komponent do kontroli rodzicielskiej.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu kontroli rodzicielskiej.
        """
        super().__init__("parental_control", "Sprawdza ograniczenia rodzicielskie")

    def execute(self, params, context):
        """
        Wykonaj sprawdzenie kontroli rodzicielskiej.

        Args:
            params (dict): Parametry komponentu.
                - action (str): Akcja do wykonania (check_time, check_usage, filter_input).
                - input_text (str, optional): Tekst do filtrowania (wymagany dla filter_input).
                - output_var (str, optional): Nazwa zmiennej wyjściowej (dla filter_input).
                - config_file (str, optional): Ścieżka do pliku konfiguracyjnego.
                - update_usage (bool, optional): Czy aktualizować statystyki użycia (domyślnie: False).
                - usage_minutes (int, optional): Liczba minut do dodania (domyślnie: 1).
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["action"])

            action = params["action"]
            config_file = self.get_param(params, "config_file")

            # Inicjalizacja kontroli rodzicielskiej
            pc = ParentalControl(config_file=config_file) if config_file else ParentalControl()

            # Zapisz kontrolę rodzicielską w kontekście dla innych komponentów
            context["parental_control"] = pc

            if action == "check_time":
                # Sprawdzenie ograniczeń czasowych
                allowed = pc.check_time_restrictions()
                result = {"allowed": allowed}

                return allowed, result

            elif action == "check_usage":
                # Sprawdzenie limitu czasu użytkowania
                allowed = pc.check_usage_limit()

                # Aktualizacja statystyk użycia
                if allowed and self.get_param(params, "update_usage", False):
                    usage_minutes = self.get_param(params, "usage_minutes", 1)
                    pc.update_usage(minutes=usage_minutes)

                result = {
                    "allowed": allowed,
                    "remaining_minutes": pc.get_remaining_time()
                }

                return allowed, result

            elif action == "filter_input":
                # Sprawdzenie treści
                self.validate_params(params, ["input_text", "output_var"])

                input_text = params["input_text"]
                output_var = params["output_var"]

                # Sprawdź, czy input_text jest zmienną w kontekście
                if isinstance(input_text, str) and input_text.startswith("${") and input_text.endswith("}"):
                    var_name = input_text[2:-1].strip()
                    parts = var_name.split('.')
                    current = context
                    try:
                        for part in parts:
                            current = current.get(part, "")
                        input_text = current
                    except:
                        return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

                filtered_text, filter_message = pc.filter_input(input_text)

                # Zapisanie wyniku w kontekście
                if "results" not in context:
                    context["results"] = {}

                context["results"][output_var] = filtered_text

                result = {
                    "filtered_text": filtered_text,
                    "filter_message": filter_message,
                    "passed": filtered_text is not None
                }

                return filtered_text is not None, result

            else:
                return False, {"error": f"Nieznana akcja: {action}"}

        except Exception as e:
            return False, {"error": f"Błąd kontroli rodzicielskiej: {str(e)}"}


class ContentFilterComponent(Component):
    """
    Komponent do filtrowania treści.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu filtrowania treści.
        """
        super().__init__("content_filter", "Filtruje treść pod kątem odpowiedniości dla dzieci")

    def execute(self, params, context):
        """
        Wykonaj filtrowanie treści.

        Args:
            params (dict): Parametry komponentu.
                - text (str): Tekst do filtrowania lub zmienna zawierająca tekst.
                - output_var (str): Nazwa zmiennej wyjściowej.
                - age_group (str, optional): Grupa wiekowa (domyślnie: "5-8").
                - filter_file (str, optional): Ścieżka do pliku z regułami filtrowania.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["text", "output_var"])

            text = params["text"]
            output_var = params["output_var"]
            age_group = self.get_param(params, "age_group", "5-8")
            filter_file = self.get_param(params, "filter_file")

            # Sprawdź, czy text jest zmienną w kontekście
            if isinstance(text, str) and text.startswith("${") and text.endswith("}"):
                var_name = text[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    text = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Inicjalizacja filtra zawartości
            content_filter = ContentFilter(filter_file=filter_file) if filter_file else ContentFilter()

            # Zapisz filtr w kontekście dla innych komponentów
            context["content_filter"] = content_filter

            # Filtrowanie treści
            filtered_text = content_filter.sanitize_content(text, age_group=age_group)

            # Analiza edukacyjna
            edu_value = content_filter.evaluate_educational_value(text)

            # Zapisanie wyniku w kontekście
            if "results" not in context:
                context["results"] = {}

            context["results"][output_var] = filtered_text

            result = {
                "filtered_text": filtered_text,
                "educational_value": edu_value["educational_value"],
                "educational_topics": edu_value["topics"]
            }

            return True, result

        except Exception as e:
            return False, {"error": f"Błąd filtrowania treści: {str(e)}"}


class CacheComponent(Component):
    """
    Komponent do zarządzania pamięcią podręczną.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu pamięci podręcznej.
        """
        super().__init__("cache", "Zarządza pamięcią podręczną")

    def execute(self, params, context):
        """
        Wykonaj operację na pamięci podręcznej.

        Args:
            params (dict): Parametry komponentu.
                - action (str): Akcja do wykonania (get, set, clear).
                - key (str, optional): Klucz do operacji (wymagany dla get/set).
                - value (any, optional): Wartość do zapisania (wymagany dla set).
                - output_var (str, optional): Nazwa zmiennej wyjściowej (dla get).
                - cache_file (str, optional): Ścieżka do pliku pamięci podręcznej.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["action"])

            action = params["action"]
            cache_file = self.get_param(params, "cache_file")

            # Inicjalizacja cache
            cache = context.get("cache")
            if not cache:
                cache = CacheManager(cache_file=cache_file) if cache_file else CacheManager()
                context["cache"] = cache

            if action == "get":
                self.validate_params(params, ["key", "output_var"])
                key = params["key"]
                output_var = params["output_var"]

                # Pobierz wartość z pamięci podręcznej
                value = cache.get(key)

                # Zapisz wartość w kontekście
                if "results" not in context:
                    context["results"] = {}

                context["results"][output_var] = value

                return True, {"value": value, "found": value is not None}

            elif action == "set":
                self.validate_params(params, ["key", "value"])
                key = params["key"]
                value = params["value"]

                # Sprawdź, czy value jest zmienną w kontekście
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    var_name = value[2:-1].strip()
                    parts = var_name.split('.')
                    current = context
                    try:
                        for part in parts:
                            current = current.get(part, "")
                        value = current
                    except:
                        return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

                # Zapisz wartość w pamięci podręcznej
                cache.set(key, value)

                return True, {"key": key, "value": value}

            elif action == "clear":
                # Wyczyść pamięć podręczną
                cache.clear()
                return True, {"message": "Pamięć podręczna wyczyszczona"}

            else:
                return False, {"error": f"Nieznana akcja: {action}"}

        except Exception as e:
            return False, {"error": f"Błąd zarządzania pamięcią podręczną: {str(e)}"}


class LoggerComponent(Component):
    """
    Komponent do logowania.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu logowania.
        """
        super().__init__("logger", "Zapisuje logi")

    def execute(self, params, context):
        """
        Wykonaj logowanie.

        Args:
            params (dict): Parametry komponentu.
                - level (str): Poziom logowania (debug, info, warning, error, critical).
                - message (str): Wiadomość do zalogowania.
                - log_dir (str, optional): Katalog logów.
                - log_to_console (bool, optional): Czy logować do konsoli (domyślnie: True).
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["level", "message"])

            level = params["level"].lower()
            message = params["message"]
            log_dir = self.get_param(params, "log_dir")
            log_to_console = self.get_param(params, "log_to_console", True)

            # Sprawdź, czy message jest zmienną w kontekście
            if isinstance(message, str) and message.startswith("${") and message.endswith("}"):
                var_name = message[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    message = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Mapowanie poziomów logowania na liczby
            level_map = {
                "debug": 10,
                "info": 20,
                "warning": 30,
                "error": 40,
                "critical": 50
            }

            # Inicjalizacja loggera
            logger = context.get("logger")
            if not logger:
                numeric_level = level_map.get(level, 20)
                logger = Logger(level=numeric_level, log_to_console=log_to_console, log_dir=log_dir)
                context["logger"] = logger

            # Wykonaj logowanie
            if level == "debug":
                logger.debug(message)
            elif level == "info":
                logger.info(message)
            elif level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
            elif level == "critical":
                logger.critical(message)
            else:
                return False, {"error": f"Nieznany poziom logowania: {level}"}

            return True, {"level": level, "message": message}

        except Exception as e:
            print(f"Błąd logowania: {str(e)}")
            return False, {"error": f"Błąd logowania: {str(e)}"}


class VariableSetComponent(Component):
    """
    Komponent do ustawiania zmiennych w kontekście.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu ustawiania zmiennych.
        """
        super().__init__("variable_set", "Ustawia zmienną w kontekście")

    def execute(self, params, context):
        """
        Ustaw zmienną w kontekście.

        Args:
            params (dict): Parametry komponentu.
                - name (str): Nazwa zmiennej.
                - value (any): Wartość zmiennej.
                - scope (str, optional): Zakres zmiennej (variables, state, results). Domyślnie: variables.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["name", "value"])

            name = params["name"]
            value = params["value"]
            scope = self.get_param(params, "scope", "variables")

            # Sprawdź, czy value jest zmienną w kontekście
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1].strip()
                parts = var_name.split('.')
                current = context
                try:
                    for part in parts:
                        current = current.get(part, "")
                    value = current
                except:
                    return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

            # Ustaw zmienną w odpowiednim zakresie
            if scope not in ["variables", "state", "results"]:
                return False, {"error": f"Nieznany zakres: {scope}"}

            if scope not in context:
                context[scope] = {}

            context[scope][name] = value

            return True, {"name": name, "value": value, "scope": scope}

        except Exception as e:
            return False, {"error": f"Błąd ustawiania zmiennej: {str(e)}"}


class ConditionComponent(Component):
    """
    Komponent do oceny warunku.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu warunku.
        """
        super().__init__("condition", "Ocenia warunek i wykonuje odpowiednią akcję")

    def execute(self, params, context):
        """
        Oceń warunek i wykonaj odpowiednią akcję.

        Args:
            params (dict): Parametry komponentu.
                - condition (str): Warunek do oceny w Pythonie.
                - true_pipeline (list, optional): Kroki do wykonania, jeśli warunek jest prawdziwy.
                - false_pipeline (list, optional): Kroki do wykonania, jeśli warunek jest fałszywy.
                - output_var (str, optional): Nazwa zmiennej wyjściowej.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["condition"])

            condition = params["condition"]
            true_pipeline = self.get_param(params, "true_pipeline", [])
            false_pipeline = self.get_param(params, "false_pipeline", [])
            output_var = self.get_param(params, "output_var")

            # Stwórz środowisko oceny warunku
            eval_env = {
                "context": context,
                "variables": context.get("variables", {}),
                "state": context.get("state", {}),
                "results": context.get("results", {})
            }

            # Oceń warunek
            condition_result = bool(eval(condition, {"__builtins__": {}}, eval_env))

            # Wykonaj odpowiednią ścieżkę
            if condition_result and true_pipeline:
                # Wykonaj kroki true_pipeline
                from movatalk.pipeline.engine import PipelineEngine

                sub_engine = PipelineEngine()
                sub_pipeline = {
                    "steps": true_pipeline
                }
                sub_engine.load_pipeline(sub_pipeline)
                sub_engine.pipeline_context = context
                sub_engine.start()

            elif not condition_result and false_pipeline:
                # Wykonaj kroki false_pipeline
                from movatalk.pipeline.engine import PipelineEngine

                sub_engine = PipelineEngine()
                sub_pipeline = {
                    "steps": false_pipeline
                }
                sub_engine.load_pipeline(sub_pipeline)
                sub_engine.pipeline_context = context
                sub_engine.start()

            # Zapisz wynik w kontekście
            if output_var:
                if "results" not in context:
                    context["results"] = {}

                context["results"][output_var] = condition_result

            return True, {"condition_result": condition_result}

        except Exception as e:
            return False, {"error": f"Błąd oceny warunku: {str(e)}"}


class LoopComponent(Component):
    """
    Komponent do wykonywania pętli.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu pętli.
        """
        super().__init__("loop", "Wykonuje powtarzające się operacje")

    def execute(self, params, context):
        """
        Wykonaj pętlę.

        Args:
            params (dict): Parametry komponentu.
                - type (str): Typ pętli (for, while, count).
                - iterations (int, optional): Liczba iteracji (dla typu count).
                - condition (str, optional): Warunek kontynuacji (dla typu while).
                - collection (list, optional): Kolekcja do iteracji (dla typu for).
                - item_var (str, optional): Nazwa zmiennej iteracji (dla typu for).
                - steps (list): Kroki do wykonania w pętli.
                - max_iterations (int, optional): Maksymalna liczba iteracji (zabezpieczenie). Domyślnie: 100.
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["type", "steps"])

            loop_type = params["type"]
            steps = params["steps"]
            max_iterations = self.get_param(params, "max_iterations", 100)

            # Inicjalizacja silnika do wykonania kroków pętli
            from movatalk.pipeline.engine import PipelineEngine
            sub_engine = PipelineEngine()

            # Przygotowanie pod-pipeline'a
            sub_pipeline = {
                "steps": steps
            }

            iterations_done = 0

            # Wykonaj pętlę w zależności od typu
            if loop_type == "count":
                self.validate_params(params, ["iterations"])
                iterations = int(params["iterations"])

                for i in range(min(iterations, max_iterations)):
                    # Aktualizuj kontekst z indeksem iteracji
                    if "variables" not in context:
                        context["variables"] = {}

                    context["variables"]["loop_index"] = i

                    # Wykonaj kroki
                    sub_engine.load_pipeline(sub_pipeline)
                    sub_engine.pipeline_context = context
                    success = sub_engine.start()

                    if not success:
                        return False, {"error": "Błąd wykonania kroków pętli", "iterations_done": iterations_done}

                    iterations_done = i + 1

            elif loop_type == "while":
                self.validate_params(params, ["condition"])
                condition = params["condition"]

                # Stwórz środowisko oceny warunku
                eval_env = {
                    "context": context,
                    "variables": context.get("variables", {}),
                    "state": context.get("state", {}),
                    "results": context.get("results", {})
                }

                # Wykonuj pętlę dopóki warunek jest spełniony
                while (eval(condition, {"__builtins__": {}}, eval_env) and
                       iterations_done < max_iterations):
                    # Aktualizuj kontekst z indeksem iteracji
                    if "variables" not in context:
                        context["variables"] = {}

                    context["variables"]["loop_index"] = iterations_done

                    # Wykonaj kroki
                    sub_engine.load_pipeline(sub_pipeline)
                    sub_engine.pipeline_context = context
                    success = sub_engine.start()

                    if not success:
                        return False, {"error": "Błąd wykonania kroków pętli", "iterations_done": iterations_done}

                    iterations_done += 1

                    # Zaktualizuj środowisko oceny
                    eval_env = {
                        "context": context,
                        "variables": context.get("variables", {}),
                        "state": context.get("state", {}),
                        "results": context.get("results", {})
                    }

            elif loop_type == "for":
                self.validate_params(params, ["collection", "item_var"])
                collection = params["collection"]
                item_var = params["item_var"]

                # Sprawdź, czy collection jest zmienną w kontekście
                if isinstance(collection, str) and collection.startswith("${") and collection.endswith("}"):
                    var_name = collection[2:-1].strip()
                    parts = var_name.split('.')
                    current = context
                    try:
                        for part in parts:
                            current = current.get(part, "")
                        collection = current
                    except:
                        return False, {"error": f"Nie znaleziono zmiennej {var_name}"}

                # Sprawdź, czy collection jest iterowalny
                if not hasattr(collection, '__iter__'):
                    return False, {"error": "Kolekcja nie jest iterowalna"}

                # Iteruj po kolekcji
                for i, item in enumerate(collection[:max_iterations]):
                    # Aktualizuj kontekst z elementem i indeksem
                    if "variables" not in context:
                        context["variables"] = {}

                    context["variables"][item_var] = item
                    context["variables"]["loop_index"] = i

                    # Wykonaj kroki
                    sub_engine.load_pipeline(sub_pipeline)
                    sub_engine.pipeline_context = context
                    success = sub_engine.start()

                    if not success:
                        return False, {"error": "Błąd wykonania kroków pętli", "iterations_done": iterations_done}

                    iterations_done = i + 1

            else:
                return False, {"error": f"Nieznany typ pętli: {loop_type}"}

            return True, {
                "iterations_done": iterations_done,
                "max_reached": iterations_done >= max_iterations
            }

        except Exception as e:
            return False, {"error": f"Błąd wykonania pętli: {str(e)}"}


class TimerComponent(Component):
    """
    Komponent do operacji związanych z czasem.
    """

    def __init__(self):
        """
        Inicjalizacja komponentu timera.
        """
        super().__init__("timer", "Wykonuje operacje związane z czasem")

    def execute(self, params, context):
        """
        Wykonaj operację związaną z czasem.

        Args:
            params (dict): Parametry komponentu.
                - action (str): Akcja do wykonania (sleep, measure_start, measure_end).
                - duration (float, optional): Czas w sekundach (dla sleep).
                - timer_name (str, optional): Nazwa timera (dla measure_start/measure_end).
                - output_var (str, optional): Nazwa zmiennej wyjściowej (dla measure_end).
            context (dict): Kontekst wykonania pipeline'a.

        Returns:
            tuple: (success, result) - Czy operacja się powiodła i jej wynik.
        """
        try:
            self.validate_params(params, ["action"])

            action = params["action"]

            if action == "sleep":
                self.validate_params(params, ["duration"])
                duration = float(params["duration"])

                # Uśpij wątek
                time.sleep(duration)

                return True, {"slept_for": duration}

            elif action == "measure_start":
                self.validate_params(params, ["timer_name"])
                timer_name = params["timer_name"]

                # Rozpocznij pomiar czasu
                if "timers" not in context:
                    context["timers"] = {}

                context["timers"][timer_name] = time.time()

                return True, {"timer_name": timer_name, "started_at": context["timers"][timer_name]}

            elif action == "measure_end":
                self.validate_params(params, ["timer_name"])
                timer_name = params["timer_name"]
                output_var = self.get_param(params, "output_var")

                # Sprawdź czy timer istnieje
                if "timers" not in context or timer_name not in context["timers"]:
                    return False, {"error": f"Timer {timer_name} nie został uruchomiony"}

                # Oblicz czas
                start_time = context["timers"][timer_name]
                end_time = time.time()
                duration = end_time - start_time

                # Zapisz wynik w kontekście
                if output_var:
                    if "results" not in context:
                        context["results"] = {}

                    context["results"][output_var] = duration

                return True, {"timer_name": timer_name, "duration": duration}

            else:
                return False, {"error": f"Nieznana akcja: {action}"}

        except Exception as e:
            return False, {"error": f"Błąd operacji timera: {str(e)}"}