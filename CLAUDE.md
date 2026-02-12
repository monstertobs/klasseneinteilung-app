# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **security-hardened**, DSGVO-compliant Flask web application for generating school class divisions (5th grade). Considers parent wishes, gender balance, religion, special needs (inclusive education), and athletic ability to produce optimized class assignments. Designed for deployment on All-Inkl shared hosting with local SQLite storage.

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

Single-file Flask app (`app.py`, ~1100 lines):

- **app.py** — All routes (18 endpoints), database schema, class division algorithm, auth logic, security features
- **templates/** — 17 Jinja2 templates extending `base.html` (includes error pages)
- **static/css/style.css** — Apple-inspired responsive design with CSS custom properties
- **static/js/script.js** — Alert auto-dismiss and delete confirmations
- **passenger_wsgi.py** — WSGI entry point for All-Inkl production hosting

### Routes Overview

**Public routes:**
- `/` - Redirects to dashboard or login
- `/login` - Login page (GET/POST) with rate limiting
- `/logout` - Session termination

**Student management:**
- `/students` - List all students
- `/students/add` - Add new student (GET/POST)
- `/students/edit/<id>` - Edit student (GET/POST)
- `/students/delete/<id>` - Delete student (POST, CSRF protected)
- `/students/import` - Import from CSV/Excel (GET/POST)
- `/students/duplicates` - Review and manage duplicate students

**Parent wishes management:**
- `/wishes` - List all wishes
- `/wishes/add` - Add new wish (GET/POST)
- `/wishes/edit/<id>` - Edit wish (GET/POST)
- `/wishes/delete/<id>` - Delete wish (POST, CSRF protected)

**Class division:**
- `/generate` - Generate class proposals (GET/POST)
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

**Student fields:** `firstname`, `lastname`, `gender` (m/w/d), `religion` (ethik/katholisch/evangelisch/leer), `sportlich` (0/1), `special_needs` (hoerschaedigung/sprache/sozial_emotional/lernen/leer), `notes`, `import_batch_id` (UUID for tracking imports).

Schema migrations use `ALTER TABLE ... ADD COLUMN` wrapped in try/except for existing columns. `init_db()` runs on every startup.

### Class Division Algorithm

Two functions: `generate_class_assignment()` and `find_best_class()`. Creates N classes (~25 students each), generates 3 proposals with different random seeds.

Scoring weights in `find_best_class()`:
- **Size balance:** -10 per size difference from average (always active)
- **Gender balance:** -5 per gender ratio (toggleable)
- **Parent wishes:** +20 together / -20 separated (toggleable)
- **Religion distribute:** -5 per religion ratio concentration (toggleable)
- **Religion group:** +5 for same religion in class (toggleable, mutually exclusive with distribute)
- **Sportklasse:** +50 for athletic students in class 1, -30 penalty otherwise (toggleable)
- **Inklusion limit:** -1000 if class exceeds max special needs count (configurable number)

Options are passed as a dict from the generate route (GET=defaults, POST=form values).

### Import Functionality

CSV/Excel import with flexible column mapping recognizes various column names:
- Firstname: `vorname`, `firstname`, `first_name`, `first name`, `name`
- Lastname: `nachname`, `lastname`, `last_name`, `last name`, `familienname`
- Gender: `geschlecht`, `gender`, `sex` (accepts `m/w/d`, `männlich/weiblich/divers`, `male/female`)
- Religion: `religion`, `konfession`
- Sportlich: `sportlich`, `sport`, `athletic` (accepts `ja/yes/1/true/x`)
- Special needs: `förderbedarf`, `foerderbedarf`, `special_needs`, `sonderpädagogik`

Imports create a batch ID for tracking and duplicate detection based on firstname+lastname.

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

Two Windows deployment packages available (see `PAKETE-INFO.txt`):

**klasseneinteilung-app-WINDOWS.zip** - Standard installation with virtualenv
- Requires Python 3.10+ installed
- Uses `INSTALLATION.bat` for one-time setup
- Uses `START.bat` to launch
- Creates desktop shortcut automatically

**klasseneinteilung-app-PORTABLE.zip** - Portable version without admin rights
- No Python installation required
- Downloads Python 3.11.8 Embedded automatically
- Uses `PORTABLE-SETUP.bat` for one-time setup
- Uses `PORTABLE-START.bat` to launch
- Can run from USB stick
- No system changes, fully portable

Both packages include all security features and full documentation.

## Language

All UI text and documentation is in German. Python identifiers and database columns are in English.

## All-Inkl Deployment

The app is configured for Passenger WSGI deployment on All-Inkl shared hosting. Key files:
- `passenger_wsgi.py` - WSGI entry point (requires path customization)
- `.htaccess` - Passenger configuration (requires path customization)
- `.env` - Production environment variables with generated SECRET_KEY

Both `passenger_wsgi.py` and `.htaccess` contain placeholder paths that must be replaced with actual server paths before deployment.

## Important Notes

- **Python Version:** 3.10+ recommended (Werkzeug 3.0.1 requires scrypt support)
- **Default Password:** `admin123` does NOT meet new security requirements - must be changed immediately
- **Security Updates:** See `SECURITY-UPDATES.md` for detailed documentation of v2.0 security improvements
- **DSGVO Compliance:** App is designed for German schools following HDSG and HSchG § 83
