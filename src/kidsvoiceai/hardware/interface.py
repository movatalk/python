# kidsvoiceai/hardware/interface.py
"""
Moduł do interfejsu sprzętowego w KidsVoiceAI.
"""

import os
import time
import threading
import importlib.util

# Sprawdzenie czy RPi.GPIO jest dostępne
GPIO_AVAILABLE = importlib.util.find_spec("RPi.GPIO") is not None


class HardwareInterface:
    """
    Klasa do obsługi interfejsu sprzętowego (przyciski, diody LED).
    """

    def __init__(self,
                 led_power_pin=22,
                 led_recording_pin=23,
                 led_thinking_pin=24,
                 button_record_pin=17,
                 button_power_pin=27):
        """
        Inicjalizacja interfejsu sprzętowego.

        Args:
            led_power_pin (int): Numer pinu GPIO dla diody zasilania.
            led_recording_pin (int): Numer pinu GPIO dla diody nagrywania.
            led_thinking_pin (int): Numer pinu GPIO dla diody "myślenia".
            button_record_pin (int): Numer pinu GPIO dla przycisku nagrywania.
            button_power_pin (int): Numer pinu GPIO dla przycisku zasilania.
        """
        # Zapisanie numerów pinów
        self.LED_POWER = led_power_pin
        self.LED_RECORDING = led_recording_pin
        self.LED_THINKING = led_thinking_pin
        self.BUTTON_RECORD = button_record_pin
        self.BUTTON_POWER = button_power_pin

        # Flaga czy mamy dostęp do GPIO
        self.has_gpio = GPIO_AVAILABLE

        # Stan symulowanych diod (dla trybu bez GPIO)
        self.simulated_leds = {
            self.LED_POWER: False,
            self.LED_RECORDING: False,
            self.LED_THINKING: False
        }

        if self.has_gpio:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO

                # Inicjalizacja GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.BUTTON_RECORD, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(self.BUTTON_POWER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(self.LED_POWER, GPIO.OUT)
                GPIO.setup(self.LED_RECORDING, GPIO.OUT)
                GPIO.setup(self.LED_THINKING, GPIO.OUT)

                # Stan początkowy
                GPIO.output(self.LED_POWER, GPIO.HIGH)
                GPIO.output(self.LED_RECORDING, GPIO.LOW)
                GPIO.output(self.LED_THINKING, GPIO.LOW)

            except Exception as e:
                print(f"Błąd inicjalizacji GPIO: {str(e)}")
                self.has_gpio = False
        else:
            print("RPi.GPIO nie jest dostępne. Używanie trybu symulacji.")

        # Callback dla przycisków
        self.record_callback = None
        self.power_callback = None

        # Monitorowanie przycisków
        self.monitoring = False
        self.monitor_thread = None

    def set_record_callback(self, callback):
        """
        Ustaw funkcję callback dla przycisku nagrywania.

        Args:
            callback (function): Funkcja do wywołania po naciśnięciu przycisku.
        """
        self.record_callback = callback

    def set_power_callback(self, callback):
        """
        Ustaw funkcję callback dla przycisku zasilania.

        Args:
            callback (function): Funkcja do wywołania po naciśnięciu przycisku.
        """
        self.power_callback = callback

    def start_monitoring(self):
        """
        Rozpocznij monitorowanie przycisków.

        Returns:
            bool: True jeśli monitorowanie zostało uruchomione, False w przeciwnym razie.
        """
        if self.monitoring:
            return False

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_buttons)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        return True

    def _monitor_buttons(self):
        """
        Monitoruj stan przycisków.
        """
        if not self.has_gpio:
            print("Monitorowanie przycisków niedostępne bez GPIO.")
            self.monitoring = False
            return

        print("Rozpoczęto monitorowanie przycisków.")
        while self.monitoring:
            try:
                # Sprawdź przycisk nagrywania
                if self.GPIO.input(self.BUTTON_RECORD) == self.GPIO.LOW:  # Przycisk wciśnięty (LOW przy pull-up)
                    if self.record_callback:
                        self.record_callback()
                    time.sleep(0.5)  # Prosta debounce

                # Sprawdź przycisk zasilania
                if self.GPIO.input(self.BUTTON_POWER) == self.GPIO.LOW:
                    if self.power_callback:
                        self.power_callback()
                    time.sleep(0.5)  # Prosta debounce

                time.sleep(0.1)  # Zmniejszenie obciążenia CPU

            except Exception as e:
                print(f"Błąd monitorowania przycisków: {str(e)}")
                time.sleep(1)

        print("Zakończono monitorowanie przycisków.")

    def set_recording_led(self, state):
        """
        Ustaw stan diody nagrywania.

        Args:
            state (bool): Stan diody (True = włączona, False = wyłączona).
        """
        if self.has_gpio:
            try:
                self.GPIO.output(self.LED_RECORDING, self.GPIO.HIGH if state else self.GPIO.LOW)
            except Exception as e:
                print(f"Błąd ustawiania diody: {str(e)}")
        else:
            self.simulated_leds[self.LED_RECORDING] = state
            print(f"LED NAGRYWANIE: {'WŁĄCZONA' if state else 'WYŁĄCZONA'}")

    def set_thinking_led(self, state):
        """
        Ustaw stan diody myślenia.

        Args:
            state (bool): Stan diody (True = włączona, False = wyłączona).
        """
        if self.has_gpio:
            try:
                self.GPIO.output(self.LED_THINKING, self.GPIO.HIGH if state else self.GPIO.LOW)
            except Exception as e:
                print(f"Błąd ustawiania diody: {str(e)}")
        else:
            self.simulated_leds[self.LED_THINKING] = state
            print(f"LED MYŚLENIE: {'WŁĄCZONA' if state else 'WYŁĄCZONA'}")

    def blink_led(self, led_pin, duration=1, interval=0.2):
        """
        Migaj diodą przez określony czas.

        Args:
            led_pin (int): Numer pinu diody.
            duration (float): Całkowity czas migania w sekundach.
            interval (float): Interwał migania w sekundach.
        """

        def blink_thread():
            end_time = time.time() + duration
            while time.time() < end_time:
                if self.has_gpio:
                    try:
                        self.GPIO.output(led_pin, self.GPIO.HIGH)
                        time.sleep(interval)
                        self.GPIO.output(led_pin, self.GPIO.LOW)
                        time.sleep(interval)
                    except Exception as e:
                        print(f"Błąd migania diodą: {str(e)}")
                        break
                else:
                    # Symulacja migania
                    self.simulated_leds[led_pin] = True
                    print(f"LED {led_pin}: WŁĄCZONA")
                    time.sleep(interval)
                    self.simulated_leds[led_pin] = False
                    print(f"LED {led_pin}: WYŁĄCZONA")
                    time.sleep(interval)

        # Uruchom miganie w osobnym wątku
        threading.Thread(target=blink_thread, daemon=True).start()

    def cleanup(self):
        """
        Zwolnij zasoby GPIO.
        """
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(1.0)

        if self.has_gpio:
            try:
                self.GPIO.cleanup()
            except Exception as e:
                print(f"Błąd podczas czyszczenia GPIO: {str(e)}")