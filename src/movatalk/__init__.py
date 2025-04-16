# Inicjalizacja pakietu
"""
movatalk - Bezpieczny interfejs głosowy AI dla dzieci.

Biblioteka movatalk zapewnia narzędzia do tworzenia bezpiecznych
aplikacji głosowych AI dla dzieci, z kontrolą rodzicielską
i przetwarzaniem lokalnym.
"""

__version__ = "0.1.3"

from movatalk.audio import AudioProcessor, WhisperSTT, PiperTTS
from movatalk.api import SafeAPIConnector, CacheManager
from movatalk.hardware import HardwareInterface, PowerManager
from movatalk.safety import ParentalControl, ContentFilter
from movatalk.utils import ConfigManager

# Domyślna konfiguracja całej biblioteki
import os
import json

CONFIG_DIR = os.path.expanduser("~/.movatalk")
os.makedirs(CONFIG_DIR, exist_ok=True)


# Sprawdzenie i utworzenie domyślnych plików konfiguracyjnych
def create_default_config(name, default_content):
    config_path = os.path.join(CONFIG_DIR, name)
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(default_content, f, indent=2)
        print(f"Utworzono domyślny plik konfiguracyjny: {config_path}")


# Domyślna konfiguracja biblioteki, tworzona przy pierwszym imporcie
def initialize_default_configs():
    # Domyślna konfiguracja API
    api_config = {
        "api_key": "",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-3.5-turbo",
        "max_tokens": 150,
        "temperature": 0.7,
        "child_safe_filter": True
    }
    create_default_config("api_config.json", api_config)

    # Domyślna konfiguracja kontroli rodzicielskiej
    parental_config = {
        "max_daily_usage_mins": 60,
        "allowed_hours_start": 8,
        "allowed_hours_end": 20,
        "blocked_topics": ["przemoc", "strach", "polityka", "seks", "narkotyki", "alkohol"],
        "educational_focus": True,
        "educational_topics": ["nauka", "historia", "matematyka", "przyroda", "języki", "sztuka", "muzyka"],
        "profanity_filter": True
    }
    create_default_config("parental_control.json", parental_config)

    # Domyślna konfiguracja systemu
    system_config = {
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "record_seconds": 5
        },
        "stt": {
            "model_path": os.path.expanduser("~/.movatalk/models/stt/models/ggml-tiny.bin"),
            "language": "pl"
        },
        "tts": {
            "voice_path": os.path.expanduser("~/.local/share/piper/voices/pl/krzysztof/low/pl_krzysztof_low.onnx")
        },
        "hardware": {
            "led_power_pin": 22,
            "led_recording_pin": 23,
            "led_thinking_pin": 24,
            "button_record_pin": 17,
            "button_power_pin": 27
        }
    }
    create_default_config("system_config.json", system_config)


# Inicjalizacja konfiguracji przy imporcie
initialize_default_configs()