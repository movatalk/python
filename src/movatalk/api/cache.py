# movatalk/api/cache.py
"""
Moduł do zarządzania pamięcią podręczną API w movatalk.
"""

import os
import json
import time
from datetime import datetime, timedelta


class CacheManager:
    """
    Klasa zarządzająca pamięcią podręczną dla zapytań API.
    """

    def __init__(self, cache_file=None, ttl=86400):
        """
        Inicjalizacja menedżera pamięci podręcznej.

        Args:
            cache_file (str, optional): Ścieżka do pliku pamięci podręcznej.
            ttl (int, optional): Czas życia wpisów w sekundach (domyślnie 24h).
        """
        # Domyślna ścieżka pliku cache
        if cache_file is None:
            self.cache_file = os.path.expanduser("~/.movatalk/api_cache.json")
        else:
            self.cache_file = os.path.expanduser(cache_file)

        self.ttl = ttl
        self.cache = {}
        self.load_cache()

    def load_cache(self):
        """
        Wczytaj pamięć podręczną z pliku.
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)

                # Filtruj nieaktualne wpisy
                current_time = time.time()
                self.cache = {
                    k: v for k, v in cache_data.items()
                    if 'timestamp' in v and current_time - v['timestamp'] < self.ttl
                }

                # Zapisz odfiltrowane dane
                if len(cache_data) != len(self.cache):
                    self.save_cache()

            else:
                self.cache = {}

        except Exception as e:
            print(f"Błąd wczytywania pamięci podręcznej: {str(e)}")
            self.cache = {}

    def save_cache(self):
        """
        Zapisz pamięć podręczną do pliku.
        """
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania pamięci podręcznej: {str(e)}")

    def get(self, key):
        """
        Pobierz wartość z pamięci podręcznej.

        Args:
            key (str): Klucz wpisu.

        Returns:
            object: Wartość wpisu lub None jeśli nie znaleziono.
        """
        if key in self.cache:
            entry = self.cache[key]

            # Sprawdź czy wpis jest aktualny
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['data']

        return None

    def set(self, key, data):
        """
        Zapisz wartość do pamięci podręcznej.

        Args:
            key (str): Klucz wpisu.
            data (object): Dane do zapisania.
        """
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        self.save_cache()

    def clear(self):
        """
        Wyczyść całą pamięć podręczną.
        """
        self.cache = {}
        self.save_cache()

    def remove(self, key):
        """
        Usuń wpis z pamięci podręcznej.

        Args:
            key (str): Klucz wpisu do usunięcia.

        Returns:
            bool: True jeśli usunięto wpis, False jeśli nie znaleziono.
        """
        if key in self.cache:
            del self.cache[key]
            self.save_cache()
            return True
        return False

    def size(self):
        """
        Zwróć rozmiar pamięci podręcznej.

        Returns:
            int: Liczba wpisów w pamięci podręcznej.
        """
        return len(self.cache)

    def cleanup(self):
        """
        Usuń nieaktualne wpisy z pamięci podręcznej.
        """
        current_time = time.time()
        old_size = len(self.cache)

        self.cache = {
            k: v for k, v in self.cache.items()
            if 'timestamp' in v and current_time - v['timestamp'] < self.ttl
        }

        if old_size != len(self.cache):
            self.save_cache()

        return old_size - len(self.cache)