# movatalk/api/connector.py
"""
Moduł do bezpiecznego łączenia z API LLM w movatalk.
"""

import os
import json
import requests
from datetime import datetime


class SafeAPIConnector:
    """
    Klasa do bezpiecznego łączenia z API modeli językowych.
    """

    def __init__(self, config_file=None):
        """
        Inicjalizacja łącznika API.

        Args:
            config_file (str, optional): Ścieżka do pliku konfiguracyjnego.
        """
        # Domyślna ścieżka konfiguracji
        if config_file is None:
            self.config_path = os.path.expanduser("~/.movatalk/api_config.json")
        else:
            self.config_path = os.path.expanduser(config_file)

        self.load_config()

        # Inicjalizacja pamięci podręcznej
        self.cache = {}
        self.cache_file = os.path.expanduser("~/.movatalk/api_cache.json")
        self.load_cache()

    def load_config(self):
        """
        Wczytaj konfigurację API.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                print(f"Plik konfiguracyjny {self.config_path} nie istnieje. Używanie domyślnej konfiguracji.")
                self.config = {
                    "api_key": "",
                    "endpoint": "https://api.openai.com/v1/chat/completions",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "child_safe_filter": True
                }

                # Utworzenie katalogu i zapisanie domyślnej konfiguracji
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)

        except Exception as e:
            print(f"Błąd wczytywania konfiguracji: {str(e)}")
            self.config = {
                "api_key": "",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-3.5-turbo",
                "max_tokens": 150,
                "temperature": 0.7,
                "child_safe_filter": True
            }

    def load_cache(self):
        """
        Wczytaj pamięć podręczną.
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"Błąd wczytywania pamięci podręcznej: {str(e)}")
            self.cache = {}

    def save_cache(self):
        """
        Zapisz pamięć podręczną.
        """
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania pamięci podręcznej: {str(e)}")

    def query_llm(self, text_input, context=None, use_cache=True):
        """
        Wyślij zapytanie tekstowe do API LLM.

        Args:
            text_input (str): Tekst zapytania.
            context (str, optional): Kontekst rozmowy.
            use_cache (bool, optional): Czy używać pamięci podręcznej.

        Returns:
            str: Odpowiedź modelu lub komunikat błędu.
        """
        if not self.config["api_key"]:
            return "Brak skonfigurowanego klucza API. Proszę skonfigurować klucz API w pliku ~/.movatalk/api_config.json"

        # Sprawdzenie w pamięci podręcznej
        if use_cache:
            cache_key = f"{text_input}_{context}"
            if cache_key in self.cache:
                print("Używanie odpowiedzi z pamięci podręcznej.")
                return self.cache[cache_key]

        # Przygotowanie kontekstu i instrukcji
        system_message = (
            "Jesteś pomocnym, przyjaznym i edukacyjnym asystentem dla dzieci. "
            "Odpowiadaj krótko, prosto i z entuzjazmem. Nigdy nie używaj nieodpowiednich, "
            "strasznych czy zbyt skomplikowanych treści. Zawsze bądź pomocny, miły i edukacyjny. "
            "Używaj języka odpowiedniego dla dzieci, unikaj trudnych słów i skomplikowanych koncepcji. "
            "Jeśli jesteś pytany o tematy nieodpowiednie dla dzieci, grzecznie przekieruj rozmowę "
            "na bardziej odpowiedni temat."
        )

        # Dodanie kontekstu jeśli dostępny
        if context:
            system_message += f" Kontekst rozmowy: {context}"

        # Przygotowanie zapytania
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}"
        }

        payload = {
            "model": self.config["model"],
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text_input}
            ],
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"]
        }

        try:
            response = requests.post(
                self.config["endpoint"],
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Zapisz do pamięci podręcznej
                if use_cache:
                    self.cache[cache_key] = content
                    # Ograniczenie rozmiaru pamięci podręcznej
                    if len(self.cache) > 100:
                        # Usuń najstarsze wpisy
                        keys = list(self.cache.keys())
                        for old_key in keys[:50]:
                            del self.cache[old_key]
                    self.save_cache()

                return content
            else:
                return f"Błąd API: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Błąd komunikacji: {str(e)}"

    def query_offline(self, text_input):
        """
        Zapytanie offline - używa prostych, predefiniowanych odpowiedzi.

        Args:
            text_input (str): Tekst zapytania.

        Returns:
            str: Prosta odpowiedź.
        """
        # Bardzo prosty mechanizm odpowiedzi offline
        text_lower = text_input.lower()

        responses = {
            "cześć": "Cześć! Jak mogę Ci dzisiaj pomóc?",
            "hej": "Hej! Miło Cię słyszeć!",
            "jak się masz": "Mam się dobrze, dziękuję za pytanie! A Ty?",
            "co robisz": "Pomagam Ci odpowiadać na pytania i uczę się razem z Tobą!",
            "kim jesteś": "Jestem Twoim asystentem głosowym. Mogę odpowiadać na pytania i pomagać Ci w nauce.",
            "do widzenia": "Do widzenia! Miło było z Tobą rozmawiać.",
            "pa": "Pa pa! Do zobaczenia wkrótce!",
            "dziękuję": "Nie ma za co! Zawsze chętnie pomagam.",
        }

        # Szukaj dopasowania w predefiniowanych odpowiedziach
        for key, response in responses.items():
            if key in text_lower:
                return response

        # Domyślna odpowiedź
        return "Przepraszam, obecnie pracuję w trybie offline. Nie mogę odpowiedzieć na to pytanie bez połączenia z internetem."