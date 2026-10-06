#!/usr/bin/env bash
# Instalează demo-ul pe Raspberry Pi OS (Lite sau cu desktop; Pi 3B+, 4 sau 5) și îl pornește automat la boot.
# Rulează ca utilizatorul obișnuit (nu cu sudo):  ./install.sh
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then
  echo "Rulează scriptul ca utilizatorul obișnuit, fără sudo:  ./install.sh"
  exit 1
fi

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="$(id -un)"
OLD_SERVICE=/etc/systemd/system/rocket-demo.service
UNIT_DIR="$HOME/.config/systemd/user"

echo "==> Pachete de sistem"
sudo apt-get update
sudo apt-get install -y \
  python3-venv python3-pip python3-gpiozero python3-lgpio python3-pygame \
  python3-flask python3-smbus2 i2c-tools alsa-utils

echo "==> Activez I2C (pentru LCD)"
sudo raspi-config nonint do_i2c 0

echo "==> Mediu Python"
python3 -m venv --system-site-packages "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet RPLCD

echo "==> Sunete provizorii"
"$APP_DIR/.venv/bin/python" "$APP_DIR/tools/make_placeholder_sounds.py"

echo "==> Serviciul de pornire automată (serviciu de utilizator)"
if [ -f "$OLD_SERVICE" ]; then
  # versiunile vechi foloseau un serviciu de sistem
  sudo systemctl disable --now rocket-demo.service || true
  sudo rm -f "$OLD_SERVICE"
  sudo systemctl daemon-reload
fi
mkdir -p "$UNIT_DIR"
sed -e "s|@APP_DIR@|$APP_DIR|g" "$APP_DIR/systemd/rocket-demo.service" > "$UNIT_DIR/rocket-demo.service"
sudo loginctl enable-linger "$APP_USER"  # pornește serviciile utilizatorului la boot
systemctl --user daemon-reload
systemctl --user enable rocket-demo.service

cat <<EOF

Gata! Pași următori:
  1. Alege ieșirea audio: „Headphones” (jack 3,5 mm, Pi 3/4) sau placa de sunet USB (Pi 5):
       sudo raspi-config  ->  System Options -> Audio
  2. Repornește Pi-ul:  sudo reboot
  3. Verifică hardware-ul (oprește întâi serviciul):
       systemctl --user stop rocket-demo
       $APP_DIR/.venv/bin/python -m rocket_demo --selftest
       systemctl --user start rocket-demo
  Jurnalul aplicației:  journalctl --user-unit rocket-demo -f
  Pagina pe un monitor legat la Pi (Pi 4/5):  $APP_DIR/kiosk/setup-kiosk.sh
EOF
