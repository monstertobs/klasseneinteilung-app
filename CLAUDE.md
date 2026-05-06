# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **security-hardened**, DSGVO-compliant Flask web application for generating school class divisions (5th grade). Considers parent wishes, gender balance, school routes (wohnort), school type (schulform), religion, special needs, and athletic ability. Designed for deployment on All-Inkl shared hosting with local SQLite storage.

**Current version:** 0.1.41 (6. Mai 2026)

**Production:** Hetzner VPS, app path `/opt/klasseneinteilung/`, systemd service `klasseneinteilung`. Deploy via paramiko (password auth); `sshpass` not available on macOS.

## Versioning

- Schema: MAJOR.MINOR.PATCH — increment PATCH on every change, MINOR for new features
- **Always update version + date when making any code change**, in all of:
  - `app.py` (header comment `Version:` + `__version__`)
  - `templates/base.html`
  - `templates/about.html` (3 occurrences + Release Datum)
  - `PORTABLE-WIN11-PAKET-INFO.txt` (version + date)
  - `START-HIER.txt`
  - `CLAUDE.md` (this file, header line above)

## Development Commands

```bash
# Install dependencies (Python 3.10+ required)
pip3 install -r requirements.txt

# Run development server at http://localhost:5050
# Initial admin password is randomly generated and printed ONCE to console on first run
python3 app.py

# Initialize/reset database (runs automatically on startup too)
python3 -c "from app import init_db; init_db()"

# Generate test data (100-150 students, 20-40 wishes) — CLI version
echo "ja" | python3 generate_testdata.py

# Generate Excel test file (100 students, IB/VM/Förderbedarf/Elternwünsche)
python3 create_testdata_excel.py  # saves testdaten_schueler_import.xlsx

# Reset admin password directly in DB (when .initial_password is already deleted)
python3 -c "
from werkzeug.security import generate_password_hash; import sqlite3
db = sqlite3.connect('klasseneinteilung.db')
db.execute('UPDATE users SET password_hash=? WHERE username=?',
           (generate_password_hash('Admin1234', method='pbkdf2:sha256'), 'admin'))
db.commit()
"

# Deploy to production (requires: pip3 install paramiko)
python3 - <<'EOF'
import paramiko
ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<SERVER-IP>', username='root', password='<PASS>', timeout=15)
sftp = ssh.open_sftp()
for f in ['app.py', 'templates/generate.html', 'templates/students.html',
          'templates/base.html', 'templates/about.html']:
    sftp.put(f, f'/opt/klasseneinteilung/{f}')
sftp.close()
ssh.exec_command('systemctl restart klasseneinteilung')
ssh.close()
EOF
```

**Note:** Port 5000 is occupied by macOS AirPlay. App always runs on **5050**.

There is no test suite, linter, or build step.

## Portable WIN11 Package

`klasseneinteilung-app-PORTABLE-WIN11.zip` — for restricted Windows 11 Enterprise environments (no admin rights). Setup downloads Python 3.11.8 Embedded + dependencies. Entry point: `PORTABLE-SETUP-WIN11.bat`.

Rebuild after every code change:
```bash
rm -f klasseneinteilung-app-PORTABLE-WIN11.zip && \
zip -r klasseneinteilung-app-PORTABLE-WIN11.zip \
  app.py requirements.txt .env.example passenger_wsgi.py \
  PORTABLE-SETUP-WIN11.bat PORTABLE-START.bat \
  START-HIER.txt PORTABLE-ANLEITUNG-WIN11.txt PORTABLE-WIN11-PAKET-INFO.txt INSTALLATION-VORSCHAU.txt \
  VERSION_HISTORY.md templates/ static/ \
  -x "*.pyc" -x "__pycache__/*" -x "*.db" -x "flask_session/*" -x "*.zip" -x ".initial_password"
```

### Windows Batch Files — Critical Requirements

All `.bat` files MUST use:
1. **`%~dp0` for all paths** — never use `cd /d "%~dp0"` (CMD is locked on school PCs). Store as `set "APP_DIR=%~dp0"` and prefix all paths with `%APP_DIR%`
2. **CRLF line endings** — convert with `sed 's/$/\r/' file.bat > tmp && mv tmp file.bat`
3. **ASCII-only** — no Unicode, no emojis, no umlauts (ä→ae, ö→oe, ü→ue, ß→ss)

Verify: `file filename.bat` → must show "DOS batch file text, ASCII text, with CRLF line terminators"

## Architecture

Single-file Flask app (`app.py`, ~2600 lines):

- **app.py** — All routes, DB schema, class division algorithm, auth, security, Excel/CSV/PDF export
- **templates/** — 23 Jinja2 templates extending `base.html`
- **static/css/style.css** — Apple-inspired responsive design
- **static/js/drag-drop.js** — Drag & drop for moving students between classes in preview mode
- **passenger_wsgi.py** — WSGI entry point for All-Inkl production hosting
- **flask_session/** — Filesystem session storage (auto-created; required for proposals >4KB)

### Routes

**Student management:** `/students`, `/students/add`, `/students/edit/<id>`, `/students/delete/<id>`, `/students/delete_multiple`, `/students/delete_all`, `/students/import`, `/students/duplicates`, `/students/generate_testdata` (POST), `/students/delete_testdata` (POST)

**Parent wishes:** `/wishes`, `/wishes/add`, `/wishes/edit/<id>`, `/wishes/delete/<id>`

**Class division:**
- `GET/POST /generate` — Generate 3 class proposals (stored in `session['last_proposals']`)
- `GET /generate/transparency/<int:proposal_idx>` — Transparency view for a proposal
- `GET /assignments/<id>` — View saved assignment
- `POST /save_assignment` — Save selected proposal to DB
- `POST /assignments/<id>/delete` — Delete a saved assignment
- `POST /export/<format>` and `POST /assignments/<id>/export/<format>` — Excel/CSV/PDF
- `/check_conflicts`, `/suggest_swaps` — Conflict detection for drag & drop

**Users (admin only):** `/users`, `/users/add`, `/users/delete/<id>` — protected by `admin_required` decorator; `/users/change-password` — for all logged-in users

**Other:** `/dashboard`, `/algorithm`, `/about`, `/wizard/*`

### Database (SQLite)

Four tables: `users`, `students`, `parent_wishes`, `class_assignments`. Parameterized SQL throughout. `class_assignments.data` stores JSON.

**Student fields:** `firstname`, `lastname`, `gender` (m/w), `wohnort`, `schulform` (H/R/G/IB), `religion` (ethik/katholisch/evangelisch/leer), `sportlich` (0/1), `sport_interesse` (0/1), `special_needs`, `notes`, `import_batch_id`

Schema migrations use `ALTER TABLE ... ADD COLUMN` wrapped in try/except. `init_db()` runs on every startup.

### Authentication & Security

- Session-based, PBKDF2-SHA256 password hashing (Werkzeug)
- `SECRET_KEY` **must** be set in `.env` — app refuses to start without it
- Initial `admin` password: randomly generated (16 chars), printed to console **and** written to `.initial_password` on first DB init. Displayed on login page until first successful login, then deleted automatically.
- **Admin role:** `session['is_admin']` is set to `True` when `username == 'admin'`. Use `admin_required` decorator (defined after `login_required`) for admin-only routes. Non-admin users cannot see the "Benutzer" navbar link.
- CSRF tokens required in all forms
- Rate limiting: 10 login attempts/minute, 200/day global
- Every user can change their own password via `/users/change-password`

### Class Division Algorithm

**Core functions:**
- `generate_class_assignment(students, wishes, num_classes, seed, options)` — generates one proposal
- `find_best_class(student, classes, ..., options, ...)` — scores each class for a student
- `optimize_assignment_wishes(classes, wish_dict, max_rounds=60, options=None)` — post-processing swaps to maximize wish fulfillment. Accepts `options` to enforce IB constraints during swaps.
- `compute_transparency(proposal, wishes)` — enriches each student dict with `reasons` list

**IB student placement (pre-assignment):**
Before the main placement loop, IB students are deterministically pre-assigned to classes in groups using round-robin. This guarantees no single IB student ends up alone:
```python
num_ib_classes = min(num_classes, num_ib // ib_min)
# round-robin: student[idx] → class[idx % num_ib_classes]
```
`optimize_assignment_wishes` checks `ib_move_allowed()` before any swap involving an IB student.

**Scoring weights (highest to lowest priority):**
1. Hard limit full class: −10000
2. Freundewünsche: +150 together / −500 separated (bidirectional via `reverse_wish_dict`)
3. Geschlechterbalance: −15 per gender ratio concentration
4. Stadt-Gruppierung: +20 per student from same city
5. PLZ-Gruppierung: +10 per student from same postal code
6. Schulform-Verteilung: −8 per ratio concentration
7. Religion: −2 per ratio concentration
8. Size balance: −10 per size deviation from average
9. IB max hard block: −1000 (normal IB placement handled by pre-assignment above)
10. Sport-Spezialklasse: +50 / −20 depending on sport_interesse

**Smart initial ordering:** Students most-wished-for by others are placed first. IB students are extracted and pre-assigned before this ordering runs.

**`options` dict keys:** `gender_balance`, `schulweg_gruppe`, `parent_wishes`, `schulform_balance`, `religion_distribute`/`religion_group`/`religion_bundle`, `specialized_classes`, `ib_min`/`ib_max`, `sportklasse` (deprecated)

### Import Functionality

`process_import_data(data, batch_id)` handles CSV/Excel with extensive column mapping.

**School-specific columns:** `SLR_WohnAdresse` → wohnort, `Eignung` → schulform, `IB / VM - s.Liste` → schulform='IB' (if contains "IB") or appended to notes as "VM: …" (if contains "VM"), `Wahlfach Religion` → religion, `Sportklasse` → sportlich+sport_interesse, `Freund/Freundin` → 'together' wishes, `Auf keine Fall mit Kind…` → 'separated' wishes

**Important:** `parent_wishes` INSERT uses column `description` (not `notes`). The table has no `created_by` column.

### Testdata Generator (Web UI)

`POST /students/generate_testdata` — generates fictional students directly into the DB. Form params: `anzahl` (10–300), `with_ib`, `with_vm`, `with_foerder`, `with_wishes` (all checkboxes, value `"1"`). Students are tagged with `import_batch_id = "TESTDATA-<timestamp>"` so they are visually marked as "Importiert" and can be bulk-deleted via `POST /students/delete_testdata`.

The `🧪 Testdaten` button and modal live in `templates/students.html`. VM students get `notes = "VM: Vorbeugende Maßnahme"` (not a special DB field).

### Proposal Comparison (generate route)

After generating 3 proposals, the `generate` route computes per-proposal metrics and stores them in `proposal['statistics']`:
- `wish_rate` (int 0–100 or None), `wish_fulfilled`, `wish_total`
- `gender_balance_score` (int 0–100, stddev-based)
- `student_class_map` (dict `{student_id: class_number}`) — used by JS in `generate.html` to compute cross-proposal student differences

`generate.html` renders a comparison panel above the proposals (`.comparison-panel`) and marks students that differ across proposals with CSS class `.student-differs` (yellow highlight + `↕` indicator).

### Key Templates

- `generate.html` — 3 proposals with drag & drop, comparison panel, per-proposal wish rate badge, student diff highlighting, Transparenz + Export buttons
- `transparency.html` — Color-coded reason badges; JS class-filter tabs + text search
- `change_password.html` — Password change form with show/hide toggle (eye button) per field
- `students.html` — Testdaten modal (inline `<style>` + `<script>`, no external files)

### CSS Badge Classes (`static/css/style.css`)

`.badge-success`, `.badge-danger`, `.badge-info`, `.badge-warning`, `.badge-dark`, `.badge-secondary`

## Configuration

`.env` variables: `SECRET_KEY` (required), `FLASK_ENV`, `FLASK_DEBUG`, `DATABASE_PATH` (default: `klasseneinteilung.db`), `SESSION_LIFETIME` (default: 2h), `MAX_USERS` (default: 10), `MAX_STUDENTS`

## Language

All UI text is German. Python identifiers and DB columns are English.

## Export Formats

- **Excel:** openpyxl, one sheet per class, color-coded headers
- **CSV:** semicolon-delimited, UTF-8, all classes in one file
- **PDF:** ReportLab/Helvetica, text normalization for special chars (ä→ae etc.)
