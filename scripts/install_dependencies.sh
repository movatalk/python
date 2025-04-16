#!/bin/bash
# Instalacja zależności systemowych dla movatalk

set -e  # Zatrzymanie przy błędzie

echo "===== Instalacja zależności systemowych dla movatalk ====="

# Sprawdzenie uprawnień
if [ "$EUID" -ne 0 ]; then
  echo "Proszę uruchomić jako root (sudo)."
  exit 1
fi

# Aktualizacja systemu
echo "[1/6] Aktualizacja systemu..."
apt update && apt upgrade -y

# Instalacja podstawowych pakietów
echo "[2/6] Instalacja podstawowych pakietów..."
apt install -y git python3-pip python3-venv python3-dev \
               libportaudio2 portaudio19-dev libsndfile1 \
               ffmpeg alsa-utils cmake build-essential \
               libblas-dev liblapack-dev libatlas-base-dev

# Konfiguracja ALSA
echo "[3/6] Konfiguracja ALSA..."
if ! grep -q "pcm.!default" /etc/asound.conf 2>/dev/null; then
  cat > /etc/asound.conf << EOF
pcm.!default {
  type hw
  card 0
  device 0
}

ctl.!default {
  type hw
  card 0
}

# Buforowanie i częstotliwość próbkowania
pcm.lowlatency {
  type hw
  card 0
  device 0
  rate 16000
  format S16_LE
  channels 1
  period_size 128
  buffer_size 512
}
EOF
  echo "Utworzono konfigurację ALSA."
else
  echo "Konfiguracja ALSA już istnieje."
fi

# Konfiguracja uprawnień audio
echo "[4/6] Konfiguracja uprawnień audio..."
if ! grep -q "@audio" /etc/security/limits.d/audio.conf 2>/dev/null; then
  cat > /etc/security/limits.d/audio.conf << EOF
@audio   -  rtprio     95
@audio   -  memlock    unlimited
EOF
  echo "Skonfigurowano uprawnienia audio."
else
  echo "Uprawnienia audio już skonfigurowane."
fi

# Dodanie użytkownika do grupy audio
echo "[5/6] Dodanie użytkownika do grupy audio..."
usermod -a -G audio $SUDO_USER
echo "Użytkownik $SUDO_USER dodany do grupy audio."

# Instalacja narzędzi do zarządzania energią
echo "[6/6] Instalacja narzędzi do zarządzania energią..."
apt install -y powertop cpufrequtils

echo "===== Instalacja zależności systemowych zakończona! ====="
echo "Proszę zrestartować system przed kontynuowaniem instalacji."