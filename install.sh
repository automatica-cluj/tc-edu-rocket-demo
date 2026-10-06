#!/usr/bin/env bash
# Instalează demo-ul pe Raspberry Pi OS (Bookworm) și îl pornește automat la boot.
# Rulează ca utilizatorul obișnuit (nu cu sudo):  ./install.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="$(id -un)"
SERVICE=/etc/systemd/system/rocket-demo.service

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

echo "==> Serviciul de pornire automată"
sed -e "s|@APP_DIR@|$APP_DIR|g" -e "s|@USER@|$APP_USER|g" \
  "$APP_DIR/systemd/rocket-demo.service" | sudo tee "$SERVICE" > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable rocket-demo.service

cat <<EOF

Gata! Pași următori:
  1. Alege ieșirea audio „Headphones” (jack 3,5 mm):
       sudo raspi-config  ->  System Options -> Audio
  2. Repornește Pi-ul:  sudo reboot
  3. Verifică hardware-ul (oprește întâi serviciul):
       sudo systemctl stop rocket-demo
       $APP_DIR/.venv/bin/python -m rocket_demo --selftest
       sudo systemctl start rocket-demo
  Jurnalul aplicației:  journalctl -u rocket-demo -f
EOF
