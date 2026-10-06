#!/usr/bin/env bash
# Afișează pagina demo-ului pe tot ecranul monitorului legat la Pi (HDMI).
# Pornit automat la login pe tty1 (vezi kiosk/setup-kiosk.sh); nu rula cu sudo.
set -u

URL="${ROCKET_URL:-http://127.0.0.1:8000/?kiosk=1}"
BASE="${URL%%\?*}"
BROWSER="$(command -v chromium || command -v chromium-browser || true)"

if [ -z "$BROWSER" ] || ! command -v cage > /dev/null; then
  echo "Lipsesc cage sau chromium. Rulează: kiosk/setup-kiosk.sh"
  sleep 30
  exit 1
fi

echo "Aștept pagina demo-ului la $BASE ..."
for _ in $(seq 1 120); do
  curl -sf -o /dev/null "${BASE%/}/api/state" && break
  sleep 1
done

# -s: permite Ctrl+Alt+F2 pentru o consolă de login
cage -s -- "$BROWSER" \
  --kiosk --incognito --noerrdialogs --disable-infobars --no-first-run \
  --disable-session-crashed-bubble --disable-features=Translate \
  --overscroll-history-navigation=0 --password-store=basic \
  --ozone-platform=wayland "$URL"

# Dacă browserul se închide, login-ul automat îl repornește după câteva secunde.
sleep 3
