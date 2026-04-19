# Klasseneinteilung App

**Intelligente Klasseneinteilung für 5. Klassen**

![Version](https://img.shields.io/badge/version-0.1.29-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Flask](https://img.shields.io/badge/flask-3.x-lightgrey)
![License](https://img.shields.io/badge/lizenz-MIT-brightgreen)

Eine DSGVO-konforme Flask-Webanwendung zur automatisierten Erstellung von Klasseneinteilungen für 5. Klassen. Berücksichtigt Elternwünsche, Geschlechterbalance, Schulweg, Schulform, Religion, Förderbedarf und sportliche Eignung.

---

## Features

- **Automatische Klasseneinteilung** — intelligenter Algorithmus generiert 3 Vorschläge zur Auswahl
- **Elternwünsche** — "zusammen" und "getrennt"-Wünsche werden gewichtet berücksichtigt
- **IB/VM-Schüler** — deterministisch vorverteilt, nie allein in einer Klasse
- **Drag & Drop** — Schüler manuell zwischen Klassen verschieben im Vorschau-Modus
- **Transparenz-Ansicht** — zeigt für jeden Schüler, warum er in welche Klasse kam
- **Import** — CSV/Excel-Import mit schulspezifischen Spaltenformaten
- **Export** — Excel, CSV und PDF je Klasse
- **Mehrbenutzer** — Admin + weitere Nutzer mit eigenem Passwort
- **Portable** — läuft auch auf Windows 11 ohne Admin-Rechte (Embedded Python)

---

## Schnellstart

```bash
# 1. Abhängigkeiten installieren (Python 3.10+ erforderlich)
pip3 install -r requirements.txt

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env bearbeiten: SECRET_KEY eintragen
# Schlüssel generieren: python3 -c "import secrets; print(secrets.token_hex(32))"

# 3. App starten
python3 app.py
# → http://localhost:5050
# Das initiale Admin-Passwort wird einmalig in der Konsole angezeigt
```

---

## Deployment (Linux/Systemd)

Die App läuft produktiv als systemd-Service. Voraussetzungen:

- Python 3.10+
- SQLite (kein extra Datenbankserver nötig)
- `passenger_wsgi.py` als WSGI-Einstiegspunkt (z.B. für All-Inkl Shared Hosting)

---

## Konfiguration

Alle Einstellungen über `.env` (Vorlage: `.env.example`):

| Variable | Standard | Beschreibung |
|---|---|---|
| `SECRET_KEY` | — | **Pflicht.** Flask-Session-Schlüssel |
| `DATABASE_PATH` | `klasseneinteilung.db` | Pfad zur SQLite-Datenbank |
| `SESSION_LIFETIME` | `2` | Session-Dauer in Stunden |
| `MAX_USERS` | `10` | Maximale Benutzeranzahl |
| `MAX_STUDENTS` | `250` | Maximale Schüleranzahl |
| `FLASK_DEBUG` | `False` | Debug-Modus (nur Entwicklung) |

---

## Berücksichtigte Kriterien

| Kriterium | Gewichtung |
|---|---|
| Elternwunsch (zusammen) | +150 |
| Elternwunsch (getrennt) | −500 |
| Geschlechterbalance | −15 pro Abweichung |
| Schulform-Verteilung | −8 pro Abweichung |
| Stadtgruppierung (Schulweg) | +20 |
| PLZ-Gruppierung | +10 |
| Religion | −2 pro Abweichung |
| Klassengrößenbalance | −10 pro Abweichung |
| IB-Klasse voll | −1000 |
| Klasse voll | −10000 |

---

## Projektstruktur

```
klasseneinteilung-app/
├── app.py                  # Flask-App, Algorithmus, alle Routen (~2600 Zeilen)
├── templates/              # 23 Jinja2-Templates
├── static/
│   ├── css/style.css       # Apple-inspiriertes responsives Design
│   └── js/drag-drop.js     # Drag & Drop für Vorschau-Modus
├── passenger_wsgi.py       # WSGI-Einstiegspunkt
├── requirements.txt
└── .env.example
```

---

## Portable Windows 11 Paket

Für Windows-Umgebungen ohne Admin-Rechte (z.B. Schulserver):

1. `PORTABLE-SETUP-WIN11.bat` ausführen — lädt Python 3.11 Embedded + Abhängigkeiten herunter
2. `PORTABLE-START.bat` zum Starten der App

---

## Datenschutz / DSGVO

- Alle Schülerdaten bleiben lokal (SQLite, kein Cloud-Dienst)
- Keine Daten werden an Dritte übermittelt
- Passwörter werden mit PBKDF2-SHA256 gehasht
- Sessions sind serverseitig gespeichert

Siehe [DATENSCHUTZ.md](DATENSCHUTZ.md) für Details.

---

## Autor

**Tobias Meier** — [admin(at)secutobs.com](mailto:admin(at)secutobs.com)

---

## Lizenz

MIT License — siehe [LICENSE](LICENSE) für Details.
