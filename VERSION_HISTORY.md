# Version History - Klasseneinteilung App

**Author:** Tobias Meier <admin(at)secutobs.com>
**Project:** Klasseneinteilung App - Intelligente Klasseneinteilung für 5. Klassen
**Repository:** klasseneinteilung-app

---

## Version 0.1.62 - Klickbare Wohnorte in gespeicherter Einteilung
**Release Date:** 19. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neues Feature (Wunsch Schulleitungsteam)
- **Wohnort-Chips anklickbar:** In der gespeicherten Einteilung kann man in der „📍 Wohnorte"-Liste einer Klasse auf einen Ort klicken — die Schüler aus diesem Ort werden hervorgehoben (gelb), die übrigen ausgegraut. Erneuter Klick hebt die Markierung auf. Hilft beim manuellen Verschieben. Funktioniert auch im Bearbeitungsmodus.
- Technisch: neuer Jinja-Filter `extract_city`, `data-city` je Schüler, JS `toggleCityHighlight()`.

---

## Version 0.1.61 - Bugfix: Wohnort-/Religions-Anzeige nach Verschieben
**Release Date:** 19. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Bugfix
- **Nach Drag-&-Drop-Verschiebung + Speichern** wurden die Wohnort-/Städte-Zähler (und auch die Religions-Zähler) einer Klasse nicht neu berechnet → die „Wohnorte"-Anzeige zeigte veraltete Werte. `update_assignment` berechnet jetzt `city_count`, `wohnort_count` und `religion_count` aus der neuen Klassenzusammensetzung neu (Geschlecht/Schulform/IB/Sport/Inklusion waren bereits korrekt).
- Verifiziert: Verschieben eines Schülers korrigiert die Städte-Zähler exakt (z.B. „60438 Frankfurt am Main" 7 → 6).

---

## Version 0.1.60 - Alphabetische Listen + Klassennamen änderbar
**Release Date:** 19. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neue Features (Wünsche Schulleitungsteam)
- **Alphabetische Sortierung:** Schüler werden in jeder Klasse nach Nachname, Vorname sortiert — in der Vorschau, der gespeicherten Ansicht und allen Exporten (Excel/CSV/PDF). (Exporte sortierten schon vorher; jetzt auch die Bildschirm-Ansicht.)
- **Klassennamen änderbar:** In einer gespeicherten Einteilung können die Klassen umbenannt werden (Button „Klassen umbenennen" → Panel mit einem Feld je Klasse). Standardnamen bleiben 5a, 5b, 5c … Die Namen werden gespeichert und in alle Exporte sowie den Vergleich übernommen. Neue Route `/assignments/<id>/rename`.

### Technisch
- Jede Klasse hat jetzt ein editierbares Feld `name` (Default „5a"…). Exporte nutzen `_class_label()` mit Fallback für ältere Einteilungen. Excel-Sheet-Titel werden auf gültige Zeichen/Länge bereinigt.

---

## Version 0.1.59 - Wunsch-Zuordnung bei mehreren Nachnamen
**Release Date:** 19. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserung (Hinweis Schulleitungsteam)
- **Freundschaftswünsche werden jetzt auch bei mehreren Nachnamen zugeordnet.** Bisher musste der komplette Nachname im Wunsch stehen; bei Doppelnamen (z.B. Schüler „Yilmaz Güney Küpeli") oder wenn im Wunsch nur ein Teil des Nachnamens stand, schlug die Zuordnung fehl.
- Neue Regel: Ein Schüler passt, wenn **mindestens ein Vorname- UND mindestens ein Nachname-Token** übereinstimmen (vorher: ganzer Nachname). Ranking: exakte Übereinstimmung > mehr passende Nachname-Tokens > größere Gesamt-Überlappung. Mehrdeutige Treffer werden weiterhin nicht geraten, sondern gemeldet.
- Deckt jetzt mehrere Vornamen UND mehrere Nachnamen sowie beliebige Reihenfolge ab.

### Verifiziert
- Synthetische Doppelnamen-Tests 8/8 korrekt. An echter (vom Team bereinigter) Datei: 241 Wünsche verknüpft, nur 2 nicht gefunden, 0 mehrdeutig, keine Falsch-Treffer in der Stichprobe (u.a. „Yilmaz Küpeli"→„Yilmaz Güney Küpeli", „Jannik Lauerer"→„Jannik Tobias Louis Lauerer").

---

## Version 0.1.58 - Sport-Zwang vs. Trennungswunsch + IB-Sport-Fix
**Release Date:** 19. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Bugfixes (Sport-Schüler landeten in Normalklassen)
Aufgefallen am Fall "Angelo Piccininni" (Sport-Häkchen, aber in Normalklasse). Zwei Ursachen:
- **Trennungswunsch überstimmte den Sportklassen-Zwang:** Hatte ein Sport-Schüler einen "Auf keinen Fall mit"-Wunsch gegen Schüler, die beide Sportklassen belegten, drückte der Trennungswunsch (−5000) ihn in eine Normalklasse. Jetzt ist der Sportklassen-Zwang (−8000 für Sport-Schüler in Normalklasse) stärker als der Trennungswunsch, aber schwächer als die Klassengrößen-Sperre (−10000) → kein Überlauf. Der Trennungswunsch wird weiterhin INNERHALB der Sportklassen bestmöglich beachtet.
- **IB-Vorverteilung ignorierte Sport:** IB-Schüler mit Sport-Häkchen wurden teils in Normalklassen vorverteilt. Jetzt werden IB-Sport-Schüler über die normale Platzierung in Sportklassen gebracht; die IB-Vorverteilung legt Nicht-Sport-IB ausschließlich in Nicht-Sport-Klassen. Ohne konfigurierte Sportklassen bleibt die IB-Vorverteilung unverändert (keine Einzelkämpfer).

### Verifiziert
- Echte Datei (45 Sport-Häkchen, 6 IB): 12 Läufe (3 Konfigurationen × 4 Seeds) → 0 Verletzungen der Sport-Invariante; Angelo, Elias und Mustafa korrekt in Sportklassen.

---

## Version 0.1.57 - Wunsch-Garantie + neue Prioritäten (Schulleitung)
**Release Date:** 19. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Änderungen nach Feedback des Schulleitungsteams
- **Mindestens ein Freundschaftswunsch garantiert:** Der Optimierer bewertet jetzt primär die *coverage* (Anzahl Schüler mit ≥1 erfülltem Zusammen-Wunsch, ×1000 gewichtet), erst dann die Gesamtzahl. Jeder Schüler mit Wunsch bekommt zuerst einen erfüllt, weitere Wünsche danach — soweit harte Regeln es zulassen. An echter Datei: Coverage ~100 % (ohne Sportklassen).
- **Neue Prioritäten-Reihenfolge der Verteilung:** 1 garantierter Wunsch → Schulweg/Wohnort → Religion → Schulform → Geschlecht. Konkret: Religion-Gewicht 2→12, Schulform 8 (unverändert), Geschlecht 15→4, Zusammen-Wunsch 150→200.
- Optimierer-Runden 60→250 und korrekte Kapazitätsprüfung pro Klasse (`effective_max`, berücksichtigt Sport-/IB-Sonderlimits).

### Hinweis
- Wünsche zwischen einem Sport- und einem Nicht-Sport-Kind sind strukturell nicht erfüllbar (verschiedene Klassentypen).

---

## Version 0.1.56 - Wunsch-Zuordnung bei mehreren Vornamen
**Release Date:** 18. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserung
- **Freundschaftswünsche werden jetzt auch bei mehreren Vornamen zugeordnet.** Bisher klappte die Zuordnung nur bei exakt „ein Vorname + ein Nachname"; bei Schülern mit zwei/drei Vornamen (z.B. „Anna Maria Müller") oder abweichender Reihenfolge schlug sie fehl.
- Neues Matching: Anker ist der **Nachname** (muss vollständig vorkommen) plus **mindestens ein übereinstimmender Vorname**; Reihenfolge egal, Bindestrich-Namen werden zerlegt.
- **Mehrdeutige Namen** (mehrere gleich gut passende Schüler) werden nicht mehr falsch geraten, sondern als Warnung zur manuellen Zuordnung gemeldet.
- An echter Schul-Datei: verknüpfte Wünsche von 86 → **147** gestiegen.

---

## Version 0.1.55 - Sportklassen-Rückfrage: sinnvolle kompakte Option
**Release Date:** 18. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Bugfix
- **Kompakte Option in der Rückfrage war an die Eingabe gekoppelt** und konnte absurde Größen vorschlagen (z.B. bei Wahl „1 Sportklasse" → „57 Schüler in 1 Klasse"). Jetzt berechnet die App die kompakte Alternative unabhängig von der Eingabe: möglichst wenige Sportklassen, aber höchstens `SPORT_OVERSIZE_MAX` (30) Schüler pro Klasse. Für 57 Schüler → „2 Sportklassen (28–29)" statt „1 Sportklasse (57)".
- Die Rückfrage wird nur noch angezeigt, wenn es tatsächlich eine sinnvollere kompakte Alternative gibt; sonst werden direkt genug Sportklassen geöffnet.

---

## Version 0.1.54 - Sportklassen-Größe wählbar (25er-Grenze)
**Release Date:** 18. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neues Feature
- **25er-Grenze für Sportklassen überschreitbar:** Reicht die gewählte Anzahl Sportklassen nicht, gibt es jetzt zwei Wege statt nur „weitere Klasse öffnen":
  - **Checkbox** „Max. 25 Schüler/Sportklasse darf überschritten werden" im Generieren-Formular. Aktiviert → bei der gewählten Anzahl bleiben, Schüler gleichmäßig verteilen (z.B. 57 → 28/29 in 2 Klassen).
  - **Interaktive Rückfrage-Seite**, wenn die Checkbox nicht gesetzt ist und ein Konflikt auftritt: zeigt konkrete Zahlen und zwei Buttons (weitere Sportklasse öffnen / 25er-Grenze überschreiten).
- Sportklassen können jetzt ein eigenes, höheres Maximum haben (`sport_class_max`), während Normalklassen weiterhin bei 25 bleiben.
- Garantie aus 0.1.53 bleibt: in Sportklassen nur Häkchen-Schüler, kein Häkchen-Schüler in Normalklasse.

### Verifiziert
- Echte Schul-Datei (57 Häkchen): Oversize 2 Klassen → 28/29, Auto-Open → 3×≤25; alle 3 Wege (Checkbox/Rückfrage „öffnen"/Rückfrage „überschreiten") end-to-end getestet, 0 Invarianten-Verletzungen.

---

## Version 0.1.53 - Sportklassen-Kapazität (kritischer Fix)
**Release Date:** 18. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Kritischer Bugfix
- **Sportklassen-Überlauf behoben:** Reichte die gewählte Anzahl Sportklassen nicht für alle Schüler mit Sportklassen-Häkchen, landeten die überzähligen Häkchen-Schüler bisher in Normalklassen. Jetzt öffnet die App automatisch so viele Sportklassen, dass ALLE Häkchen-Schüler hineinpassen (max. 25/Klasse), und erhöht bei Bedarf die Gesamt-Klassenzahl. Ein Info-Hinweis informiert über die automatische Anpassung.
- **Garantie:** In Sportklassen sind ausschließlich Schüler mit Häkchen; kein Häkchen-Schüler landet in einer Normalklasse. An echter Schul-Datei verifiziert (57 Häkchen-Schüler, 1 gewählte Sportklasse → 3 automatisch geöffnet, 0 Verletzungen über alle 3 Vorschläge).
- Die Kapazitätsprüfung läuft jetzt bei GET und POST (vorher nur GET, und nur für Normalklassen).

---

## Version 0.1.52 - Import-Verbesserungen (Religion & Sportklasse)
**Release Date:** 18. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Import-Fixes (nach Abgleich echter Schul-Exportdatei)
- **Religion:** Import bevorzugt jetzt die Spalte "Religionsunterricht" (Ethik/Ev/Kath) statt "Religion" (Konfession). Bei leerem Religionsunterricht wird auf die Konfession zurückgegriffen. Deutlich korrektere Religionsverteilung für die Einteilung.
- **Konfession:** Die Spalte "Religion"/"Konfession" wird – wenn eine separate "Religionsunterricht"-Spalte existiert – zusätzlich als Info in den Notizen festgehalten (z.B. "Konfession: …").
- **Sportklasse:** Erkennung toleriert jetzt "X" mit Kommentar (z.B. "X Sportattest liegt vor") sowie das ausgeschriebene Wort "Sportklasse". Vorher wurde nur exakt "X" erkannt → an einer Realdatei stieg die Trefferzahl von 37 auf 57.

### Hinweis
- Unklare/leere Werte in der "Eignung"-Spalte (Schulform) müssen weiterhin in der Quelldatei bereinigt werden – das kann der Import nicht erraten.

---

## Version 0.1.51 - Security-Audit & Härtung
**Release Date:** 10. Juni 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Security-Fixes (aus Penetration-Test / Audit)
- **Authorization:** `/admin/update` (GET) war für jeden eingeloggten Nutzer erreichbar (`@login_required`) → jetzt `@admin_required`. Verhinderte Info-Disclosure von Versions-/Backup-Status für Nicht-Admins.
- **Robustheit:** Nicht-numerische Eingaben in `/generate` (`num_classes`, `ib_min`, `ib_max`, `specialized_*_count`, `ib_class_size`) lösten einen ungefangenen 500-Fehler aus → neuer `safe_int()`-Helper fängt ungültige Werte ab.
- **Timing-Angriff:** Token-Vergleich im KI-Proxy `/api/ki-config` nutzt jetzt `secrets.compare_digest()` statt `!=`.
- **Zip-Slip:** Auto-Updater prüft nun, dass extrahierte Pfade innerhalb des App-Verzeichnisses bleiben (Defense-in-Depth gegen Pfad-Traversal beim Update).

### Verifiziert
- Live-Pentest bestätigt: CSRF-Schutz, Auth-Gating, Admin-Autorisierung, Datenisolation, Security-Header, kein SQLi/XSS.

---

## Version 0.1.31 - Schüler-Info per Klick
**Release Date:** 20. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neues Feature
- **Schüler-Info Modal:** Klick auf einen Schüler in der Klassen-Übersicht zeigt ein Info-Fenster mit Name, Geschlecht, Schulform, Wohnort, Religion, Sportklasse, IKL, Förderbedarf und Notizen — ohne etwas zu verändern
- Verfügbar in gespeicherten Einteilungen (Ansehen) sowie in der Vorschau beim Generieren
- Im Bearbeitungsmodus bleibt das Klicken für Drag & Drop reserviert

---

## Version 0.1.30 - Bugfix Einteilung-Bearbeiten + Sportklasse-Logik
**Release Date:** 20. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Bugfixes
- **KRITISCH: Einteilung bearbeiten → Änderungen speichern** gab "Interner Server Error" — `import json` fehlte in `update_assignment`-Route

### Sportklasse-Logik
- **Import:** Spalte "Sportklasse" setzt nur noch `sport_interesse` (nicht mehr `sportlich`) — einziges Kriterium für Sportklassen-Zuteilung
- **Import:** Spalte "Sportattest" wird explizit ignoriert — hat keinen Einfluss auf Sportklasse
- **Formular:** Checkboxen "Besonders sportlich" und "Interesse an Sportklasse" aus Schüler-Formularen entfernt — Sportklasse-Zuordnung nur noch über Excel-Import möglich
- **IB-Sperre:** IB-Schüler ohne Sportklasse-Hacken bleiben hart gesperrt (−5000)

---

## Version 0.1.29 - Auto-Restart Fix (Delay vor SIGHUP)
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Bugfix
- **Auto-Restart:** SIGHUP wird jetzt mit 2 Sekunden Verzögerung in einem Background-Thread gesendet, damit die HTTP-Antwort zuerst zum Browser zurückgesendet wird bevor gunicorn die Worker neu startet

---

## Version 0.1.28 - Auto-Restart nach Update + Berechtigungs-Fix
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserungen
- **Auto-Restart:** Nach erfolgreichem Update wird gunicorn automatisch via SIGHUP neu geladen (kein manueller Neustart mehr nötig auf dem Server)
- **Portable App:** Fallback-Hinweis für PORTABLE-START.bat bleibt erhalten wenn SIGHUP nicht verfügbar

---

## Version 0.1.27 - Update-Seite für alle Benutzer sichtbar
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserungen
- **Update-Seite:** Alle eingeloggten Benutzer können die Update-Seite öffnen und prüfen ob eine neue Version verfügbar ist
- **Install/Rollback:** Weiterhin nur für Admin sichtbar und ausführbar

---

## Version 0.1.26 - Security Hardening
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Sicherheits-Verbesserungen
- **Debug-Modus deaktiviert:** `debug=True` → nur noch aktiv wenn `FLASK_ENV=development` gesetzt ist (verhindert Werkzeug-Debugger im Produktivbetrieb)
- **Security-Header:** Alle HTTP-Antworten enthalten jetzt `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy`
- **Version-Endpoint geschützt:** `/version` erfordert jetzt Login
- **GitHub-Versionsstring validiert:** Format wird auf `x.y.z` geprüft bevor er verarbeitet wird
- **Rate-Limiting auf Update-Routen:** `apply_update` und `rollback_update` auf max. 5 Aufrufe/Stunde begrenzt
- **SQL-Query bereinigt:** Unnötiger f-String in DELETE-Query entfernt, stattdessen saubere Parametrisierung

---

## Version 0.1.25 - Breitere Darstellung (max-width 1600px)
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserungen
- **Layout:** `max-width` des Haupt-Containers von 1120px auf 1600px erhöht — die App nutzt jetzt die volle Breite auf großen Monitoren.

---

## Version 0.1.24 - In-App Update-System
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neues Feature
- **In-App Update-System (Admin):** Unter "Update" in der Navbar kann der Admin prüfen ob eine neuere Version auf GitHub (monstertobs/klasseneinteilung-app) verfügbar ist.
  - Zeigt Versionsvergleich und Änderungsnotizen der neuen Version
  - "Update installieren" lädt die neue Version von GitHub und überschreibt App-Dateien (DB und .env bleiben erhalten)
  - Automatischer Rollback bei Fehler im Update-Prozess
  - Manueller Rollback-Button wenn Backup vorhanden
  - Neustart-Hinweis nach Update/Rollback

---

## Version 0.1.23 - Einteilungen editierbar, Wünsche-Hinweis, harte Trennsperre
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neue Features
- **Einteilungen bearbeiten:** Gespeicherte Einteilungen können per Drag & Drop geändert werden ("Bearbeiten"-Button). Änderungen werden mit "Änderungen speichern" in die DB zurückgeschrieben.
- **Kein-Wünsche-Hinweis:** Wenn keine Elternwünsche erfasst sind, erscheint auf der Generieren-Seite ein gelber Warnhinweis mit Link zu Wünsche-Erfassung.

### Bugfixes / Verbesserungen
- **Trennungswünsche ("Auf keinen Fall mit"):** Strafe von −500 auf −5000 erhöht → quasi harte Sperre. Schüler werden praktisch nie mehr zusammen eingeteilt wenn ein Trennungswunsch besteht.

---

## Version 0.1.22 - Neue Schüler zu bestehender Einteilung hinzufügen
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Neues Feature
- **Basis-Einteilung:** Beim Generieren kann eine gespeicherte Einteilung als Basis gewählt werden. Bestehende Schüler bleiben in ihrer Klasse — nur neue Schüler (nicht in der Basis) werden durch den Algorithmus verteilt.
- Gepinnte Schüler werden durch die Wunsch-Optimierung nicht bewegt.
- UI: Dropdown auf der Generieren-Seite erscheint wenn gespeicherte Einteilungen vorhanden sind.

---

## Version 0.1.21 - Sportklasse: nur mit Hacken, IB ausgeschlossen
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserungen
- **Import:** "Sportklasse"-Spalte setzt jetzt auch `sport_interesse=1` (bisher nur `sportlich`), damit der Algorithmus Schüler korrekt der Sportklasse zuordnet
- **Algorithmus:** IB-Schüler ohne Sportklassen-Hacken können nicht mehr in die Sportklasse kommen (harte Sperre −5000)
- **Algorithmus:** IB-Vorverteilung überspringt jetzt Sportklassen-Indizes für IB-Schüler ohne Hacken
- **Algorithmus:** Nicht-IB-Schüler ohne Hacken werden stark von der Sportklasse ferngehalten (−200 statt −20)
- **Ausnahme:** IB-Schüler MIT Sportklassen-Hacken können weiterhin in die Sportklasse

---

## Version 0.1.20 - Eignung hat Vorrang vor Elternwunsch
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### Verbesserungen
- **Import:** Wenn "Eignung"=R oder H, bleibt die Schulform dabei — auch wenn Elternwunsch (z.B. in "Infos Übergabe" oder einer anderen Schulform-Spalte) Gymnasium angibt. Warnung wird im Import-Log angezeigt.

---

## Version 0.1.19 - Religion Fallback auf Ethik
**Release Date:** 19. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### 🐛 Bugfixes / Verbesserungen
- **Import:** Nicht erkannte Religionswerte werden jetzt automatisch auf "Ethik" gesetzt (statt Warnung + falscher Wert). Nur "katholisch" und "evangelisch" (inkl. Varianten) bleiben erhalten.

---

## Version 0.1.18 - Bugfix: Flask-Login in Portable Setup
**Release Date:** 12. April 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### 🐛 Bugfixes
- **CRITICAL:** `Flask-Login==0.6.3` fehlte im `pip install`-Befehl in `PORTABLE-SETUP-WIN11.bat` → App startete auf Windows nicht (ModuleNotFoundError)

---

## Version 2.1.0 - Algorithm & Transparency Release
**Release Date:** February 21, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### 🎉 Major Features Added

#### **1. Transparency Page (Transparenzseite)**
- New page showing exactly why each student was assigned to their class
- Color-coded badges per reason: fulfilled/failed wishes, school route, school type, gender balance, IB, special needs
- Filter by class tab and full-text search
- Accessible from both proposal preview and saved assignment view
- **New Routes:** `/generate/transparency/<idx>`, `/assignments/<id>/transparency`
- **New File:** `templates/transparency.html`
- **New Functions:** `compute_transparency()`, `find_student_in_classes()`

#### **2. Algorithm Optimization — 90%+ Wish Fulfillment**
- **Post-processing swap optimizer** (`optimize_assignment_wishes()`): iteratively swaps same-gender students between classes until no further improvement is possible (up to 60 rounds)
- **Smart initial ordering**: students most-wished-for by others are placed first, so classmates can follow them
- **Bidirectional wish checking**: if student A wishes to be with B, this now also scores positively when placing B
- **Increased wish weights**: together +150 (was +20), separated -500 (was -20)
- **Result**: wish fulfillment rate improved from ~57% to 90–93%
- **Files:** `app.py` (+120 lines)

#### **3. Parent Wishes Import Fix**
- Fixed critical bug: Excel import silently failed to create wishes due to wrong DB column names (`notes`/`created_by` → `description`)
- Wishes from "Freund/Freundin" and "Auf keinen Fall mit Kind..." columns now reliably imported
- **Files:** `app.py`

### 🔧 Technical Improvements

- **CSS:** Added `.badge-secondary` and `.badge-dark` classes for transparency badges
- **Statistics recomputed** after swap optimization to ensure correct display
- **Files:** `static/css/style.css`, `templates/generate.html`, `templates/view_assignment.html`

### 📊 Statistics

- **Files Created:** 1 (`transparency.html`)
- **Files Modified:** 4
- **Lines Added:** ~200
- **New Routes:** 2
- **Bug Fixes:** 1 (critical import bug)

### 🐛 Bug Fixes

- Fixed: Parent wishes from Excel import not being saved (wrong column name `notes` → `description`)

---

## Version 2.0.0 - Feature Extension Release
**Release Date:** February 13, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### 🎉 Major Features Added

This release adds 6 major features to enhance the class assignment system with advanced options, interactive preview, and conflict resolution.

#### **1. Export Function (Excel, CSV, PDF)**
- Multi-format export for class lists
- Excel: Multi-sheet workbook with statistics
- CSV: Semicolon-delimited, UTF-8 encoded
- PDF: Professional layout with ReportLab
- **Files:** `app.py` (+200 lines), `generate.html` (+30 lines)
- **Dependencies:** Added `reportlab==4.0.9`

#### **2. Multiple Specialized Classes**
- Support for Sport, Musik, and Theater classes
- Student interest tracking with checkboxes
- Algorithm prioritizes students for matching classes
- Visual badges (⚽🎵🎭) on class headers
- **Database:** Added columns `sport_interesse`, `musik_interesse`, `theater_interesse`
- **Files:** `app.py` (+150 lines), `add_student.html`, `edit_student.html`, `generate.html`

#### **3. Religion Bundling**
- Prevents pure Ethik-only classes
- Promotes religious diversity
- Intelligent scoring for mixed religion classes
- **Files:** `app.py` (+30 lines), `generate.html` (+10 lines)

#### **4. IB Min/Max Constraints**
- Configurable minimum and maximum IB students per class
- Pre-generation validation and warnings
- Classes have either 0 or between min-max IB students
- **Files:** `app.py` (+50 lines), `generate.html` (+20 lines)

#### **5. Drag & Drop Student Movements**
- Interactive preview mode for class adjustments
- Visual feedback with grab cursor and animations
- Real-time statistics updates
- Modification tracking without database changes
- **New File:** `static/js/drag-drop.js` (433 lines)
- **Files Modified:** `generate.html` (+40 lines), `style.css` (+80 lines)

#### **6. Conflict Detection & Resolution**
- Automatic conflict detection when moving students
- Modal dialog with severity levels
- Solution suggestions with scoring
- Three action options: Revert, Accept, or View Suggestions
- **New Routes:** `/check_conflicts`, `/suggest_swaps`
- **Files:** `app.py` (+120 lines), `drag-drop.js`, `style.css` (+70 lines)

### 🔧 Technical Improvements

- **Password Hashing:** Switched from scrypt to pbkdf2:sha256 for better compatibility
- **Error Handling:** Improved error handling in init_db()
- **Code Quality:** 1,200+ lines of well-documented code added
- **Performance:** Optimized DOM manipulation in drag & drop
- **Security:** CSRF protection on all AJAX calls

### 📊 Statistics

- **Files Created:** 2 (drag-drop.js, VERSION_HISTORY.md)
- **Files Modified:** 7
- **Lines Added:** ~1,200
- **New Routes:** 3
- **New Database Columns:** 3
- **Dependencies Added:** 1 (reportlab)

### 🐛 Bug Fixes

- Fixed scrypt unavailability on some Python installations
- Improved session handling for drag & drop state
- Fixed sorting of students after drag & drop operations

### 📝 Documentation

- Added `IMPLEMENTATION_SUMMARY.md`
- Added `VERSION_HISTORY.md`
- Updated inline code documentation
- Added comprehensive testing documentation

---

## Version 1.0.0 - Initial Release
**Release Date:** January 30, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable (Superseded by v2.0.0)

### 🎯 Core Features

#### **Class Generation Algorithm**
- Intelligent distribution of students across classes (~25 students per class)
- Multi-factor scoring system
- Three proposal variants with different random seeds

#### **Scoring Priorities**
1. **Gender Balance** (Highest Priority)
   - Target: 50/50 distribution
   - Score penalty: -15 per gender ratio deviation
2. **School Route Grouping**
   - Groups students from same area (Wohnort)
   - Enables carpooling
   - Score bonus: +12 per matching location
3. **Friend Wishes**
   - Together wishes: +20 bonus
   - Separation wishes: -20 penalty
4. **School Type Distribution** (Schulform)
   - Balanced distribution of H/R/G/IB
   - Score penalty: -8 per ratio deviation
5. **Religion Distribution** (Secondary)
   - Optional distribution or grouping
   - Score impact: ±2 points

#### **Student Management**
- Add, edit, delete students
- Import from CSV/Excel
- Duplicate detection
- Fields: Name, Gender, Wohnort, Schulform, Religion, Special Needs, Notes

#### **Parent Wishes Management**
- Together wishes (students want to be in same class)
- Separation wishes (students should be in different classes)
- Automatic import from CSV/Excel

#### **Security Features**
- CSRF Protection (Flask-WTF)
- Rate Limiting (Flask-Limiter: 10 login attempts/minute)
- Session Security (HttpOnly, SameSite, Secure cookies)
- Strong Password Requirements (8+ chars, upper, lower, digit)
- Custom Error Handlers (404, 500, 429)

#### **User Management**
- Multi-user support (max 10 users)
- Role-based access (login required)
- Password strength validation
- Session timeout (2 hours)

#### **Database Schema**
- SQLite database
- Tables: users, students, parent_wishes, class_assignments
- Automatic migrations on startup

#### **UI/UX**
- Apple-inspired design system
- Responsive layout
- German language UI
- Print-friendly views
- Flash message system

### 📊 Statistics

- **Files Created:** 23
- **Lines of Code:** ~1,330 (app.py)
- **Templates:** 16 (Jinja2)
- **Routes:** 18 endpoints
- **Database Tables:** 4

---

## Version 0.5.0 - Beta Release
**Release Date:** January 15, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ⚠️ Beta (Superseded)

### Features

- Basic class generation algorithm
- Student CRUD operations
- CSV import functionality
- Simple login system
- Basic dashboard

### Known Issues

- No parent wishes support
- Limited import flexibility
- No security features
- Single user only

---

## Version 0.1.0 - Alpha Release
**Release Date:** January 1, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ⚠️ Alpha (Superseded)

### Features

- Proof of concept
- Random class distribution
- Basic student list
- No database persistence

---

## Roadmap

### Version 2.2.0 (Planned)
- [ ] Advanced conflict resolution strategies
- [ ] Batch import improvements
- [ ] Export customization options
- [ ] Performance optimizations for large datasets

### Version 2.3.0 (Planned)
- [ ] Teacher assignment integration
- [ ] Room allocation
- [ ] Timetable integration
- [ ] Advanced reporting
- [ ] Multi-language support

### Version 3.0.0 (Future)
- [ ] API for external integrations
- [ ] Real-time collaboration
- [ ] Advanced analytics
- [ ] Machine learning optimization
- [ ] Mobile app

---

## Upgrade Guide

### From v1.0.0 to v2.0.0

**Database Migration:**
- Automatic migration runs on startup
- New columns added: `sport_interesse`, `musik_interesse`, `theater_interesse`
- No manual intervention required
- Existing data preserved

**Dependencies:**
```bash
pip install -r requirements.txt  # Installs reportlab==4.0.9
```

**Configuration:**
- No configuration changes required
- All new features are optional
- Backward compatible with v1.0 usage

**Breaking Changes:**
- None - fully backward compatible

---

## Support & Contact

**Author:** Tobias Meier
**Email:** admin(at)secutobs.com
**Project:** Klasseneinteilung App

For issues, questions, or feature requests, please contact the author.

---

## License

**Copyright © 2026 Tobias Meier**
All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

**Last Updated:** 19. April 2026
**Current Version:** 0.1.31
**Maintained By:** Tobias Meier <admin(at)secutobs.com>
