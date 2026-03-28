#!/bin/bash
# Update-Script: Neue Version auf den Server deployen (auf dem Mac ausführen)
# Verwendung: bash deploy/3-update.sh

set -e

SERVER_IP="<DEINE-SERVER-IP>"
APP_DIR="/opt/klasseneinteilung"
ZIP_FILE="$(dirname "$0")/../klasseneinteilung-app-PORTABLE-WIN11.zip"

if [ ! -f "$ZIP_FILE" ]; then
    echo "Fehler: ZIP nicht gefunden. Bitte zuerst ZIP bauen."
    exit 1
fi

echo "==> Lade neue Version auf Server hoch..."
scp "$ZIP_FILE" "root@$SERVER_IP:/root/klasseneinteilung-app-update.zip"

echo "==> Installiere Update..."
ssh "root@$SERVER_IP" bash <<EOF
  set -e
  cd $APP_DIR

  # Neue Dateien entpacken (DB + .env bleiben erhalten)
  unzip -o /root/klasseneinteilung-app-update.zip \
    -x "*.db" -x ".env" -x "flask_session/*" -x ".initial_password"

  chown -R klasseneinteilung:klasseneinteilung $APP_DIR

  # Service neu starten
  systemctl restart klasseneinteilung

  rm /root/klasseneinteilung-app-update.zip
  echo "Update abgeschlossen."
EOF

echo ""
echo "================================================================"
echo "  Update erfolgreich!"
echo "  App: http://$SERVER_IP"
echo "================================================================"
