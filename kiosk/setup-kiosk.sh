#!/usr/bin/env bash
# Pornește automat pagina demo-ului pe tot ecranul, pe monitorul legat la Pi (HDMI).
# Recomandat pe Raspberry Pi 4 sau 5 (Raspberry Pi OS Lite sau cu desktop). Rulează după install.sh:
#   ./kiosk/setup-kiosk.sh            activează
#   ./kiosk/setup-kiosk.sh --remove   dezactivează (revine la desktop sau la consola de login)
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="$HOME/.profile"
BEGIN="# >>> rocket-demo kiosk >>>"
END="# <<< rocket-demo kiosk <<<"

remove_block() {
  if [ -f "$PROFILE" ]; then
    sed -i "/^$BEGIN\$/,/^$END\$/d" "$PROFILE"
  fi
}

if [ "${1:-}" = "--remove" ]; then
  remove_block
  if [ -x /usr/sbin/lightdm ]; then
    sudo raspi-config nonint do_boot_behaviour B4  # desktop cu login automat
    echo "Kiosk dezactivat. După repornire pornește din nou desktopul."
  else
    sudo raspi-config nonint do_boot_behaviour B1
    echo "Kiosk dezactivat. După repornire apare din nou consola de login."
  fi
  exit 0
fi

echo "==> Instalez cage (afișare pe tot ecranul) și Chromium"
sudo apt-get update
sudo apt-get install -y --no-install-recommends cage curl fonts-dejavu-core
sudo apt-get install -y --no-install-recommends chromium \
  || sudo apt-get install -y --no-install-recommends chromium-browser

echo "==> Login automat în consolă (desktopul, dacă există, nu mai pornește)"
sudo raspi-config nonint do_boot_behaviour B2

echo "==> Pagina pornește automat la login pe ecranul principal (tty1)"
chmod +x "$APP_DIR/kiosk/start-kiosk.sh"
remove_block
cat >> "$PROFILE" <<EOF
$BEGIN
if [ -z "\${WAYLAND_DISPLAY:-}" ] && [ "\$(tty)" = "/dev/tty1" ]; then
    exec "$APP_DIR/kiosk/start-kiosk.sh"
fi
$END
EOF

cat <<EOF

Gata! Leagă monitorul la portul HDMI 0 (cel de lângă USB-C) și repornește: sudo reboot
  - Consolă de login: Ctrl+Alt+F2 (înapoi la pagină: Ctrl+Alt+F1).
  - Dezactivare: $APP_DIR/kiosk/setup-kiosk.sh --remove
EOF
