#!/usr/bin/env python3
"""
WSGI-Konfiguration für Passenger (All-Inkl)

Anleitung:
1. Passen Sie den INTERP-Pfad an Ihre virtuelle Umgebung an
2. Passen Sie sys.path.insert an Ihren Projektpfad an
3. Stellen Sie sicher, dass die Dateirechte korrekt sind (chmod 755)
"""

import sys
import os

# WICHTIG: Passen Sie diesen Pfad an Ihre virtuelle Umgebung an!
# Beispiel: /home/username/klasseneinteilung-app/venv/bin/python3
INTERP = "/pfad/zu/ihrem/venv/bin/python3"

# Python-Interpreter wechseln, falls nötig
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# WICHTIG: Passen Sie diesen Pfad an Ihr Projektverzeichnis an!
# Beispiel: /home/username/klasseneinteilung-app
sys.path.insert(0, '/pfad/zu/ihrem/projektverzeichnis')

# Umgebungsvariablen setzen (optional)
os.environ['FLASK_ENV'] = 'production'

# Datenbank initialisieren, falls noch nicht vorhanden
from app import init_db
import os
if not os.path.exists('klasseneinteilung.db'):
    init_db()

# Flask-App importieren
from app import app as application

# Für Passenger ist 'application' der Entry Point
# Kein app.run() notwendig!
