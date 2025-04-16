# kidsvoiceai/safety/parental_control.py
"""
Moduł kontroli rodzicielskiej w KidsVoiceAI.
"""

import os
import json
import re
from datetime import datetime, timedelta


class ParentalControl:
    """
    Klasa do kontroli rodzicielskiej, filtrowania treści i ograniczania czasu.
    """

    def __init__(self, config_file=None):
        """
        Inicjalizacja kontroli rodzicielskiej.

        Args:
            config_file (str, optional): Ścieżka do pliku konfiguracyjnego.
        """
        # Domyślna ścieżka konfiguracji
        if config_file is None:
            self.config_path = os.path.expanduser("~/.kidsvoiceai/parental_control.json")
        else:
            self.config_path = os.path.expanduser(config_file)

        self.load_config()
        self.initialize_usage_stats()

    def load_config(self):
        """