# Version History - Klasseneinteilung App

**Author:** Tobias Meier <admin(at)secutobs.com>
**Project:** Klasseneinteilung App - Intelligente Klasseneinteilung für 5. Klassen
**Repository:** klasseneinteilung-app

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
**Current Version:** 0.1.29
**Maintained By:** Tobias Meier <admin(at)secutobs.com>
