# Installation auf All-Inkl Webhosting

Diese Anleitung führt Sie Schritt für Schritt durch die Installation der Klasseneinteilung-Webapp auf Ihrem All-Inkl Webspace.

## Voraussetzungen

- All-Inkl Webhosting-Paket (empfohlen: PrivatPlus oder höher)
- SSH-Zugang (muss im KAS aktiviert sein)
- FTP-Zugang
- Python 3.8+ (bei All-Inkl vorinstalliert)

## Schritt 1: SSH-Zugang aktivieren

1. Melden Sie sich im **KAS** (Kunden-Administrations-System) an
2. Navigieren Sie zu **Tools** → **SSH/Shell**
3. Aktivieren Sie den SSH-Zugang
4. Notieren Sie sich die Zugangsdaten

## Schritt 2: Dateien hochladen

### Via FTP (FileZilla empfohlen)

1. Verbinden Sie sich via FTP zu Ihrem All-Inkl Server
   - Server: `ssh.all-inkl.com`
   - Port: 22 (SFTP)
   - Benutzername: Ihr KAS-Login
   - Passwort: Ihr KAS-Passwort

2. Erstellen Sie ein Verzeichnis für die App (z.B. `/klasseneinteilung`)

3. Laden Sie alle Dateien aus dem Projekt-Ordner hoch:
   - `app.py`
   - `requirements.txt`
   - `passenger_wsgi.py`
   - Ordner: `templates/`
   - Ordner: `static/`
   - `.env.example`
   - `README.md`

## Schritt 3: Via SSH verbinden

Öffnen Sie ein Terminal (Windows: PuTTY, Mac/Linux: Terminal) und verbinden Sie sich:

```bash
ssh ihr-username@ssh.all-inkl.com
```

Geben Sie Ihr Passwort ein.

## Schritt 4: Python Virtual Environment einrichten

```bash
# In Ihr Projektverzeichnis wechseln
cd klasseneinteilung

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Pip aktualisieren
pip install --upgrade pip

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Schritt 5: Konfiguration anpassen

### Secret Key generieren

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Kopieren Sie den generierten Key.

### Umgebungsvariablen setzen

```bash
# .env Datei erstellen
cp .env.example .env

# .env Datei bearbeiten
nano .env
```

Fügen Sie den generierten Secret Key ein und speichern Sie (Strg+O, Enter, Strg+X).

### passenger_wsgi.py anpassen

```bash
nano passenger_wsgi.py
```

Ändern Sie folgende Zeilen:

```python
# Ersetzen Sie dies mit Ihrem tatsächlichen Pfad:
INTERP = "/home/IHR-USERNAME/klasseneinteilung/venv/bin/python3"

# Und dies:
sys.path.insert(0, '/home/IHR-USERNAME/klasseneinteilung')
```

**Tipp**: Um Ihren vollständigen Pfad zu finden, führen Sie aus:
```bash
pwd
```

Speichern Sie die Datei (Strg+O, Enter, Strg+X).

### Berechtigungen setzen

```bash
chmod 755 passenger_wsgi.py
chmod 755 app.py
chmod 775 .
```

## Schritt 6: Datenbank initialisieren

```bash
# Python starten
python3

# In der Python-Shell:
>>> from app import init_db
>>> init_db()
>>> exit()
```

Überprüfen Sie, ob die Datenbank erstellt wurde:

```bash
ls -la klasseneinteilung.db
```

Setzen Sie die richtigen Berechtigungen:

```bash
chmod 664 klasseneinteilung.db
```

## Schritt 7: Domain/Subdomain konfigurieren

### Im KAS

1. Gehen Sie zu **Domain** → **Subdomains**
2. Erstellen Sie eine neue Subdomain (z.B. `klasseneinteilung.ihre-domain.de`)
3. Setzen Sie das Zielverzeichnis auf Ihr Projekt-Verzeichnis

### .htaccess erstellen

Erstellen Sie eine `.htaccess` Datei in Ihrem Projekt-Verzeichnis:

```bash
nano .htaccess
```

Fügen Sie folgendes ein:

```apache
# Passenger aktivieren
PassengerEnabled on
PassengerPython /home/IHR-USERNAME/klasseneinteilung/venv/bin/python3

# HTTPS erzwingen
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Sicherheit
<Files "klasseneinteilung.db">
    Order allow,deny
    Deny from all
</Files>

<Files ".env">
    Order allow,deny
    Deny from all
</Files>
```

Ersetzen Sie `IHR-USERNAME` mit Ihrem tatsächlichen Benutzernamen.

## Schritt 8: SSL/TLS aktivieren

1. Im KAS: **SSL** → **SSL-Zertifikate**
2. Aktivieren Sie Let's Encrypt für Ihre (Sub)Domain
3. Warten Sie ca. 5-10 Minuten auf die Aktivierung

## Schritt 9: Testen

1. Öffnen Sie Ihren Browser
2. Gehen Sie zu `https://klasseneinteilung.ihre-domain.de`
3. Sie sollten die Login-Seite sehen
4. Melden Sie sich mit den Standard-Zugangsdaten an:
   - Benutzername: `admin`
   - Passwort: `admin123`

## Schritt 10: Sicherheit

### WICHTIG: Admin-Passwort ändern!

1. Melden Sie sich an
2. Gehen Sie zu **Benutzer**
3. Erstellen Sie einen neuen Admin-Benutzer mit sicherem Passwort
4. Löschen Sie den Standard-Admin (optional)

### Weitere Sicherheitsmaßnahmen

```bash
# Verzeichnis-Listening deaktivieren (in .htaccess)
Options -Indexes

# Sensitive Dateien schützen
chmod 600 .env
chmod 600 klasseneinteilung.db
```

## Fehlerbehandlung

### "Internal Server Error"

Überprüfen Sie die Logs:

```bash
# All-Inkl Fehlerlog
tail -50 ~/access_log/error_log

# Oder bei neueren Setups:
tail -50 ~/logs/error.log
```

### Passenger neu starten

```bash
# Erstellen Sie eine restart.txt
touch tmp/restart.txt

# Oder:
mkdir -p tmp
touch tmp/restart.txt
```

### Datenbankfehler

```bash
# Datenbank neu initialisieren
rm klasseneinteilung.db
python3
>>> from app import init_db
>>> init_db()
>>> exit()
```

### Python-Module fehlen

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Wartung

### Backup erstellen

```bash
# Datenbank sichern
cp klasseneinteilung.db backups/klasseneinteilung_$(date +%Y%m%d_%H%M%S).db

# Regelmäßiges Backup via Cronjob (im KAS einrichten)
# Befehl: cd /home/IHR-USERNAME/klasseneinteilung && cp klasseneinteilung.db backups/db_$(date +\%Y\%m\%d).db
```

### Updates einspielen

```bash
# Backup erstellen
cp klasseneinteilung.db klasseneinteilung_backup.db

# Neue Dateien hochladen via FTP
# Passenger neu starten
touch tmp/restart.txt
```

## Support

### All-Inkl Support

- Telefon: 0261 / 50 20 40
- E-Mail: info@all-inkl.com
- FAQ: https://all-inkl.com/wichtig/anleitungen/

### Hilfreiche All-Inkl Dokumentation

- Python auf All-Inkl: https://all-inkl.com/wichtig/anleitungen/scripte-und-tools/python_allgemein/
- Passenger: https://all-inkl.com/wichtig/anleitungen/scripte-und-tools/phusion-passenger_grundlagen/
- SSH: https://all-inkl.com/wichtig/anleitungen/verbindungen/ssh-zugriff_allgemein/

## Checkliste

- [ ] SSH-Zugang aktiviert
- [ ] Dateien hochgeladen
- [ ] Virtual Environment erstellt
- [ ] Abhängigkeiten installiert
- [ ] Secret Key generiert
- [ ] passenger_wsgi.py angepasst
- [ ] Datenbank initialisiert
- [ ] .htaccess erstellt
- [ ] Subdomain konfiguriert
- [ ] SSL aktiviert
- [ ] Webapp getestet
- [ ] Admin-Passwort geändert
- [ ] Backup-Strategie eingerichtet

## Fertig!

Ihre Klasseneinteilung-Webapp ist jetzt einsatzbereit! 🎉

Bei Problemen überprüfen Sie die Logs und die Dokumentation oder kontaktieren Sie den All-Inkl Support.
