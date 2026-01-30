# Datenschutz und DSGVO-Konformität

## Übersicht

Die Klasseneinteilung-Webapp wurde mit höchsten Datenschutz-Standards entwickelt, um die Anforderungen der DSGVO (Datenschutz-Grundverordnung) zu erfüllen.

## Grundprinzipien

### 1. Datenminimierung (Art. 5 Abs. 1 lit. c DSGVO)

Die Webapp erfasst nur die minimal notwendigen Daten:
- Vorname und Nachname des Schülers
- Geschlecht (optional, für ausgewogene Verteilung)
- Besondere Bedürfnisse (optional, nur bei Relevanz)
- Notizen (optional, für zusätzliche Informationen)
- Elternwünsche (nur wenn vorhanden)

**KEINE Erfassung von:**
- Geburtsdatum
- Adresse
- Kontaktdaten
- Religiöse oder ethnische Informationen
- Gesundheitsdaten (außer bei explizitem Förderbedarf)

### 2. Speicherbegrenzung (Art. 5 Abs. 1 lit. e DSGVO)

- Daten werden nur für den Zeitraum der Klasseneinteilung gespeichert
- Nach Abschluss der Einteilung sollten die Daten gelöscht werden
- Empfohlene Aufbewahrungsfrist: Max. 1 Schuljahr

### 3. Vertraulichkeit und Integrität (Art. 32 DSGVO)

#### Technische Maßnahmen:
- **Verschlüsselte Übertragung**: HTTPS/TLS für alle Verbindungen
- **Passwort-Hashing**: Bcrypt-Verschlüsselung für alle Passwörter
- **Session-Management**: Sichere, zeitlich begrenzte Sessions
- **Zugriffskontrolle**: Login-System mit max. 10 autorisierten Nutzern
- **Lokale Speicherung**: Keine Cloud-Services, alle Daten auf eigenem Server

#### Organisatorische Maßnahmen:
- Klare Zuständigkeiten für Datenverwaltung
- Schulung der berechtigten Nutzer
- Dokumentation der Verarbeitungstätigkeiten

### 4. Zweckbindung (Art. 5 Abs. 1 lit. b DSGVO)

Daten werden ausschließlich für folgenden Zweck erhoben:
- Erstellung von Klasseneinteilungen für die 5. Klasse
- Berücksichtigung pädagogischer und organisatorischer Aspekte

**KEINE Verwendung für:**
- Marketing
- Weitergabe an Dritte
- Andere schulische Zwecke ohne explizite Einwilligung

## Rechtsgrundlagen

Die Verarbeitung personenbezogener Daten erfolgt auf Grundlage von:

1. **Art. 6 Abs. 1 lit. e DSGVO** - Wahrnehmung einer Aufgabe im öffentlichen Interesse
   - Klasseneinteilung als Teil des Bildungsauftrags der Schule

2. **Schulgesetze der Länder**
   - Ermächtigung zur Verarbeitung für schulorganisatorische Zwecke

## Betroffenenrechte

Eltern und Schüler haben folgende Rechte:

### 1. Auskunftsrecht (Art. 15 DSGVO)
- Recht auf Information über gespeicherte Daten
- Implementierung: Einsicht durch Schulverwaltung möglich

### 2. Recht auf Berichtigung (Art. 16 DSGVO)
- Korrektur falscher Daten möglich
- Implementierung: Bearbeiten-Funktion in der Webapp

### 3. Recht auf Löschung (Art. 17 DSGVO)
- Löschung nach Zweckerfüllung
- Implementierung: Löschen-Funktion vorhanden

### 4. Widerspruchsrecht (Art. 21 DSGVO)
- Widerspruch gegen Verarbeitung möglich
- Bei berechtigtem Widerspruch: Löschung der Daten

## Datenschutz-Folgenabschätzung

### Risikobewertung

**Geringe Risiken**, da:
- Keine sensiblen Daten (Gesundheit, Religion, etc.)
- Lokale Speicherung ohne Cloud
- Begrenzter Nutzerkreis
- Zeitlich begrenzte Verarbeitung

**Keine DSFA erforderlich**, da keine hohen Risiken für Rechte und Freiheiten der Betroffenen.

## Technische Details zur Datenspeicherung

### Datenbank: SQLite

**Vorteile für Datenschutz:**
- Datei-basiert (keine Netzwerk-Datenbank)
- Lokal auf dem Server
- Keine externe Verbindung notwendig
- Einfache Datenlöschung möglich

**Speicherort:**
```
/home/username/klasseneinteilung-app/klasseneinteilung.db
```

### Passwort-Sicherheit

- **Hashing-Algorithmus**: Werkzeug (Bcrypt)
- **Salt**: Automatisch pro Passwort
- **Keine Klartext-Speicherung** von Passwörtern

### Session-Verwaltung

- **Session-Dauer**: 2 Stunden (konfigurierbar)
- **Secure Cookies**: Nur über HTTPS
- **Session-Speicher**: Server-seitig

## Löschkonzept

### Automatische Löschung

Die Webapp bietet keine automatische Löschung. Dies muss manuell durchgeführt werden:

```sql
-- Alle Schüler löschen
DELETE FROM students;

-- Alle Elternwünsche löschen
DELETE FROM parent_wishes;

-- Alle Einteilungen löschen
DELETE FROM class_assignments;
```

### Manuelle Löschung via Webapp

1. Anmeldung als Administrator
2. Navigation zu "Schüler"
3. Einzelne Schüler löschen oder
4. Alle Daten löschen über Datenbank-Reset

### Empfohlener Löschzeitpunkt

- **Nach Schuljahresbeginn**: Wenn Klasseneinteilung final ist
- **Spätestens**: Nach einem Schuljahr
- **Alternative**: Anonymisierung der Daten

## Verzeichnis von Verarbeitungstätigkeiten

Die Schule sollte folgende Informationen dokumentieren:

### Verantwortlicher
- Name der Schule
- Kontaktdaten des Schulleiters
- Kontaktdaten des Datenschutzbeauftragten

### Zweck der Verarbeitung
- Klasseneinteilung für 5. Klassen
- Berücksichtigung pädagogischer Aspekte
- Optimale Klassengrößen

### Kategorien betroffener Personen
- Schüler der zukünftigen 5. Klassen

### Kategorien personenbezogener Daten
- Stammdaten (Name, Geschlecht)
- Pädagogische Daten (Förderbedarf)
- Elternwünsche

### Empfänger
- Nur: Schulleitung, berechtigte Lehrkräfte

### Löschfristen
- Nach Abschluss der Klasseneinteilung
- Spätestens nach 1 Schuljahr

### Technische und organisatorische Maßnahmen
- Siehe oben

## Informationspflichten

### Information der Eltern

Vor Nutzung der Webapp sollten Eltern informiert werden über:

1. Zweck der Datenerhebung
2. Rechtsgrundlage
3. Dauer der Speicherung
4. Ihre Rechte (Auskunft, Berichtigung, Löschung)
5. Beschwerderecht bei der Datenschutzbehörde

**Vorlage-Text:**

> "Sehr geehrte Eltern,
> 
> für die Klasseneinteilung der neuen 5. Klassen verwenden wir eine datenschutzfreundliche Software. 
> Wir verarbeiten nur die notwendigsten Daten (Name, Geschlecht, besondere Bedürfnisse) auf unserem 
> eigenen Server. Die Daten werden ausschließlich für die Klasseneinteilung verwendet und nach 
> Abschluss gelöscht.
> 
> Sie haben jederzeit das Recht auf Auskunft, Berichtigung oder Löschung der Daten Ihres Kindes.
> 
> Bei Fragen wenden Sie sich bitte an: [Kontaktdaten Datenschutzbeauftragter]"

## Datenpannen-Management

### Bei Sicherheitsvorfällen

1. **Vorfall dokumentieren**
2. **Schulleitung informieren**
3. **Datenschutzbeauftragten kontaktieren**
4. **Bei hohem Risiko**: Meldung an Aufsichtsbehörde (72 Stunden)
5. **Bei hohem Risiko**: Information der Betroffenen

### Mögliche Vorfälle

- Unbefugter Zugriff auf Server
- Datenverlust durch technischen Defekt
- Versehentliche Weitergabe von Daten

### Prävention

- Regelmäßige Backups
- Starke Passwörter
- Aktualisierung der Software
- Schulung der Nutzer

## Auftragsverarbeitung

### Hosting-Provider (All-Inkl)

Falls All-Inkl als Auftragsverarbeiter gilt:

1. **Vertrag zur Auftragsverarbeitung (AVV)** abschließen
2. All-Inkl bietet Standard-AVV an
3. Dokumentation der Auftragsverarbeitung

**Achtung**: Prüfen Sie, ob Ihre Schule bereits einen AVV mit All-Inkl hat.

## Checkliste DSGVO-Konformität

- [ ] Verarbeitungsverzeichnis erstellt
- [ ] Rechtsgrundlage geprüft
- [ ] Information der Eltern durchgeführt
- [ ] Technische Sicherheitsmaßnahmen implementiert
- [ ] Zugriffsrechte definiert und dokumentiert
- [ ] Löschkonzept erstellt
- [ ] AVV mit Hosting-Provider vorhanden
- [ ] Datenschutzbeauftragter informiert
- [ ] Notfallplan für Datenpannen vorhanden

## Fazit

Die Klasseneinteilung-Webapp ist mit höchsten Datenschutz-Standards entwickelt worden. Bei korrekter Anwendung und Beachtung der organisatorischen Maßnahmen ist die Webapp DSGVO-konform nutzbar.

**Wichtig**: Diese Dokumentation ersetzt keine rechtliche Beratung. Im Zweifelsfall konsultieren Sie bitte Ihren Datenschutzbeauftragten oder einen spezialisierten Rechtsanwalt.

---

Stand: Januar 2025
