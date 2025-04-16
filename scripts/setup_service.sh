#!/bin/bash
# Konfiguracja usługi systemd dla KidsVoiceAI

set -e  # Zatrzymanie przy błędzie

echo "===== Konfiguracja usługi systemd dla KidsVoiceAI ====="

# Sprawdzenie uprawnień
if [ "$EUID" -ne 0 ]; then
  echo "Proszę uruchomić jako root (sudo)."
  exit 1
fi

# Ścieżka do zainstalowanego pakietu
KIDSVOICEAI_PATH=$(pip3 show kidsvoiceai | grep "Location" | awk '{print $2}')
if [ -z "$KIDSVOICEAI_PATH" ]; then
  echo "Błąd: Nie znaleziono pakietu kidsvoiceai. Czy został zainstalowany?"
  exit 1
fi

# Utworzenie usługi systemd
echo "Tworzenie usługi systemd..."
cat > /etc/systemd/system/kidsvoiceai.service << EOF
[Unit]
Description=KidsVoiceAI - Bezpieczny interfejs głosowy AI dla dzieci
After=network.target

[Service]
ExecStart=/usr/bin/python3 -m kidsvoiceai
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
systemctl enable kidsvoiceai.service

echo "===== Konfiguracja usługi zakończona! ====="
echo "Aby uruchomić usługę: sudo systemctl start kidsvoiceai"
echo "Aby sprawdzić status: sudo systemctl status kidsvoiceai"
echo "Aby zatrzymać usługę: sudo systemctl stop kidsvoiceai"