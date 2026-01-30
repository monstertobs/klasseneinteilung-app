# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A DSGVO-compliant Flask web application for generating school class divisions (5th grade). It considers parent wishes (together/separated), gender balance, and special needs to produce optimized class assignments. Designed for deployment on All-Inkl shared hosting with local SQLite storage.

## Development Commands

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run development server (http://localhost:5000, login: admin/admin123)
python3 app.py

# Initialize/reset database
python3 -c "from app import init_db; init_db()"

# Generate test data (100-150 students, 20-40 wishes)
python3 generate_testdata.py
```

There is no test suite, linter, or build step configured.

## Architecture

Single-file Flask app (`app.py`, ~500 lines) following MVC pattern:

- **app.py** — All routes (16 endpoints), database schema, class division algorithm, auth logic
- **templates/** — 13 Jinja2 templates extending `base.html`
- **static/css/style.css** — Responsive styles with purple gradient theme
- **static/js/script.js** — Alert auto-dismiss and delete confirmations
- **passenger_wsgi.py** — WSGI entry point for All-Inkl production hosting

### Database (SQLite)

Four tables: `users`, `students`, `parent_wishes`, `class_assignments`. All queries use parameterized SQL (no ORM). The `class_assignments.data` column stores JSON.

### Class Division Algorithm

Located in the `/generate` route handler. Creates N classes (~25 students each), applies weighted scoring: +20 for "together" wishes, -20 for "separated" wishes, plus gender balance optimization. Generates 3 proposals with different random seeds.

### Authentication

Flask-Login with bcrypt password hashing (Werkzeug). Sessions expire after 2 hours. Max 10 users, max 250 students (configurable via `.env`).

## Configuration

Environment variables loaded from `.env` (see `.env.example`): `SECRET_KEY`, `FLASK_DEBUG`, `DATABASE_PATH`, `SESSION_LIFETIME`, `MAX_USERS`, `MAX_STUDENTS`.

## Language

All UI text, documentation, and variable naming in templates is in German. Code comments and Python identifiers are in English.
