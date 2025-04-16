# movatalk/pipeline/parser.py
"""
Parser konfiguracji pipeline'ów z różnych formatów (YAML, JSON).
"""

import os
import yaml
import json


class YamlParser:
    """
    Parser konfiguracji pipeline'ów z formatu YAML.
    """

    def parse_file(self, file_path):
        """
        Parsuj plik YAML.

        Args:
            file_path (str): Ścieżka do pliku YAML.

        Returns:
            dict: Sparsowana konfiguracja pipeline'a.
        """
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self._validate_config(config)
        return config

    def parse_string(self, yaml_string):
        """
        Parsuj string YAML.

        Args:
            yaml_string (str): String YAML.

        Returns:
            dict: Sparsowana konfiguracja pipeline'a.
        """
        config = yaml.safe_load(yaml_string)
        self._validate_config(config)
        return config

    def _validate_config(self, config):
        """
        Sprawdź poprawność konfiguracji pipeline'a.

        Args:
            config (dict):