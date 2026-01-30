# Klasseneinteilung - Webapp für Schulen

Eine benutzerfreundliche Webanwendung zur automatischen Erstellung von Klasseneinteilungen für die 5. Klasse unter Berücksichtigung von Elternwünschen, Geschlechterverteilung und besonderen Bedürfnissen.

## Features

✅ **Schülerverwaltung**: Einfaches Hinzufügen und Verwalten von Schülerdaten
✅ **Elternwünsche**: Erfassung von Wünschen (z.B. "zusammen" oder "getrennt")
✅ **Intelligente Einteilung**: Automatische Generierung von 3 verschiedenen Einteilungsvorschlägen
✅ **DSGVO-konform**: Alle Daten werden lokal auf Ihrem Server gespeichert
✅ **Benutzerverwaltung**: Bis zu 10 Benutzer mit Login-System
✅ **Moderne Oberfläche**: Responsive Design für alle Geräte

## Systemanforderungen

- Python 3.8 oder höher
- SQLite (im Lieferumfang von Python enthalten)
- Webserver mit Python-Unterstützung (z.B. All-Inkl)

## Installation auf All-Inkl

### 1. Dateien hochladen

Laden Sie alle Dateien auf Ihren All-Inkl Webspace hoch:
- Verwenden Sie FTP (z.B. FileZilla)
- Laden Sie den gesamten Ordner in Ihr gewünschtes Verzeichnis

### 2. Python-Umgebung einrichten

SSH-Verbindung zu Ihrem Server herstellen und folgende Befehle ausführen:

```bash
# In Ihr Projektverzeichnis wechseln
cd /pfad/zu/klasseneinteilung-app

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### 3. Datenbank initialisieren

```bash
# Python-Shell starten
python3

# In der Python-Shell:
from app import init_db
init_db()
exit()
```

### 4. Anwendung starten

Für All-Inkl erstellen Sie eine `.htaccess`-Datei oder nutzen Sie Passenger:

**Option A: Mit Passenger (empfohlen für All-Inkl)**

Erstellen Sie eine Datei `passenger_wsgi.py`:

```python
import sys
import os

# Pfad anpassen!
INTERP = "/pfad/zu/venv/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
```

**Option B: Manueller Start (für Testzwecke)**

```bash
python3 app.py
```

Die Anwendung läuft dann auf Port 5000. Für den Produktivbetrieb sollten Sie einen WSGI-Server wie Gunicorn verwenden.

### 5. HTTPS einrichten

Stellen Sie sicher, dass Ihre Anwendung über HTTPS erreichbar ist:
- Bei All-Inkl ist SSL/TLS in der Regel bereits aktiviert
- Überprüfen Sie die SSL-Einstellungen in Ihrem KAS-Panel

## Erste Schritte

### Erster Login

1. Öffnen Sie die Webapp im Browser
2. Verwenden Sie die Standard-Zugangsdaten:
   - **Benutzername**: `admin`
   - **Passwort**: `admin123`
3. **WICHTIG**: Ändern Sie das Passwort nach dem ersten Login!

### Workflow

1. **Benutzer erstellen**: Fügen Sie weitere Benutzer hinzu (max. 10)
2. **Schüler erfassen**: Tragen Sie alle Schüler der neuen 5. Klassen ein
3. **Elternwünsche hinzufügen**: Erfassen Sie Wünsche wie "zusammen" oder "getrennt"
4. **Einteilung generieren**: Lassen Sie 3 verschiedene Vorschläge erstellen
5. **Auswählen & speichern**: Wählen Sie den besten Vorschlag aus

## Sicherheit & Datenschutz

### DSGVO-Konformität

✅ Lokale Datenspeicherung (kein Cloud-Service)
✅ Verschlüsselte Passwörter (bcrypt)
✅ Session-basierte Authentifizierung
✅ Keine Weitergabe an Dritte
✅ Datenminimierung

### Empfohlene Sicherheitsmaßnahmen

1. **Starke Passwörter**: Verwenden Sie sichere Passwörter (min. 8 Zeichen, Sonderzeichen)
2. **HTTPS**: Stellen Sie sicher, dass die Anwendung nur über HTTPS erreichbar ist
3. **Regelmäßige Backups**: Sichern Sie die Datenbank regelmäßig
4. **Zugriffsbeschränkung**: Beschränken Sie den Zugriff auf autorisierte Personen
5. **Updates**: Halten Sie Python und alle Abhängigkeiten aktuell

### Secret Key ändern

Für den Produktivbetrieb sollten Sie einen eigenen Secret Key verwenden:

```bash
# Zufälligen Secret Key generieren
python3 -c "import secrets; print(secrets.token_hex(32))"

# Als Umgebungsvariable setzen
export SECRET_KEY="ihr-generierter-key"
```

## Datensicherung

### Datenbank sichern

```bash
# Backup erstellen
cp klasseneinteilung.db klasseneinteilung_backup_$(date +%Y%m%d).db
```

### Datenbank wiederherstellen

```bash
# Backup wiederherstellen
cp klasseneinteilung_backup_YYYYMMDD.db klasseneinteilung.db
```

## Fehlerbehebung

### "Datenbank ist gesperrt"

```bash
# SQLite-Datenbank reparieren
sqlite3 klasseneinteilung.db "VACUUM;"
```

### Session-Probleme

```bash
# Flask-Cache leeren
rm -rf __pycache__
rm -rf *.pyc
```

### Berechtigungsprobleme

```bash
# Berechtigungen für Datenbank setzen
chmod 664 klasseneinteilung.db
chmod 775 .
```

## Support & Kontakt

Bei Fragen oder Problemen:
- Überprüfen Sie die Logs: `tail -f /var/log/apache2/error.log`
- Kontaktieren Sie Ihren Server-Administrator
- Dokumentation von All-Inkl: https://all-inkl.com/wichtig/anleitungen/

## Lizenz

Dieses Tool wurde für den internen Gebrauch in Schulen entwickelt.
Alle Rechte vorbehalten.

## Version

Version 1.0 - Januar 2025

---

**Hinweis**: Diese Anwendung wurde mit größter Sorgfalt entwickelt, um Datenschutz und Sicherheit zu gewährleisten. Dennoch liegt die Verantwortung für den ordnungsgemäßen Betrieb und die Einhaltung aller rechtlichen Vorgaben beim Betreiber.
