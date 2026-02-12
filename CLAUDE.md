# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **security-hardened**, DSGVO-compliant Flask web application for generating school class divisions (5th grade). Considers parent wishes, gender balance, school routes (wohnort), school type classification (schulform), religion, special needs (inclusive education), and athletic ability to produce optimized class assignments. Designed for deployment on All-Inkl shared hosting with local SQLite storage.

**Security Features (v2.0):**
- ✅ CSRF Protection (Flask-WTF)
- ✅ Brute-Force Protection (Flask-Limiter: 10 login attempts/minute)
- ✅ Hardened Session Security (HttpOnly, SameSite, Secure cookies)
- ✅ Strong Password Requirements (8+ chars, uppercase, lowercase, digit)
- ✅ Custom Error Handlers (404, 500, 429)
- ✅ Rate Limiting on all endpoints
- ✅ Session regeneration on login

## Development Commands

```bash
# Install dependencies (Python 3.10+ recommended for Werkzeug scrypt support)
pip3 install -r requirements.txt

# Run development server (http://localhost:5050, login: admin/admin123)
python3 app.py

# Initialize/reset database (also runs automatically on startup)
python3 -c "from app import init_db; init_db()"

# Generate test data (100-150 students, 20-40 wishes)
# Prompts for confirmation if data exists; pipe "ja" to auto-confirm
echo "ja" | python3 generate_testdata.py
```

There is no test suite, linter, or build step configured.

## Architecture

Single-file Flask app (`app.py`, ~1330 lines):

- **app.py** — All routes (18 endpoints), database schema, class division algorithm, auth logic, security features, Excel/CSV import processing
- **templates/** — 16 Jinja2 templates extending `base.html` (includes error pages)
- **static/css/style.css** — Apple-inspired responsive design with CSS custom properties
- **static/js/script.js** — Alert auto-dismiss and delete confirmations
- **passenger_wsgi.py** — WSGI entry point for All-Inkl production hosting

### Routes Overview

**Public routes:**
- `/` - Redirects to dashboard or login
- `/login` - Login page (GET/POST) with rate limiting
- `/logout` - Session termination

**Student management:**
- `/students` - List all students with wohnort and schulform columns
- `/students/add` - Add new student (GET/POST) with wohnort and schulform fields
- `/students/edit/<id>` - Edit student (GET/POST) with wohnort and schulform fields
- `/students/delete/<id>` - Delete student (POST, CSRF protected)
- `/students/import` - Import from CSV/Excel (GET/POST) with extensive column mapping
- `/students/duplicates` - Review and manage duplicate students

**Parent wishes management:**
- `/wishes` - List all wishes
- `/wishes/add` - Add new wish (GET/POST)
- `/wishes/edit/<id>` - Edit wish (GET/POST)
- `/wishes/delete/<id>` - Delete wish (POST, CSRF protected)

**Class division:**
- `/generate` - Generate class proposals (GET/POST) - displays classes as "5a, 5b, 5c..."
- `/assignments` - View saved assignments

**User management:**
- `/users` - List users
- `/users/add` - Add new user (GET/POST, enforces password policy)
- `/users/delete/<id>` - Delete user (POST, CSRF protected)

**Wizard & Dashboard:**
- `/dashboard` - Main overview with statistics
- `/wizard` - Start guided wizard
- `/wizard/<step>` - Step-by-step wizard (5 steps)
- `/wizard/cancel` - Cancel wizard
- `/wizard/complete` - Complete wizard

### Database (SQLite)

Four tables: `users`, `students`, `parent_wishes`, `class_assignments`. All queries use parameterized SQL (no ORM). The `class_assignments.data` column stores JSON.

**Student fields:**
- Core: `firstname`, `lastname`, `gender` (m/w/d), `created_by`, `created_at`
- School route: `wohnort` (address/location for carpooling groups)
- School type: `schulform` (H=Hauptschule, R=Realschule, G=Gymnasium, IB=Inklusive Beschulung)
- Additional: `religion` (ethik/katholisch/evangelisch/leer), `sportlich` (0/1), `special_needs` (hoerschaedigung/sprache/sozial_emotional/lernen/leer), `notes`
- Import tracking: `import_batch_id` (UUID for tracking imports)

Schema migrations use `ALTER TABLE ... ADD COLUMN` wrapped in try/except for existing columns. `init_db()` runs on every startup.

### Class Division Algorithm

**Core Functions:** `generate_class_assignment(students, wishes, num_classes, seed, options)` and `find_best_class(student, classes, gender_count, wohnort_count, schulform_count, religion_count, inklusion_count, wish_dict, num_classes, options)`.

Creates N classes (~25 students each), generates 3 proposals with different random seeds.

**Algorithm Priorities (from highest to lowest):**
1. **Geschlechterbalance (SEHR WICHTIG):** -15 per gender ratio concentration
2. **Schulweg-Gruppierung (WICHTIG):** +12 bonus for students from same location (enables carpooling)
3. **Freundewünsche (WICHTIG):** +20 together / -20 separated
4. **Schulform-Verteilung (WICHTIG):** -8 per schulform ratio concentration
5. **Religion (ZWEITRANGIG):** -2 per religion ratio (reduced priority)

**Additional scoring weights:**
- **Size balance:** -10 per size difference from average (always active)
- **Sportklasse:** +50 for athletic students in class 1, -30 penalty otherwise (toggleable)
- **Inklusion limit:** -1000 if class exceeds max special needs count (configurable number)

Options are passed as a dict from the generate route (GET=defaults, POST=form values):
- `gender_balance` (default: True)
- `schulweg_gruppe` (default: True) - groups students by wohnort
- `parent_wishes` (default: True)
- `schulform_balance` (default: True) - distributes H/R/G/IB evenly
- `religion_distribute` / `religion_group` (mutually exclusive)
- `sportklasse`, `max_inklusion`

**Result formatting:**
- Classes are displayed as "5a, 5b, 5c..." instead of "Klasse 1, 2, 3..."
- Wohnorte are simplified to "PLZ Stadt (count)" format (e.g., "61440 Oberursel (3)")
- City counts aggregate multiple addresses from same city

### Import Functionality

CSV/Excel import with extensive column mapping in `process_import_data(data, batch_id)`:

**Specific column recognition for school data:**
- **Vorname/Nachname:** Standard name fields
- **Geschlecht:** m/w/d (männlich/weiblich/divers)
- **SLR_WohnAdresse:** Full address → wohnort field
- **Eignung:** H/R/G values → schulform field
- **IB / VM - s.Liste:** IB sets schulform='IB', VM stored in notes
- **Religion / Wahlfach Religion:** Wahlfach takes precedence
- **Sportklasse:** Ja/X/1 → sportlich=1
- **Freund/ Freundin:** Automatically creates 'together' wishes (attempts name matching)
- **Auf keine Fall mit Kind…:** Automatically creates 'separated' wishes
- **Infos Übergabe / Sonstige / Einwände:** Combined into notes field

**Generic column mapping (flexible recognition):**
- Firstname: `vorname`, `firstname`, `first_name`, `first name`, `name`
- Lastname: `nachname`, `lastname`, `last_name`, `last name`, `familienname`
- Gender: `geschlecht`, `gender`, `sex` (accepts `m/w/d`, `männlich/weiblich/divers`, `male/female`)
- Wohnort: `wohnort`, `ort`, `adresse`, `address`, `schulweg`, `location`, `slr_wonadresse`
- Schulform: `schulform`, `schule`, `school_type`, `bildungsgang`, `eignung`
- Religion: `religion`, `konfession`, `wahlfach religion`
- Sportlich: `sportlich`, `sport`, `athletic`, `sportklasse` (accepts `ja/yes/1/true/x`)
- Special needs: `förderbedarf`, `foerderbedarf`, `special_needs`, `sonderpädagogik`

**Import returns:** `(imported_count, errors, duplicates, wishes_created)`

Imports create a batch ID for tracking and duplicate detection based on firstname+lastname. Friend wishes use intelligent name matching (tries both "Vorname Nachname" and "Nachname Vorname" combinations).

### Authentication & Security

**Authentication:**
- Session-based with bcrypt password hashing (Werkzeug)
- Sessions expire after 2 hours (configurable)
- Max 10 users
- Default admin: `admin/admin123` (⚠️ Must be changed after first login!)

**Security Features:**
- **CSRF Protection:** Flask-WTF with tokens in all forms
- **Rate Limiting:** Flask-Limiter (10 login attempts/minute, 200/day global)
- **Session Security:** HttpOnly, SameSite=Lax, Secure (in production)
- **Password Policy:** Min 8 chars, requires uppercase, lowercase, digit (validated by `validate_password()`)
- **Error Handling:** Custom 404/500/429 pages, no stack traces
- **Input Validation:** Parameterized queries, form validation
- **Session Management:** Regeneration on login, explicit clearing on logout

### Template Structure

All templates extend `base.html` which provides:
- Navigation menu with active state tracking
- Flash message display system
- Consistent header/footer
- Mobile-responsive layout

Templates use Jinja2 syntax with German UI text. Form submissions use POST with CSRF protection via Flask-WTF.

**All forms include CSRF tokens:**
```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- form fields -->
</form>
```

**Key templates:**
- `generate.html` - Displays classes as "5a, 5b, 5c..." with schulform stats and simplified wohnort display
- `students.html` - Includes wohnort and schulform columns
- `add_student.html` / `edit_student.html` - Include wohnort input and schulform dropdown
- `import_students.html` - Excel/CSV upload interface

## Configuration

Environment variables from `.env` (see `.env.example`):
- `SECRET_KEY` — **Required!** Use `secrets.token_hex(32)` to generate
- `FLASK_ENV` — Set to `production` for HTTPS-only cookies
- `FLASK_DEBUG` — Set to `false` in production
- `DATABASE_PATH` — Path to SQLite database (default: `klasseneinteilung.db`)
- `SESSION_LIFETIME` — Session timeout in hours (default: 2)
- `MAX_USERS` — Maximum user accounts (default: 10)
- `MAX_STUDENTS` — Maximum students (default: unlimited)

## Deployment Packages

Three Windows deployment options available:

**klasseneinteilung-app-WINDOWS.zip** - Standard installation with virtualenv
- Requires Python 3.10+ installed
- Uses `INSTALLATION.bat` for one-time setup
- Uses `START.bat` to launch
- Creates desktop shortcut automatically

**klasseneinteilung-app-PORTABLE.zip** - Basic portable version
- No Python installation required
- Downloads Python 3.11.8 Embedded automatically
- Uses `PORTABLE-SETUP.bat` for one-time setup
- Uses `PORTABLE-START.bat` to launch
- Can run from USB stick

**klasseneinteilung-app-PORTABLE-WIN11.zip** - Enhanced portable version (RECOMMENDED for Enterprise)
- **Simplified installation** - Linear STEP 1/5 to 5/5 progress display
- **Completely automatic** - no user input required
- **No admin rights** needed - perfect for restricted Windows 11 Enterprise PCs
- **Automatic browser launch** after installation
- **Desktop shortcut** created automatically
- Uses `PORTABLE-SETUP-WIN11.bat` for one-time setup (simplified, ~80 lines)
- Uses `PORTABLE-START.bat` to launch (~60 lines, ASCII-only)
- Includes comprehensive documentation:
  * `START-HIER.txt` - Quick start guide (first file users see)
  * `PORTABLE-ANLEITUNG-WIN11.txt` - Complete user manual
  * `INSTALLATION-VORSCHAU.txt` - Shows what installation looks like
  * `PORTABLE-WIN11-PAKET-INFO.txt` - Technical package details
- Can run from USB stick or network drive
- No system changes, fully portable
- Installation time: 2-3 minutes (one-time), Future starts: 5 seconds
- Downloads during setup: ~27 MB (Python 3.11.8 Embedded + dependencies)
- **File size:** ~63 KB (all batch files use CRLF + ASCII only)

All packages include all security features and full documentation.

## Language

All UI text and documentation is in German. Python identifiers and database columns are in English.

## All-Inkl Deployment

The app is configured for Passenger WSGI deployment on All-Inkl shared hosting. Key files:
- `passenger_wsgi.py` - WSGI entry point (requires path customization)
- `.htaccess` - Passenger configuration (requires path customization)
- `.env` - Production environment variables with generated SECRET_KEY

Both `passenger_wsgi.py` and `.htaccess` contain placeholder paths that must be replaced with actual server paths before deployment.

## Windows Batch Files - Critical Requirements

**IMPORTANT:** All `.bat` files MUST have:
1. **Windows line endings (CRLF)** - Use `sed 's/$/\r/'` to convert from Unix LF
2. **ASCII-only characters** - No Unicode (╔═╗║█░), no emojis (❌✓ℹ️), no special chars
3. **No German umlauts** in code - Replace: ä→ae, ö→oe, ü→ue, ß→ss
4. **Simple PowerShell commands** - Avoid nested quotes, use direct Invoke-WebRequest
5. **Test with:** `file filename.bat` should show "DOS batch file text, ASCII text, with CRLF line terminators"

**Affected files:**
- `PORTABLE-SETUP-WIN11.bat` - Installation script
- `PORTABLE-START.bat` - Portable startup script
- `START.bat` - Standard startup script
- `INSTALLATION.bat` - Standard installation script

**Common error:** Files created on macOS/Linux default to LF endings and may contain UTF-8 encoded umlauts. Windows CMD cannot parse these correctly and shows errors like "Der Befehl 'n!' ist entweder falsch geschrieben...".

**Fix template:**
```bash
# Create file, then convert to Windows format
cat > filename.bat << 'EOF'
@echo off
chcp 65001 >nul 2>&1
echo Text without umlauts (ue instead of ü)
EOF
sed 's/$/\r/' filename.bat > filename-temp.bat
mv filename-temp.bat filename.bat
```

## Important Notes

- **Python Version:** 3.10+ recommended (Werkzeug 3.0.1 requires scrypt support)
- **Default Password:** `admin123` does NOT meet new security requirements - must be changed immediately
- **Security Updates:** See `SECURITY-UPDATES.md` for detailed documentation of v2.0 security improvements
- **DSGVO Compliance:** App is designed for German schools following HDSG and HSchG § 83
- **Algorithm Priorities:** Gender balance is most important, followed by school route grouping, friend wishes, schulform distribution, and religion (secondary)
- **Class Naming:** Classes are displayed as "5a, 5b, 5c..." for 5th grade (hardcoded)
- **Wohnort Display:** Addresses are parsed to extract "PLZ Stadt" and grouped by city with counts
- **Enterprise Deployment:** Use `klasseneinteilung-app-PORTABLE-WIN11.zip` for restricted Windows 11 environments - it's the most user-friendly option
- **Batch Files:** Always use ASCII + CRLF when editing .bat files (see section above)
