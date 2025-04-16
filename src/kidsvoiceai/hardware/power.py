# kidsvoiceai/hardware/power.py
"""
Moduł do zarządzania energią w KidsVoiceAI.
"""

import os
import time
import threading
import subprocess
import importlib.util


class PowerManager:
    """
    Klasa do zarządzania energią urządzenia.
    """

    def __init__(self, battery_gpio_pin=None):
        """
        Inicjalizacja zarządzania energią.

        Args:
            battery_gpio_pin (int, optional): Pin GPIO do monitorowania stanu baterii.
        """
        self.battery_gpio_pin = battery_gpio_pin
        self.battery_level = 100  # Domyślny poziom baterii
        self.is_charging = False
        self.low_power_mode = False
        self.critical_power = False

        # Sprawdź czy uruchomione na Raspberry Pi
        self.is_raspberry_pi = os.path.exists('/sys/firmware/devicetree/base/model')

        # Sprawdź czy mamy dostęp do GPIO
        self.has_gpio = importlib.util.find_spec("RPi.GPIO") is not None

        # Wątek monitorowania
        self.monitoring = False
        self.power_thread = None

    def start_monitoring(self):
        """
        Rozpocznij monitorowanie stanu zasilania.

        Returns:
            bool: True jeśli monitoring został uruchomiony, False w przeciwnym razie.
        """
        if self.monitoring:
            return False

        self.monitoring = True
        self.power_thread = threading.Thread(target=self._monitor_power)
        self.power_thread.daemon = True
        self.power_thread.start()
        return True

    def _monitor_power(self):
        """
        Monitoruj stan zasilania w tle.
        """
        print("Rozpoczęto monitorowanie zasilania.")

        while self.monitoring:
            try:
                # Sprawdź czy urządzenie jest podłączone do zasilania
                if self.is_raspberry_pi:
                    # Metoda 1: Sprawdź status throttlingu
                    try:
                        power_status = subprocess.check_output(['vcgencmd', 'get_throttled']).decode('utf-8')
                        self.is_charging = 'throttled=0x0' in power_status
                    except:
                        # Jeśli nie działa, spróbuj innej metody
                        self.is_charging = self._check_power_supply()
                else:
                    # Symulacja dla innych platform
                    # Tutaj możemy zasymulować rozładowywanie/ładowanie
                    pass

                # Symulacja odczytu poziomu baterii
                # W rzeczywistej aplikacji należy odczytać faktyczny poziom z ADC
                if self.is_charging and self.battery_level < 100:
                    self.battery_level += 0.5  # Wolniejsze ładowanie
                elif not self.is_charging and self.battery_level > 0:
                    self.battery_level -= 0.2  # Rozładowywanie

                # Zaokrąglenie do jednego miejsca po przecinku
                self.battery_level = round(self.battery_level, 1)

                # Ograniczenie zakresu
                if self.battery_level > 100:
                    self.battery_level = 100
                elif self.battery_level < 0:
                    self.battery_level = 0

                # Zarządzanie trybami energii
                if self.battery_level < 10:
                    if not self.critical_power:
                        print(f"OSTRZEŻENIE: Krytyczny poziom baterii: {self.battery_level}%")
                        self.critical_power = True
                        self._enter_critical_power_mode()
                elif self.battery_level < 20:
                    if not self.low_power_mode:
                        print(f"Niski poziom baterii: {self.battery_level}%")
                        self.low_power_mode = True
                        self._enter_low_power_mode()
                else:
                    if self.low_power_mode or self.critical_power:
                        self.low_power_mode = False
                        self.critical_power = False
                        self._exit_power_saving()

            except Exception as e:
                print(f"Błąd monitorowania zasilania: {str(e)}")

            # Sprawdzanie co 30 sekund
            time.sleep(30)

        print("Zakończono monitorowanie zasilania.")

    def _check_power_supply(self):
        """
        Sprawdź czy urządzenie jest podłączone do zasilania.

        Returns:
            bool: True jeśli podłączone, False w przeciwnym razie.
        """
        try:
            # Przykładowa implementacja - sprawdź napięcie na GPIO
            # W rzeczywistej aplikacji należy użyć odpowiedniego sprzętu
            if self.has_gpio and self.battery_gpio_pin is not None:
                import RPi.GPIO as GPIO
                return GPIO.input(self.battery_gpio_pin) == GPIO.HIGH

            # Alternatywnie, możemy sprawdzić napięcie systemowe
            with open('/sys/class/power_supply/BAT0/status', 'r') as f:
                status = f.read().strip()
                return status == 'Charging'

        except Exception as e:
            print(f"Błąd sprawdzania zasilania: {str(e)}")

        # Domyślnie zakładamy, że urządzenie jest podłączone
        return True

    def _enter_low_power_mode(self):
        """
        Włącz tryb oszczędzania energii.
        """
        print("Włączanie trybu oszczędzania energii")

        if self.is_raspberry_pi:
            try:
                # Zmniejszenie częstotliwości CPU
                os.system('sudo cpufreq-set -g powersave')
                # Wyłączenie HDMI
                os.system('sudo /usr/bin/tvservice -o')
            except Exception as e:
                print(f"Błąd włączania trybu oszczędzania: {str(e)}")

    def _enter_critical_power_mode(self):
        """
        Włącz tryb krytycznego oszczędzania energii.
        """
        print("UWAGA: Włączanie trybu krytycznego oszczędzania energii!")

        if self.is_raspberry_pi:
            try:
                # Maksymalne oszczędzanie energii
                os.system('sudo cpufreq-set -f 600MHz')
                # Wyłączenie wszystkich zbędnych usług
                os.system('sudo systemctl stop bluetooth.service')
                os.system('sudo systemctl stop avahi-daemon.service')
                os.system('sudo systemctl stop triggerhappy.service')
            except Exception as e:
                print(f"Błąd włączania trybu krytycznego oszczędzania: {str(e)}")

    def _exit_power_saving(self):
        """
        Wyjdź z trybu oszczędzania energii.
        """
        print("Wyłączanie trybu oszczędzania energii")

        if self.is_raspberry_pi:
            try:
                # Przywrócenie normalnych ustawień
                os.system('sudo cpufreq-set -g ondemand')
                # Włączenie HDMI (jeśli było wyłączone)
                os.system('sudo /usr/bin/tvservice -p')
                # Restart usług (jeśli były zatrzymane)
                os.system('sudo systemctl start bluetooth.service')
                os.system('sudo systemctl start avahi-daemon.service')
            except Exception as e:
                print(f"Błąd wyłączania trybu oszczędzania: {str(e)}")

    def get_status(self):
        """
        Zwróć status zasilania.

        Returns:
            dict: Słownik ze statusem zasilania.
        """
        return {
            'battery_level': int(self.battery_level),
            'is_charging': self.is_charging,
            'low_power_mode': self.low_power_mode,
            'critical_power': self.critical_power
        }

    def cleanup(self):
        """
        Zwalnianie zasobów.
        """
        self.monitoring = False
        if self.power_thread:
            self.power_thread.join(1.0)

        if self.low_power_mode or self.critical_power:
            self._exit_power_saving()

