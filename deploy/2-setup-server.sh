#!/bin/bash
# Schritt 2: Server einrichten (auf dem Hetzner-Server als root ausführen)
# Installiert: Python 3, Gunicorn, Nginx, App-Dateien, Systemd-Service

set -e

APP_DIR="/opt/klasseneinteilung"
APP_USER="klasseneinteilung"

echo ""
echo "================================================================"
echo "  Klasseneinteilung - Server Setup"
echo "  Ubuntu 24.04 | Nginx + Gunicorn | Kein SSL (nur IP)"
echo "================================================================"
echo ""

# 1. System aktualisieren
echo "[1/7] System aktualisieren..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx unzip

# 2. App-Benutzer anlegen
echo "[2/7] App-Benutzer anlegen..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false "$APP_USER"
fi

# 3. App-Verzeichnis einrichten
echo "[3/7] App-Dateien installieren..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"
unzip -o /root/klasseneinteilung-app.zip
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# 4. Python-Umgebung und Abhängigkeiten
echo "[4/7] Python-Umgebung einrichten..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
"$APP_DIR/venv/bin/pip" install --quiet gunicorn

# 5. .env erstellen
echo "[5/7] Konfiguration erstellen..."
if [ ! -f "$APP_DIR/.env" ]; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$SECRET
FLASK_DEBUG=False
DATABASE_PATH=$APP_DIR/klasseneinteilung.db
SESSION_LIFETIME=2
MAX_USERS=10
MAX_STUDENTS=250
EOF
    chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
fi

mkdir -p "$APP_DIR/flask_session"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR/flask_session"

# 6. Systemd-Service einrichten
echo "[6/7] Systemd-Service einrichten..."
cat > /etc/systemd/system/klasseneinteilung.service <<EOF
[Unit]
Description=Klasseneinteilung App
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5050 --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable klasseneinteilung
systemctl restart klasseneinteilung

# 7. Nginx einrichten
echo "[7/7] Nginx einrichten..."
cat > /etc/nginx/sites-available/klasseneinteilung <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }
}
EOF

ln -sf /etc/nginx/sites-available/klasseneinteilung /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Datenbank initialisieren und Passwort anzeigen
echo ""
echo "================================================================"
echo "  Datenbank initialisieren..."
echo "================================================================"
cd "$APP_DIR"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" -c "from app import init_db; init_db()"

echo ""
echo "================================================================"
echo "  SETUP ABGESCHLOSSEN!"
echo "================================================================"
echo ""
echo "  App erreichbar unter: http://$(curl -s ifconfig.me)"
echo ""
echo "  Login: admin"
echo "  Passwort: siehe OBEN (einmalig angezeigt)"
echo ""
echo "  Passwort-Datei: $APP_DIR/.initial_password"
echo "  (wird nach erstem Login automatisch geloescht)"
echo ""
echo "  Service-Befehle:"
echo "    systemctl status klasseneinteilung"
echo "    systemctl restart klasseneinteilung"
echo "    journalctl -u klasseneinteilung -f"
echo "================================================================"
