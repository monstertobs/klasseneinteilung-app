#!/bin/bash
# SSL einrichten mit Let's Encrypt (auf dem Server als root ausführen)

set -e

DOMAIN="klassenwahl.de"
APP_DIR="/opt/klasseneinteilung"

echo "==> Installiere Certbot..."
apt-get install -y -qq certbot python3-certbot-nginx

echo "==> Nginx für Domain konfigurieren..."
cat > /etc/nginx/sites-available/klasseneinteilung <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

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

nginx -t && systemctl reload nginx

echo "==> SSL-Zertifikat anfordern..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN \
    --non-interactive --agree-tos \
    --email admin@secutobs.com \
    --redirect

echo ""
echo "================================================================"
echo "  HTTPS eingerichtet!"
echo ""
echo "  App erreichbar unter:"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo ""
echo "  Zertifikat wird automatisch erneuert."
echo "================================================================"
