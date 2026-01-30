# Schnellstart-Anleitung

Diese Kurzanleitung hilft Ihnen, die Klasseneinteilung-Webapp schnell zum Laufen zu bringen.

## Für Entwicklung / Lokales Testen

### 1. Voraussetzungen prüfen

```bash
# Python-Version prüfen (min. 3.8)
python3 --version

# Pip prüfen
pip3 --version
```

### 2. Installation

```bash
# Repository herunterladen oder entpacken
cd klasseneinteilung-app

# Abhängigkeiten installieren
pip3 install -r requirements.txt
```

### 3. Starten

```bash
# Anwendung starten
python3 app.py
```

Die Webapp läuft nun auf: `http://localhost:5000`

### 4. Anmelden

- Benutzername: `admin`
- Passwort: `admin123`

⚠️ **Wichtig**: Ändern Sie das Passwort nach dem ersten Login!

## Für Produktion (All-Inkl)

### Schnell-Installation

```bash
# 1. Via FTP alle Dateien hochladen

# 2. Via SSH verbinden und ausführen:
cd /pfad/zu/klasseneinteilung-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Datenbank initialisieren
python3
>>> from app import init_db
>>> init_db()
>>> exit()

# 4. passenger_wsgi.py anpassen (Pfade!)
nano passenger_wsgi.py

# 5. .htaccess erstellen (siehe INSTALLATION.md)

# 6. Fertig! Webapp über Domain aufrufen
```

**Detaillierte Anleitung**: Siehe [INSTALLATION.md](INSTALLATION.md)

## Testdaten generieren (optional)

Für erste Tests können Sie Beispieldaten generieren:

```bash
python3 generate_testdata.py
```

Dies erstellt:
- 100-150 Test-Schüler
- 20-40 Test-Elternwünsche
- Einen Test-Benutzer (testuser / test123)

⚠️ **Nur für Tests verwenden! Vor Produktiveinsatz löschen!**

## Basis-Workflow

### 1. Benutzer verwalten
- Navigation: **Benutzer** → **Benutzer hinzufügen**
- Weitere Lehrkräfte/Admins anlegen

### 2. Schüler erfassen
- Navigation: **Schüler** → **Schüler hinzufügen**
- Alle Schüler der neuen 5. Klassen eintragen

### 3. Elternwünsche hinzufügen
- Navigation: **Elternwünsche** → **Wunsch hinzufügen**
- "Zusammen" oder "Getrennt"-Wünsche erfassen

### 4. Einteilung generieren
- Navigation: **Einteilung generieren**
- System erstellt 3 verschiedene Vorschläge
- Besten Vorschlag auswählen

### 5. Fertig!
- Einteilung exportieren/drucken
- Nach Verwendung: Daten löschen (DSGVO!)

## Häufige Probleme

### "Internal Server Error"

**Lösung 1**: Logs prüfen
```bash
tail -50 ~/access_log/error_log
```

**Lösung 2**: Passenger neu starten
```bash
mkdir -p tmp
touch tmp/restart.txt
```

### "Datenbank gesperrt"

**Lösung**: Berechtigungen setzen
```bash
chmod 664 klasseneinteilung.db
chmod 775 .
```

### Login funktioniert nicht

**Lösung**: Datenbank neu initialisieren
```bash
python3
>>> from app import init_db
>>> init_db()
>>> exit()
```

## Wichtige Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app.py` | Haupt-Anwendung |
| `requirements.txt` | Python-Abhängigkeiten |
| `passenger_wsgi.py` | WSGI-Konfiguration für All-Inkl |
| `klasseneinteilung.db` | SQLite-Datenbank |
| `.env` | Umgebungsvariablen (erstellen!) |
| `.htaccess` | Apache-Konfiguration (erstellen!) |

## Nützliche Befehle

```bash
# Datenbank-Backup
cp klasseneinteilung.db backup_$(date +%Y%m%d).db

# Alle Schüler löschen (VORSICHT!)
sqlite3 klasseneinteilung.db "DELETE FROM students;"

# Alle Daten löschen (VORSICHT!)
rm klasseneinteilung.db
python3 -c "from app import init_db; init_db()"

# Logs anzeigen (All-Inkl)
tail -f ~/access_log/error_log

# Passenger neu starten
touch tmp/restart.txt
```

## Sicherheits-Checkliste

- [ ] Admin-Passwort geändert
- [ ] Secret Key geändert (.env)
- [ ] HTTPS aktiviert
- [ ] Datenbank-Berechtigungen gesetzt
- [ ] Testdaten gelöscht
- [ ] Backup-Strategie eingerichtet

## Support

- **Technische Fragen**: Siehe [README.md](README.md)
- **Installation**: Siehe [INSTALLATION.md](INSTALLATION.md)  
- **Datenschutz**: Siehe [DATENSCHUTZ.md](DATENSCHUTZ.md)
- **All-Inkl Support**: info@all-inkl.com

## Weitere Ressourcen

- [Vollständige Dokumentation](README.md)
- [Installations-Anleitung](INSTALLATION.md)
- [DSGVO-Informationen](DATENSCHUTZ.md)

---

**Viel Erfolg mit der Klasseneinteilung!** 🎉
