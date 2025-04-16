#!/bin/bash
# Konfiguracja usługi systemd dla movatalk

set -e  # Zatrzymanie przy błędzie

echo "===== Konfiguracja usługi systemd dla movatalk ====="

# Sprawdzenie uprawnień
if [ "$EUID" -ne 0 ]; then
  echo "Proszę uruchomić jako root (sudo)."
  exit 1
fi

# Ścieżka do zainstalowanego pakietu
movatalk_PATH=$(pip3 show movatalk | grep "Location" | awk '{print $2}')
if [ -z "$movatalk_PATH" ]; then
  echo "Błąd: Nie znaleziono pakietu movatalk. Czy został zainstalowany?"
  exit 1
fi

# Utworzenie usługi systemd
echo "Tworzenie usługi systemd..."
cat > /etc/systemd/system/movatalk.service << EOF
[Unit]
Description=movatalk - Bezpieczny interfejs głosowy AI dla dzieci
After=network.target

[Service]
ExecStart=/usr/bin/python3 -m movatalk
WorkingDirectory=/home/$SUDO_USER
StandardOutput=journal
StandardError=journal
Restart=always
User=$SUDO_USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Aktywacja usługi
echo "Aktywacja usługi..."
systemctl daemon-reload
systemctl enable movatalk.service

echo "===== Konfiguracja usługi zakończona! ====="
echo "Aby uruchomić usługę: sudo systemctl start movatalk"
echo "Aby sprawdzić status: sudo systemctl status movatalk"
echo "Aby zatrzymać usługę: sudo systemctl stop movatalk"