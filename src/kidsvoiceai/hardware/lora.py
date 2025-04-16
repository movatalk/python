# kidsvoiceai/hardware/lora.py
"""
Moduł do obsługi komunikacji LoRaWAN w KidsVoiceAI.
"""

import os
import time
import threading
import json
import importlib.util


class LoRaConnector:
    """
    Klasa do komunikacji poprzez LoRaWAN.
    """

    def __init__(self, config_file=None):
        """
        Inicjalizacja komunikacji LoRaWAN.

        Args:
            config_file (str, optional): Ścieżka do pliku konfiguracyjnego.
        """
        # Sprawdź czy mamy dostęp do biblioteki SX127x
        self.has_lora = importlib.util.find_spec("SX127x") is not None

        # Domyślna ścieżka konfiguracji
        if config_file is None:
            self.config_path = os.path.expanduser("~/.kidsvoiceai/lora_config.json")
        else:
            self.config_path = os.path.expanduser(config_file)

        # Wczytanie konfiguracji
        self.load_config()

        # Stan połączenia
        self.is_connected = False
        self.lora_device = None

        # Kolejka wiadomości
        self.message_queue = []
        self.message_lock = threading.Lock()

        # Wątek wysyłania
        self.sending_thread = None
        self.sending_active = False

        # Inicjalizacja LoRa jeśli dostępne
        if self.has_lora and self.config.get("enabled", False):
            self._initialize_lora()

    def load_config(self):
        """
        Wczytaj konfigurację LoRaWAN.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                print(f"Plik konfiguracyjny {self.config_path} nie istnieje. Używanie domyślnej konfiguracji.")
                self.config = {
                    "enabled": False,
                    "frequency": 868.1,  # MHz (Europa)
                    "spreading_factor": 7,
                    "coding_rate": 5,
                    "bandwidth": 125,  # kHz
                    "power": 17,  # dBm
                    "sync_word": 0x34,
                    "gateway_address": "0000000000000000",
                    "device_address": "FFFFFFFFFFFFFFFF"
                }

                # Utworzenie katalogu i zapisanie domyślnej konfiguracji
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)

        except Exception as e:
            print(f"Błąd wczytywania konfiguracji LoRa: {str(e)}")
            self.config = {
                "enabled": False,
                "frequency": 868.1,
                "spreading_factor": 7,
                "coding_rate": 5,
                "bandwidth": 125,
                "power": 17,
                "sync_word": 0x34,
                "gateway_address": "0000000000000000",
                "device_address": "FFFFFFFFFFFFFFFF"
            }

    def _initialize_lora(self):
        """
        Inicjalizacja modułu LoRa.

        Returns:
            bool: True jeśli inicjalizacja powiodła się, False w przeciwnym razie.
        """
        if not self.has_lora:
            print("Biblioteka LoRa (SX127x) nie jest dostępna.")
            return False

        try:
            from SX127x.LoRa import LoRa
            from SX127x.board_config import BOARD

            # Klasa wewnętrzna rozszerzająca LoRa
            class LoRaImpl(LoRa):
                def __init__(self, verbose=False):
                    BOARD.setup()
                    super(LoRaImpl, self).__init__(verbose)

                def on_rx_done(self):
                    payload = self.read_payload(nocheck=True)
                    print(f"Otrzymano: {payload}")
                    self.set_mode(MODE.SLEEP)
                    self.reset_ptr_rx()
                    self.set_mode(MODE.RXCONT)

                def on_tx_done(self):
                    print("Wysyłanie zakończone")
                    self.set_mode(MODE.SLEEP)
                    self.reset_ptr_rx()
                    self.set_mode(MODE.RXCONT)

            # Inicjalizacja modułu
            from SX127x.constants import MODE
            self.lora_device = LoRaImpl(verbose=False)
            self.MODE = MODE

            # Konfiguracja
            self.lora_device.set_mode(MODE.SLEEP)
            self.lora_device.set_freq(self.config["frequency"])
            self.lora_device.set_spreading_factor(self.config["spreading_factor"])
            self.lora_device.set_coding_rate(self.config["coding_rate"])
            self.lora_device.set_bw(self.config["bandwidth"])
            self.lora_device.set_preamble(8)
            self.lora_device.set_sync_word(self.config["sync_word"])
            self.lora_device.set_rx_crc(True)

            # Przejście do trybu nasłuchiwania
            self.lora_device.set_mode(MODE.RXCONT)

            self.is_connected = True
            print("Moduł LoRa zainicjalizowany pomyślnie.")

            # Uruchomienie wątku wysyłania
            self.start_sending_thread()

            return True

        except Exception as e:
            print(f"Błąd inicjalizacji LoRa: {str(e)}")
            self.is_connected = False
            return False

    def start_sending_thread(self):
        """
        Uruchom wątek wysyłania wiadomości.
        """
        if self.sending_active:
            return

        self.sending_active = True
        self.sending_thread = threading.Thread(target=self._message_sender)
        self.sending_thread.daemon = True
        self.sending_thread.start()

    def _message_sender(self):
        """
        Wątek wysyłający wiadomości z kolejki.
        """
        while self.sending_active:
            # Sprawdź czy jest coś do wysłania
            message_to_send = None
            with self.message_lock:
                if self.message_queue:
                    message_to_send = self.message_queue.pop(0)

            # Wyślij wiadomość
            if message_to_send:
                self._send_message_internal(message_to_send)

            # Zaczekaj chwilę
            time.sleep(0.5)

    def _send_message_internal(self, message):
        """
        Wyślij wiadomość przez LoRa.

        Args:
            message (str): Wiadomość do wysłania.
        """
        if not self.is_connected or not self.lora_device:
            print("LoRa nie jest zainicjalizowane.")
            return False

        try:
            # Konwersja wiadomości na listę bajtów
            message_bytes = list(message.encode())

            # Przygotowanie i wysłanie
            self.lora_device.set_mode(self.MODE.SLEEP)
            self.lora_device.write_payload(message_bytes)
            self.lora_device.set_mode(self.MODE.TX)
            print(f"Wysyłanie przez LoRa: {message}")
            return True

        except Exception as e:
            print(f"Błąd wysyłania przez LoRa: {str(e)}")
            return False

    def send_message(self, message):
        """
        Dodaj wiadomość do kolejki wysyłania.

        Args:
            message (str): Wiadomość do wysłania.

        Returns:
            bool: True jeśli dodano do kolejki, False w przypadku błędu.
        """
        if not self.is_connected:
            print("LoRa nie jest podłączone.")
            return False

        try:
            with self.message_lock:
                self.message_queue.append(message)
            return True

        except Exception as e:
            print(f"Błąd dodawania wiadomości do kolejki: {str(e)}")
            return False

    def cleanup(self):
        """
        Zwolnij zasoby LoRa.
        """
        self.sending_active = False
        if self.sending_thread:
            self.sending_thread.join(1.0)

        if self.is_connected and self.lora_device:
            try:
                self.lora_device.set_mode(self.MODE.SLEEP)
                self.is_connected = False
            except Exception as e:
                print(f"Błąd podczas czyszczenia LoRa: {str(e)}")

