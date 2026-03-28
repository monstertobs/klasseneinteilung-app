#!/bin/bash
# Schritt 1: App auf den Hetzner-Server hochladen (auf dem Mac ausführen)
# Verwendung: ./deploy/1-upload.sh <SERVER-IP>
# Beispiel:   ./deploy/1-upload.sh 65.21.100.200

set -e

SERVER_IP=$1
if [ -z "$SERVER_IP" ]; then
    echo "Fehler: Server-IP fehlt."
    echo "Verwendung: $0 <SERVER-IP>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ZIP_FILE="$SCRIPT_DIR/klasseneinteilung-app-PORTABLE-WIN11.zip"

if [ ! -f "$ZIP_FILE" ]; then
    echo "Fehler: ZIP nicht gefunden: $ZIP_FILE"
    echo "Bitte zuerst ZIP bauen."
    exit 1
fi

echo "==> Lade ZIP auf Server $SERVER_IP hoch..."
scp "$ZIP_FILE" "root@$SERVER_IP:/root/klasseneinteilung-app.zip"

echo "==> Lade Setup-Script hoch..."
scp "$SCRIPT_DIR/deploy/2-setup-server.sh" "root@$SERVER_IP:/root/setup-server.sh"
ssh "root@$SERVER_IP" "chmod +x /root/setup-server.sh"

echo ""
echo "================================================================"
echo "Upload abgeschlossen!"
echo ""
echo "Jetzt auf dem Server ausführen:"
echo "  ssh root@$SERVER_IP"
echo "  bash /root/setup-server.sh"
echo "================================================================"
