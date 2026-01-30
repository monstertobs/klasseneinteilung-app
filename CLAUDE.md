# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A DSGVO-compliant Flask web application for generating school class divisions (5th grade). Considers parent wishes, gender balance, religion, special needs (inclusive education), and athletic ability to produce optimized class assignments. Designed for deployment on All-Inkl shared hosting with local SQLite storage.

## Development Commands

```bash
# Install dependencies
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

Single-file Flask app (`app.py`, ~600 lines):

- **app.py** — All routes (16 endpoints), database schema, class division algorithm, auth logic
- **templates/** — 11 Jinja2 templates extending `base.html`
- **static/css/style.css** — Apple-inspired responsive design with CSS custom properties
- **static/js/script.js** — Alert auto-dismiss and delete confirmations
- **passenger_wsgi.py** — WSGI entry point for All-Inkl production hosting

### Database (SQLite)

Four tables: `users`, `students`, `parent_wishes`, `class_assignments`. All queries use parameterized SQL (no ORM). The `class_assignments.data` column stores JSON.

**Student fields:** `firstname`, `lastname`, `gender` (m/w/d), `religion` (ethik/katholisch/evangelisch/leer), `sportlich` (0/1), `special_needs` (hoerschaedigung/sprache/sozial_emotional/lernen/leer), `notes`.

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

### Authentication

Session-based with bcrypt password hashing (Werkzeug). Sessions expire after 2 hours. Max 10 users. Default admin: `admin/admin123`.

## Configuration

Environment variables from `.env` (see `.env.example`): `SECRET_KEY`, `FLASK_DEBUG`, `DATABASE_PATH`, `SESSION_LIFETIME`, `MAX_USERS`, `MAX_STUDENTS`.

## Language

All UI text and documentation is in German. Python identifiers and database columns are in English.
