kidsvoiceai/
├── LICENSE                           # Licencja MIT
├── README.md                         # Główny plik README z opisem projektu
├── MANIFEST.in                       # Pliki statyczne do uwzględnienia w pakiecie
├── pyproject.toml                    # Konfiguracja projektu Python
├── setup.py                          # Skrypt instalacyjny pakietu
├── .gitlab-ci.yml                    # Konfiguracja CI/CD dla GitLab
├── .gitignore                        # Pliki ignorowane przez git
│
├── scripts/                          # Skrypty instalacyjne i konfiguracyjne
│   ├── install_dependencies.sh       # Instalacja zależności systemowych
│   ├── install_models.sh             # Pobieranie modeli STT i TTS
│   ├── configure_hardware.sh         # Konfiguracja sprzętu
│   ├── setup_service.sh              # Konfiguracja usługi systemd
│   └── optimize_rpi.sh               # Optymalizacja Raspberry Pi
│
├── config/                           # Domyślne pliki konfiguracyjne
│   ├── default_api_config.json       # Konfiguracja API
│   ├── default_parental_control.json # Ustawienia kontroli rodzicielskiej
│   └── default_system_config.json    # Główna konfiguracja systemu
│
├── docs/                             # Dokumentacja
│   ├── installation.md               # Przewodnik instalacji
│   ├── hardware_setup.md             # Konfiguracja sprzętowa
│   ├── api_reference.md              # Referencja API
│   ├── examples.md                   # Przykłady użycia
│   ├── pipelines.md                  # Dokumentacja systemu pipelinów
│   └── images/                       # Zasoby graficzne
│       ├── logo.svg                  # Logo projektu
│       ├── hardware_diagram.png      # Schemat podłączenia sprzętu
│       └── pipeline_schema.svg       # Schemat działania pipelinów
│
├── examples/                         # Przykłady użycia
│   ├── simple_assistant.py           # Przykład prostego asystenta
│   ├── educational_quiz.py           # Przykład quizu edukacyjnego
│   ├── storyteller.py                # Przykład opowiadacza historii
│   └── pipelines/                    # Przykłady pipelinów
│       ├── simple_assistant.yaml     # Pipeline prostego asystenta
│       ├── educational_quiz.yaml     # Pipeline quizu edukacyjnego
│       └── storyteller.yaml          # Pipeline opowiadacza historii
│
├── deployment/                       # Narzędzia wdrożeniowe
│   └── ansible/                      # Pliki Ansible
│       ├── inventory.ini             # Konfiguracja hostów
│       └── kidsvoiceai-deploy.yml    # Playbook Ansible
│
├── tests/                            # Testy jednostkowe
│   ├── __init__.py
│   ├── test_audio.py                 # Testy modułu audio
│   ├── test_api.py                   # Testy modułu API
│   ├── test_safety.py                # Testy modułu bezpieczeństwa
│   ├── test_hardware.py              # Testy modułu sprzętowego
│   └── test_pipeline.py              # Testy systemu pipelinów
│
└── kidsvoiceai/                      # Główny pakiet
    ├── __init__.py                   # Inicjalizacja pakietu
    ├── __main__.py                   # Punkt wejścia dla modułu
    │
    ├── audio/                        # Moduł przetwarzania audio
    │   ├── __init__.py               # Eksportuje AudioProcessor, WhisperSTT, PiperTTS
    │   ├── processor.py              # Przetwarzanie i nagrywanie dźwięku
    │   ├── stt.py                    # Rozpoznawanie mowy (STT)
    │   └── tts.py                    # Synteza mowy (TTS)
    │
    ├── api/                          # Moduł integracji z API
    │   ├── __init__.py               # Eksportuje SafeAPIConnector, LocalLLMConnector, CacheManager
    │   ├── connector.py              # Połączenie z zewnętrznymi API
    │   ├── local_llm.py              # Integracja z lokalnymi modelami językowymi
    │   └── cache.py                  # Zarządzanie pamięcią podręczną
    │
    ├── hardware/                     # Moduł interfejsu sprzętowego
    │   ├── __init__.py               # Eksportuje HardwareInterface, PowerManager, LoRaConnector
    │   ├── interface.py              # Interfejs przycisków i diod LED
    │   ├── power.py                  # Zarządzanie energią
    │   └── lora.py                   # Komunikacja LoRaWAN
    │
    ├── safety/                       # Moduł bezpieczeństwa i kontroli rodzicielskiej
    │   ├── __init__.py               # Eksportuje ParentalControl, ContentFilter
    │   ├── parental_control.py       # Kontrola rodzicielska
    │   └── content_filter.py         # Filtrowanie treści
    │
    ├── utils/                        # Moduł narzędzi pomocniczych
    │   ├── __init__.py               # Eksportuje ConfigManager, Logger
    │   ├── config.py                 # Zarządzanie konfiguracją
    │   └── logging.py                # Logowanie
    │
    ├── cli/                          # Moduł interfejsu linii poleceń
    │   ├── __init__.py
    │   └── commands.py               # Komendy CLI
    │
    └── pipeline/                     # Moduł systemu pipelinów
        ├── __init__.py               # Eksportuje PipelineEngine, YamlParser, ComponentRegistry
        ├── engine.py                 # Silnik wykonujący pipeliny
        ├── parser.py                 # Parser plików YAML
        ├── components.py             # Komponenty pipelinów
        └── designer.py               # Wizualny projektant pipelinów