# movatalk/api/local_llm.py
"""
Moduł do integracji z lokalnymi modelami językowymi (LLM) takimi jak Ollama.
"""

import json
import os
import subprocess
import time
import requests


class LocalLLMConnector:
    """
    Klasa do komunikacji z lokalnymi modelami językowymi (LLM).
    Obecnie wspiera Ollama, ale może być rozszerzona o inne lokalne modele.
    """

    def __init__(self, config_file=None):
        """
        Inicjalizacja konektora do lokalnego LLM.

        Args:
            config_file (str, optional): Ścieżka do pliku konfiguracyjnego.
        """
        # Domyślna ścieżka konfiguracji
        if config_file is None:
            self.config_path = os.path.expanduser("~/.movatalk/local_llm_config.json")
        else:
            self.config_path = os.path.expanduser(config_file)

        self.load_config()

        # Sprawdzenie czy model jest dostępny
        if self.config["provider"] == "ollama":
            self.check_ollama_status()

    def load_config(self):
        """
        Wczytaj konfigurację lokalnego LLM.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                print(f"Plik konfiguracyjny {self.config_path} nie istnieje. Używanie domyślnej konfiguracji.")
                # Domyślna konfiguracja
                self.config = {
                    "provider": "ollama",
                    "model": "llama2",
                    "endpoint": "http://localhost:11434/api/generate",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "use_local_first": True,  # Preferuj lokalny model przed API
                    "fallback_to_api": True,  # W razie błędu z lokalnym modelem użyj API
                    "system_prompt": "Jesteś pomocnym, przyjaznym i edukacyjnym asystentem dla dzieci. Odpowiadaj krótko, prosto i z entuzjazmem."
                }

                # Utworzenie katalogu i zapisanie domyślnej konfiguracji
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)

        except Exception as e:
            print(f"Błąd wczytywania konfiguracji lokalnego LLM: {str(e)}")
            self.config = {
                "provider": "ollama",
                "model": "llama2",
                "endpoint": "http://localhost:11434/api/generate",
                "temperature": 0.7,
                "max_tokens": 500,
                "use_local_first": True,
                "fallback_to_api": True,
                "system_prompt": "Jesteś pomocnym, przyjaznym i edukacyjnym asystentem dla dzieci. Odpowiadaj krótko, prosto i z entuzjazmem."
            }

    def check_ollama_status(self):
        """
        Sprawdź status Ollama i pobierz dostępne modele.

        Returns:
            bool: True jeśli Ollama jest dostępne, False w przeciwnym razie.
        """
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                self.available_models = [model["name"] for model in models]

                # Sprawdź czy skonfigurowany model jest dostępny
                if self.config["model"] not in self.available_models and len(self.available_models) > 0:
                    print(f"Model {self.config['model']} nie jest dostępny. Używanie {self.available_models[0]}.")
                    self.config["model"] = self.available_models[0]

                print(f"Ollama dostępne. Znaleziono modele: {', '.join(self.available_models)}")
                return True
            else:
                print(f"Ollama zwróciło kod błędu: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            print("Nie można połączyć się z Ollama. Sprawdź czy serwer jest uruchomiony.")
            self.available_models = []
            return False
        except Exception as e:
            print(f"Błąd podczas sprawdzania statusu Ollama: {str(e)}")
            self.available_models = []
            return False

    def ensure_model_is_pulled(self, model=None):
        """
        Upewnij się, że model jest pobrany lokalnie.

        Args:
            model (str, optional): Nazwa modelu. Jeśli None, użyj domyślnego modelu z konfiguracji.

        Returns:
            bool: True jeśli model jest dostępny, False w przeciwnym razie.
        """
        if model is None:
            model = self.config["model"]

        # Sprawdź czy model jest już dostępny
        if hasattr(self, 'available_models') and model in self.available_models:
            return True

        # Spróbuj pobrać model
        try:
            print(f"Pobieranie modelu {model}...")
            response = requests.post(
                "http://localhost:11434/api/pull",
                json={"name": model}
            )

            if response.status_code == 200:
                print(f"Model {model} pobrany pomyślnie.")
                if not hasattr(self, 'available_models'):
                    self.available_models = []
                self.available_models.append(model)
                return True
            else:
                print(f"Błąd pobierania modelu: {response.status_code}")
                return False

        except Exception as e:
            print(f"Błąd podczas pobierania modelu: {str(e)}")
            return False

    def query_ollama(self, text_input, context=None):
        """
        Wyślij zapytanie do Ollama.

        Args:
            text_input (str): Tekst zapytania.
            context (str, optional): Kontekst rozmowy.

        Returns:
            str: Odpowiedź modelu lub komunikat błędu.
        """
        # Upewnij się, że model jest dostępny
        if not self.ensure_model_is_pulled():
            return "Błąd: Wymagany model nie jest dostępny."

        try:
            # Przygotowanie zapytania
            prompt = text_input

            # Dodanie kontekstu, jeśli dostępny
            if context:
                prompt = f"Kontekst: {context}\n\nPytanie: {text_input}"

            # Zapytanie do Ollama
            payload = {
                "model": self.config["model"],
                "prompt": prompt,
                "system": self.config["system_prompt"],
                "temperature": self.config["temperature"],
                "max_tokens": self.config["max_tokens"]
            }

            response = requests.post(
                self.config["endpoint"],
                json=payload,
                stream=False  # Nie używamy strumieniowania
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Brak odpowiedzi od modelu.")
            else:
                return f"Błąd API: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Błąd komunikacji z lokalnym modelem: {str(e)}"

    def query_llm(self, text_input, context=None, api_connector=None):
        """
        Wyślij zapytanie do lokalnego LLM z opcjonalnym fallbackiem do API.

        Args:
            text_input (str): Tekst zapytania.
            context (str, optional): Kontekst rozmowy.
            api_connector (SafeAPIConnector, optional): Konektor do zewnętrznego API.

        Returns:
            str: Odpowiedź modelu lub komunikat błędu.
        """
        # Najpierw spróbuj użyć lokalnego modelu, jeśli skonfigurowano
        if self.config["use_local_first"]:
            if self.config["provider"] == "ollama":
                response = self.query_ollama(text_input, context)

                # Jeśli odpowiedź nie zawiera błędu, zwróć ją
                if not response.startswith("Błąd:"):
                    return response

                # W przeciwnym razie, jeśli skonfigurowano fallback, użyj API
                if self.config["fallback_to_api"] and api_connector:
                    print("Używanie fallbacku do zewnętrznego API.")
                    return api_connector.query_llm(text_input, context)
                else:
                    return response
            else:
                return "Błąd: Nieobsługiwany dostawca lokalnego LLM."
        else:
            # Jeśli lokalny model nie jest preferowany, użyj API
            if api_connector:
                return api_connector.query_llm(text_input, context)
            else:
                return "Błąd: Brak skonfigurowanego konektora API."

    def start_ollama_server(self):
        """
        Uruchom serwer Ollama jeśli nie jest uruchomiony.

        Returns:
            bool: True jeśli serwer został uruchomiony, False w przeciwnym razie.
        """
        # Sprawdź czy Ollama jest już uruchomione
        if self.check_ollama_status():
            return True

        # Spróbuj uruchomić serwer Ollama
        try:
            print("Uruchamianie serwera Ollama...")

            # Uruchomienie w tle
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Poczekaj chwilę na uruchomienie
            time.sleep(5)

            # Sprawdź czy serwer jest dostępny
            if self.check_ollama_status():
                print("Serwer Ollama uruchomiony pomyślnie.")
                return True
            else:
                print("Nie udało się uruchomić serwera Ollama.")
                return False

        except Exception as e:
            print(f"Błąd podczas uruchamiania serwera Ollama: {str(e)}")
            return False
