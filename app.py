"""
Klasseneinteilung App - Intelligente Klasseneinteilung für 5. Klassen

Version: 2.0.0
Author: Tobias Meier <admin(at)secutobs.com>
Date: February 13, 2026
License: Proprietary - All rights reserved

Description:
    Webanwendung zur automatisierten Erstellung von Klasseneinteilungen
    mit Berücksichtigung von Geschlechterverteilung, Schulweg, Elternwünschen,
    Schulformen, Religion, Spezialklassen und Inklusion.

Features:
    - Intelligenter Einteilungs-Algorithmus
    - Export (Excel, CSV, PDF)
    - Mehrere Spezialklassen (Sport, Musik, Theater)
    - Religion-Bündelung
    - IB Min/Max-Einschränkungen
    - Drag & Drop Vorschau-Modus
    - Konflikt-Erkennung und -Auflösung
    - DSGVO-konform
    - Sicherheits-Features (CSRF, Rate Limiting, sichere Sessions)
"""

__version__ = '2.0.0'
__author__ = 'Tobias Meier'
__email__ = 'admin(at)secutobs.com'

# Konstanten
MAX_CLASS_SIZE = 25  # Maximale Anzahl Schüler pro Klasse
__copyright__ = 'Copyright © 2026 Tobias Meier'
__license__ = 'Proprietary'

import os
import sqlite3
import random
import csv
import io
import re
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

try:
    from openpyxl import load_workbook
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

# Lade .env Datei (für SECRET_KEY und andere Konfiguration)
try:
    from dotenv import load_dotenv
    load_dotenv()  # Lädt .env aus dem aktuellen Verzeichnis
except ImportError:
    pass  # python-dotenv nicht installiert (Production mit System-Variablen)

app = Flask(__name__)

# SECRET_KEY muss als Umgebungsvariable gesetzt sein (Sicherheit!)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError(
        "KRITISCHER FEHLER: SECRET_KEY Umgebungsvariable nicht gesetzt!\n"
        "Generieren Sie einen sicheren Key mit:\n"
        "  python3 -c 'import secrets; print(secrets.token_hex(32))'\n"
        "Dann setzen Sie ihn in der .env Datei:\n"
        "  SECRET_KEY=<generierter-key>"
    )

# Session-Konfiguration für Filesystem-basierte Sessions (größere Daten möglich)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# JSON und Encoding-Konfiguration
app.config['JSON_AS_ASCII'] = False  # Erlaubt Unicode in JSON (keine ASCII-Escape-Sequenzen)

# Sicherheits-Konfiguration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF-Token läuft mit Session ab
app.config['WTF_CSRF_SSL_STRICT'] = False  # Für Entwicklung

# CSRF-Schutz aktivieren
csrf = CSRFProtect(app)

# Session initialisieren
Session(app)

# Rate Limiting aktivieren (verhindert Brute-Force-Angriffe)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Response-Header für UTF-8 Encoding setzen
@app.after_request
def after_request(response):
    """Setzt UTF-8 Encoding für alle Responses"""
    if response.content_type and 'text/html' in response.content_type:
        response.content_type = 'text/html; charset=utf-8'
    return response

DATABASE = 'klasseneinteilung.db'

def get_db():
    """Datenbankverbindung herstellen"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    # UTF-8 Encoding für Text-Daten erzwingen
    db.text_factory = str
    return db

def init_db():
    """Datenbank initialisieren"""
    db = get_db()
    cursor = db.cursor()
    
    # Benutzer-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Schüler-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            gender TEXT,
            wohnort TEXT DEFAULT '',
            schulform TEXT DEFAULT '',
            religion TEXT DEFAULT '',
            sportlich INTEGER DEFAULT 0,
            special_needs TEXT,
            notes TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            import_batch_id TEXT,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Spalten nachträglich hinzufügen (für bestehende Datenbanken)
    for col, coldef in [
        ('religion', 'TEXT DEFAULT ""'),
        ('sportlich', 'INTEGER DEFAULT 0'),
        ('import_batch_id', 'TEXT'),
        ('wohnort', 'TEXT DEFAULT ""'),
        ('schulform', 'TEXT DEFAULT ""'),
        ('sport_interesse', 'INTEGER DEFAULT 0'),
        ('musik_interesse', 'INTEGER DEFAULT 0'),
        ('theater_interesse', 'INTEGER DEFAULT 0')
    ]:
        try:
            cursor.execute(f'ALTER TABLE students ADD COLUMN {col} {coldef}')
        except sqlite3.OperationalError:
            pass  # Spalte existiert bereits
    
    # Elternwünsche-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parent_wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            wish_type TEXT NOT NULL,
            related_student_id INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (related_student_id) REFERENCES students (id)
        )
    ''')
    
    # Klasseneinteilungen-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Standard-Admin-User erstellen (falls nicht vorhanden)
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        try:
            # Generiere ein sicheres zufälliges Passwort (16 Zeichen)
            alphabet = string.ascii_letters + string.digits + string.punctuation
            initial_password = ''.join(secrets.choice(alphabet) for _ in range(16))

            # Hash das Passwort mit pbkdf2 für Kompatibilität
            password_hash = generate_password_hash(initial_password, method='pbkdf2:sha256')
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                          ('admin', password_hash))

            # WICHTIG: Passwort nur EINMAL anzeigen (wird nicht gespeichert!)
            print("\n" + "="*70)
            print("WICHTIG: Neuer Admin-Account erstellt!")
            print("="*70)
            print(f"  Benutzername: admin")
            print(f"  Passwort:     {initial_password}")
            print("="*70)
            print("BITTE SOFORT NACH DEM ERSTEN LOGIN ÄNDERN!")
            print("Das Passwort wird nicht erneut angezeigt und ist nicht wiederherstellbar.")
            print("="*70 + "\n")
        except Exception as e:
            # Skip admin user creation if error (user should already exist in DB)
            print(f"Warning: Could not create admin user: {e}")
            pass
    
    db.commit()
    db.close()

def login_required(f):
    """Decorator für Login-Pflicht"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_password(password):
    """
    Validiert Passwort-Sicherheit

    Anforderungen:
    - Mindestens 8 Zeichen
    - Mindestens einen Großbuchstaben
    - Mindestens einen Kleinbuchstaben
    - Mindestens eine Ziffer

    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Passwort muss mindestens 8 Zeichen lang sein."

    if not re.search(r'[A-Z]', password):
        return False, "Passwort muss mindestens einen Großbuchstaben enthalten."

    if not re.search(r'[a-z]', password):
        return False, "Passwort muss mindestens einen Kleinbuchstaben enthalten."

    if not re.search(r'\d', password):
        return False, "Passwort muss mindestens eine Ziffer enthalten."

    return True, ""

@app.route('/')
def index():
    """Startseite - weiterleiten zu Dashboard oder Login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/version')
def version():
    """Version und Autor-Informationen anzeigen"""
    return jsonify({
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'copyright': __copyright__,
        'license': __license__,
        'release_date': 'February 13, 2026'
    })

@app.route('/about')
def about():
    """Über die Anwendung und Kontaktdaten"""
    return render_template('about.html')

@app.route('/algorithm')
def algorithm():
    """Algorithmus-Dokumentation - Wie funktioniert die Klasseneinteilung?"""
    return render_template('algorithm.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Brute-Force-Schutz: Max 10 Login-Versuche pro Minute
def login():
    """Login-Seite"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Input-Validierung
        if not username or not password:
            flash('Bitte füllen Sie alle Felder aus.', 'danger')
            return render_template('login.html')

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()  # Alte Session-Daten löschen
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            session.modified = True
            flash('Erfolgreich angemeldet!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültiger Benutzername oder Passwort.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Haupt-Dashboard"""
    db = get_db()
    cursor = db.cursor()

    # Statistiken abrufen
    cursor.execute('SELECT COUNT(*) as count FROM students')
    student_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM parent_wishes')
    wish_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM class_assignments')
    assignment_count = cursor.fetchone()['count']

    db.close()

    # Wizard-Status prüfen
    wizard_active = session.get('wizard_active', False)
    wizard_step = session.get('wizard_step', 0)

    return render_template('dashboard.html',
                         student_count=student_count,
                         wish_count=wish_count,
                         assignment_count=assignment_count,
                         wizard_active=wizard_active,
                         wizard_step=wizard_step,
                         version=__version__,
                         author=__author__)

@app.route('/students')
@login_required
def students():
    """Schülerliste anzeigen"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM students ORDER BY lastname, firstname')
    students = cursor.fetchall()
    db.close()
    
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    """Schüler hinzufügen"""
    if request.method == 'POST':
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        gender = request.form.get('gender', '')
        wohnort = request.form.get('wohnort', '').strip()
        schulform = request.form.get('schulform', '')
        religion = request.form.get('religion', '')
        sportlich = 1 if 'sportlich' in request.form else 0
        sport_interesse = 1 if 'sport_interesse' in request.form else 0
        special_needs = request.form.get('special_needs', '').strip()
        notes = request.form.get('notes', '').strip()

        if firstname and lastname:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO students (firstname, lastname, gender, wohnort, schulform, religion, sportlich,
                                     sport_interesse, musik_interesse, theater_interesse, special_needs, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (firstname, lastname, gender, wohnort, schulform, religion, sportlich,
                  sport_interesse, 0, 0, special_needs, notes, session['user_id']))
            db.commit()
            db.close()

            flash(f'Schüler {firstname} {lastname} wurde hinzugefügt.', 'success')
            return redirect(url_for('students'))
        else:
            flash('Vorname und Nachname sind erforderlich.', 'danger')

    return render_template('add_student.html')

@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    """Schüler bearbeiten"""
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        gender = request.form.get('gender', '')
        wohnort = request.form.get('wohnort', '').strip()
        schulform = request.form.get('schulform', '')
        religion = request.form.get('religion', '')
        sportlich = 1 if 'sportlich' in request.form else 0
        sport_interesse = 1 if 'sport_interesse' in request.form else 0
        special_needs = request.form.get('special_needs', '').strip()
        notes = request.form.get('notes', '').strip()

        if firstname and lastname:
            cursor.execute('''
                UPDATE students
                SET firstname = ?, lastname = ?, gender = ?, wohnort = ?, schulform = ?, religion = ?,
                    sportlich = ?, sport_interesse = ?, musik_interesse = ?, theater_interesse = ?,
                    special_needs = ?, notes = ?
                WHERE id = ?
            ''', (firstname, lastname, gender, wohnort, schulform, religion, sportlich,
                  sport_interesse, 0, 0, special_needs, notes, student_id))
            db.commit()
            db.close()

            flash(f'Schüler {firstname} {lastname} wurde aktualisiert.', 'success')
            return redirect(url_for('students'))
        else:
            flash('Vorname und Nachname sind erforderlich.', 'danger')

    # Schüler-Daten laden
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    db.close()

    if not student:
        flash('Schüler nicht gefunden.', 'danger')
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)

@app.route('/students/import', methods=['GET', 'POST'])
@login_required
def import_students():
    """Schüler aus CSV/Excel importieren"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Keine Datei ausgewählt.', 'danger')
            return redirect(request.url)

        if not file:
            flash('Ungültige Datei.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        try:
            imported_count = 0
            errors = []
            duplicates = []

            # Eindeutige Batch-ID generieren
            import uuid
            batch_id = str(uuid.uuid4())[:8]

            # CSV-Import
            if file_ext == 'csv':
                stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
                csv_reader = csv.DictReader(stream, delimiter=';')

                # Fallback auf Komma, falls Semikolon nicht funktioniert
                if csv_reader.fieldnames and len(csv_reader.fieldnames) == 1:
                    stream.seek(0)
                    csv_reader = csv.DictReader(stream, delimiter=',')

                imported_count, errors, duplicates, wishes_created = process_import_data(csv_reader, batch_id)

            # Excel-Import
            elif file_ext in ['xlsx', 'xls']:
                if not EXCEL_SUPPORT:
                    flash('Excel-Unterstützung nicht installiert. Bitte installieren Sie openpyxl.', 'danger')
                    return redirect(request.url)

                workbook = load_workbook(filename=file)
                sheet = workbook.active

                # Header-Zeile lesen
                headers = [cell.value for cell in sheet[1]]

                # Daten als Dict-Liste aufbereiten
                data = []
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if any(row):  # Überspringe leere Zeilen
                        row_dict = dict(zip(headers, row))
                        data.append(row_dict)

                imported_count, errors, duplicates, wishes_created = process_import_data(data, batch_id)

            else:
                flash('Ungültiges Dateiformat. Bitte verwenden Sie CSV oder Excel (.xlsx).', 'danger')
                return redirect(request.url)

            # Erfolgsmeldung
            if imported_count > 0:
                flash(f'{imported_count} Schüler erfolgreich importiert!', 'success')

            if wishes_created > 0:
                flash(f'{wishes_created} Freundewünsche automatisch importiert!', 'success')

            if errors:
                flash(f'{len(errors)} Fehler beim Import: ' + ', '.join(errors[:5]), 'warning')

            if duplicates:
                flash(f'⚠️ {len(duplicates)} mögliche Duplikate gefunden! Bitte überprüfen Sie die Liste.', 'warning')

            # Zu Duplikats-Seite weiterleiten, wenn Duplikate gefunden wurden
            if duplicates:
                session['last_import_batch'] = batch_id
                return redirect(url_for('check_duplicates'))

            return redirect(url_for('students'))

        except Exception as e:
            flash(f'Fehler beim Import: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('import_students.html', excel_support=EXCEL_SUPPORT)

def process_import_data(data, batch_id):
    """Verarbeitet Import-Daten (CSV oder Excel)"""
    db = get_db()
    cursor = db.cursor()

    imported_count = 0
    errors = []
    duplicates = []
    wish_data = []  # Für Freundewünsche

    # Mögliche Spaltennamen (flexibel)
    field_mappings = {
        'firstname': ['vorname', 'firstname', 'first_name', 'first name', 'name'],
        'lastname': ['nachname', 'lastname', 'last_name', 'last name', 'familienname'],
        'gender': ['geschlecht', 'gender', 'sex'],
        'wohnort': ['wohnort', 'ort', 'adresse', 'address', 'schulweg', 'location', 'slr_wonadresse', 'slr_wohnadresse'],
        'schulform': ['schulform', 'schule', 'school_type', 'bildungsgang', 'eignung'],
        'religion': ['religion', 'konfession', 'wahlfach religion'],
        'sportlich': ['sportlich', 'sport', 'athletic', 'sporty', 'sportklasse'],
        'special_needs': ['förderbedarf', 'foerderbedarf', 'special_needs', 'special needs', 'sonderpädagogik'],
        'notes': ['notizen', 'notes', 'bemerkungen', 'anmerkungen', 'infos übergabe', 'infos uebergabe', 'sonstige / einwände', 'sonstige / einwaende', 'sonstige']
    }

    # Spezielle Spalten für Freundewünsche und IB/VM
    special_columns = {
        'freund_freundin': ['freund/ freundin', 'freund / freundin', 'freund', 'freundin'],
        'auf_keinen_fall': ['auf keine fall mit kind…', 'auf keinen fall mit kind', 'auf keinen fall', 'nicht mit'],
        'ib_vm': ['ib / vm - s.liste', 'ib / vm', 'ib vm', 'ib/vm']
    }

    for idx, row in enumerate(data, start=1):
        try:
            # Flexibles Mapping
            student_data = {}
            row_lower = {k.lower().strip() if k else '': v for k, v in row.items()}

            # Vorname und Nachname sind Pflichtfelder
            firstname = None
            lastname = None
            notes_parts = []  # Für mehrere Notizen-Felder
            freund_value = None
            keinen_fall_value = None

            # Standard-Felder mappen
            for db_field, possible_names in field_mappings.items():
                for possible_name in possible_names:
                    if possible_name in row_lower and row_lower[possible_name]:
                        value = row_lower[possible_name]

                        # Spezielle Behandlung für verschiedene Felder
                        if db_field == 'firstname':
                            firstname = str(value).strip()
                        elif db_field == 'lastname':
                            lastname = str(value).strip()
                        elif db_field == 'gender':
                            gender_map = {'m': 'm', 'männlich': 'm', 'male': 'm',
                                         'w': 'w', 'weiblich': 'w', 'female': 'w',
                                         'd': 'd', 'divers': 'd', 'diverse': 'd'}
                            student_data['gender'] = gender_map.get(str(value).lower().strip(), '')
                        elif db_field == 'wohnort':
                            student_data['wohnort'] = str(value).strip()
                        elif db_field == 'schulform':
                            schulform_map = {'h': 'H', 'hauptschule': 'H', 'hs': 'H',
                                           'r': 'R', 'realschule': 'R', 'rs': 'R',
                                           'g': 'G', 'gymnasium': 'G', 'gym': 'G',
                                           'ib': 'IB', 'inklusiv': 'IB', 'inklusion': 'IB'}
                            student_data['schulform'] = schulform_map.get(str(value).lower().strip(), str(value).strip())
                        elif db_field == 'religion':
                            student_data['religion'] = str(value).strip()
                        elif db_field == 'sportlich':
                            sportlich_values = ['ja', 'yes', '1', 'true', 'x']
                            student_data['sportlich'] = 1 if str(value).lower().strip() in sportlich_values else 0
                        elif db_field == 'special_needs':
                            student_data['special_needs'] = str(value).strip()
                        elif db_field == 'notes':
                            # Alle Notizen sammeln
                            notes_parts.append(f"{possible_name.title()}: {str(value).strip()}")
                        break

            # Spezielle Spalten verarbeiten
            for special_field, possible_names in special_columns.items():
                for possible_name in possible_names:
                    if possible_name in row_lower and row_lower[possible_name]:
                        value = str(row_lower[possible_name]).strip()
                        if not value:
                            continue

                        if special_field == 'ib_vm':
                            # IB / VM Spalte: IB setzt schulform, VM wird als Notiz gespeichert
                            value_upper = value.upper()
                            if 'IB' in value_upper:
                                student_data['schulform'] = 'IB'
                            if 'VM' in value_upper:
                                notes_parts.append(f"VM: {value}")
                        elif special_field == 'freund_freundin':
                            freund_value = value
                        elif special_field == 'auf_keinen_fall':
                            keinen_fall_value = value
                        break

            # Notizen zusammenführen
            if notes_parts:
                student_data['notes'] = ' | '.join(notes_parts)

            # Pflichtfelder prüfen
            if not firstname or not lastname:
                errors.append(f'Zeile {idx}: Vorname oder Nachname fehlt')
                continue

            # Duplikats-Check (gleicher Vor- und Nachname)
            cursor.execute('''
                SELECT id, firstname, lastname, gender, religion, import_batch_id
                FROM students
                WHERE LOWER(firstname) = LOWER(?) AND LOWER(lastname) = LOWER(?)
            ''', (firstname, lastname))

            existing = cursor.fetchone()
            if existing:
                duplicates.append({
                    'existing_id': existing['id'],
                    'name': f"{firstname} {lastname}",
                    'existing_is_import': existing['import_batch_id'] is not None
                })

            # In Datenbank einfügen (trotz Duplikat, wird später überprüft)
            cursor.execute('''
                INSERT INTO students (firstname, lastname, gender, wohnort, schulform, religion, sportlich, special_needs, notes, created_by, import_batch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                firstname,
                lastname,
                student_data.get('gender', ''),
                student_data.get('wohnort', ''),
                student_data.get('schulform', ''),
                student_data.get('religion', ''),
                student_data.get('sportlich', 0),
                student_data.get('special_needs', ''),
                student_data.get('notes', ''),
                session['user_id'],
                batch_id
            ))

            student_id = cursor.lastrowid
            imported_count += 1

            # Freundewünsche für späteren Import speichern
            if freund_value:
                wish_data.append({
                    'student_id': student_id,
                    'student_name': f"{firstname} {lastname}",
                    'wish_type': 'together',
                    'related_names': freund_value
                })
            if keinen_fall_value:
                wish_data.append({
                    'student_id': student_id,
                    'student_name': f"{firstname} {lastname}",
                    'wish_type': 'separated',
                    'related_names': keinen_fall_value
                })

        except Exception as e:
            errors.append(f'Zeile {idx}: {str(e)}')

    db.commit()

    # Freundewünsche verarbeiten (nach dem Commit, damit alle Schüler in der DB sind)
    wishes_created = 0
    for wish in wish_data:
        try:
            # Namen aus der related_names Spalte extrahieren (kann mehrere Namen enthalten)
            related_names_raw = wish['related_names']
            # Namen können durch Komma, Semikolon oder "und" getrennt sein
            import re
            name_list = re.split(r'[,;]|\sund\s', related_names_raw)

            for related_name in name_list:
                related_name = related_name.strip()
                if not related_name:
                    continue

                # Namen splitten (Vorname Nachname oder Nachname, Vorname)
                name_parts = related_name.replace(',', ' ').split()
                if len(name_parts) < 2:
                    continue

                # Versuche verschiedene Kombinationen (Vorname Nachname und Nachname Vorname)
                possible_combinations = [
                    (name_parts[0], name_parts[1]),  # Vorname Nachname
                    (name_parts[1], name_parts[0])   # Nachname Vorname
                ]

                related_student_id = None
                for first, last in possible_combinations:
                    cursor.execute('''
                        SELECT id FROM students
                        WHERE LOWER(firstname) = LOWER(?) AND LOWER(lastname) = LOWER(?)
                    ''', (first, last))
                    result = cursor.fetchone()
                    if result:
                        related_student_id = result['id']
                        break

                if related_student_id and related_student_id != wish['student_id']:
                    # Prüfen ob Wunsch schon existiert (verhindert Duplikate)
                    cursor.execute('''
                        SELECT id FROM parent_wishes
                        WHERE student_id = ? AND related_student_id = ? AND wish_type = ?
                    ''', (wish['student_id'], related_student_id, wish['wish_type']))

                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO parent_wishes (student_id, related_student_id, wish_type, notes, created_by)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (wish['student_id'], related_student_id, wish['wish_type'],
                              f"Automatisch importiert aus: {wish['related_names']}", session['user_id']))
                        wishes_created += 1
                else:
                    # Name nicht gefunden - als Notiz hinzufügen
                    if related_student_id is None:
                        errors.append(f"Freundewunsch für {wish['student_name']}: '{related_name}' nicht gefunden")

        except Exception as e:
            errors.append(f"Fehler beim Verarbeiten des Wunsches für {wish['student_name']}: {str(e)}")

    db.commit()
    db.close()

    return imported_count, errors, duplicates, wishes_created

@app.route('/students/duplicates')
@login_required
def check_duplicates():
    """Duplikate überprüfen"""
    batch_id = session.get('last_import_batch')

    db = get_db()
    cursor = db.cursor()

    # Alle Schüler mit Duplikaten finden
    cursor.execute('''
        SELECT
            s1.id, s1.firstname, s1.lastname, s1.gender, s1.religion,
            s1.sportlich, s1.special_needs, s1.notes, s1.import_batch_id, s1.created_at,
            COUNT(*) OVER (PARTITION BY LOWER(s1.firstname), LOWER(s1.lastname)) as dup_count
        FROM students s1
        WHERE (
            SELECT COUNT(*)
            FROM students s2
            WHERE LOWER(s1.firstname) = LOWER(s2.firstname)
            AND LOWER(s1.lastname) = LOWER(s2.lastname)
        ) > 1
        ORDER BY LOWER(s1.lastname), LOWER(s1.firstname), s1.created_at
    ''')

    all_duplicates = cursor.fetchall()
    db.close()

    # Gruppiere nach Namen
    duplicates_by_name = {}
    for student in all_duplicates:
        key = f"{student['firstname']} {student['lastname']}".lower()
        if key not in duplicates_by_name:
            duplicates_by_name[key] = []
        duplicates_by_name[key].append(dict(student))

    return render_template('check_duplicates.html',
                         duplicates=duplicates_by_name,
                         batch_id=batch_id)

@app.route('/students/delete-duplicates', methods=['POST'])
@login_required
def delete_duplicates():
    """Ausgewählte Duplikate löschen"""
    student_ids = request.form.getlist('delete_ids[]')

    if not student_ids:
        flash('Keine Schüler zum Löschen ausgewählt.', 'warning')
        return redirect(url_for('check_duplicates'))

    db = get_db()
    cursor = db.cursor()

    for student_id in student_ids:
        # Verbundene Elternwünsche löschen
        cursor.execute('DELETE FROM parent_wishes WHERE student_id = ? OR related_student_id = ?',
                      (student_id, student_id))

        # Schüler löschen
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))

    db.commit()
    db.close()

    flash(f'{len(student_ids)} Duplikat(e) erfolgreich gelöscht!', 'success')

    # Prüfen, ob noch Duplikate vorhanden
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM students s1
        WHERE (
            SELECT COUNT(*)
            FROM students s2
            WHERE LOWER(s1.firstname) = LOWER(s2.firstname)
            AND LOWER(s1.lastname) = LOWER(s2.lastname)
        ) > 1
    ''')
    remaining = cursor.fetchone()['count']
    db.close()

    if remaining > 0:
        return redirect(url_for('check_duplicates'))
    else:
        session.pop('last_import_batch', None)
        return redirect(url_for('students'))

@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    """Schüler löschen"""
    db = get_db()
    cursor = db.cursor()

    # Zuerst verbundene Elternwünsche löschen
    cursor.execute('DELETE FROM parent_wishes WHERE student_id = ? OR related_student_id = ?',
                  (student_id, student_id))

    # Dann den Schüler löschen
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.commit()
    db.close()

    flash('Schüler wurde gelöscht.', 'success')
    return redirect(url_for('students'))

@app.route('/students/delete_multiple', methods=['POST'])
@login_required
def delete_multiple_students():
    """Mehrere ausgewählte Schüler löschen"""
    student_ids = request.form.getlist('student_ids')

    if not student_ids:
        flash('Keine Schüler ausgewählt.', 'warning')
        return redirect(url_for('students'))

    db = get_db()
    cursor = db.cursor()

    count = 0
    for student_id in student_ids:
        # Zuerst verbundene Elternwünsche löschen
        cursor.execute('DELETE FROM parent_wishes WHERE student_id = ? OR related_student_id = ?',
                      (student_id, student_id))

        # Dann den Schüler löschen
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        count += 1

    db.commit()
    db.close()

    flash(f'{count} Schüler wurden gelöscht.', 'success')
    return redirect(url_for('students'))

@app.route('/students/delete_all', methods=['POST'])
@login_required
def delete_all_students():
    """Alle Schüler löschen"""
    db = get_db()
    cursor = db.cursor()

    # Zähle Schüler vor dem Löschen
    cursor.execute('SELECT COUNT(*) FROM students')
    count = cursor.fetchone()[0]

    if count == 0:
        flash('Keine Schüler vorhanden.', 'info')
        return redirect(url_for('students'))

    # Zuerst alle Elternwünsche löschen
    cursor.execute('DELETE FROM parent_wishes')

    # Dann alle Schüler löschen
    cursor.execute('DELETE FROM students')

    db.commit()
    db.close()

    flash(f'Alle {count} Schüler wurden gelöscht.', 'success')
    return redirect(url_for('students'))

@app.route('/wishes')
@login_required
def wishes():
    """Elternwünsche anzeigen"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT pw.*, 
               s1.firstname || ' ' || s1.lastname as student_name,
               s2.firstname || ' ' || s2.lastname as related_student_name
        FROM parent_wishes pw
        JOIN students s1 ON pw.student_id = s1.id
        LEFT JOIN students s2 ON pw.related_student_id = s2.id
        ORDER BY s1.lastname, s1.firstname
    ''')
    wishes = cursor.fetchall()
    db.close()
    
    return render_template('wishes.html', wishes=wishes)

@app.route('/wishes/add', methods=['GET', 'POST'])
@login_required
def add_wish():
    """Elternwunsch hinzufügen"""
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        wish_type = request.form.get('wish_type')
        related_student_id = request.form.get('related_student_id') or None
        description = request.form.get('description', '').strip()
        
        if student_id and wish_type:
            cursor.execute('''
                INSERT INTO parent_wishes (student_id, wish_type, related_student_id, description)
                VALUES (?, ?, ?, ?)
            ''', (student_id, wish_type, related_student_id, description))
            db.commit()
            flash('Elternwunsch wurde hinzugefügt.', 'success')
            db.close()
            return redirect(url_for('wishes'))
        else:
            flash('Schüler und Wunsch-Typ sind erforderlich.', 'danger')
    
    # Schülerliste für Dropdown
    cursor.execute('SELECT * FROM students ORDER BY lastname, firstname')
    students = cursor.fetchall()
    db.close()
    
    return render_template('add_wish.html', students=students)

@app.route('/wishes/edit/<int:wish_id>', methods=['GET', 'POST'])
@login_required
def edit_wish(wish_id):
    """Elternwunsch bearbeiten"""
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        wish_type = request.form.get('wish_type')
        related_student_id = request.form.get('related_student_id') or None
        description = request.form.get('description', '').strip()

        if student_id and wish_type:
            cursor.execute('''
                UPDATE parent_wishes
                SET student_id = ?, wish_type = ?, related_student_id = ?, description = ?
                WHERE id = ?
            ''', (student_id, wish_type, related_student_id, description, wish_id))
            db.commit()
            flash('Elternwunsch wurde aktualisiert.', 'success')
            db.close()
            return redirect(url_for('wishes'))
        else:
            flash('Schüler und Wunsch-Typ sind erforderlich.', 'danger')

    # Wunsch laden
    cursor.execute('SELECT * FROM parent_wishes WHERE id = ?', (wish_id,))
    wish = cursor.fetchone()

    # Schülerliste für Dropdown
    cursor.execute('SELECT * FROM students ORDER BY lastname, firstname')
    students = cursor.fetchall()
    db.close()

    if not wish:
        flash('Elternwunsch nicht gefunden.', 'danger')
        return redirect(url_for('wishes'))

    return render_template('edit_wish.html', wish=wish, students=students)

@app.route('/wishes/delete/<int:wish_id>', methods=['POST'])
@login_required
def delete_wish(wish_id):
    """Elternwunsch löschen"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM parent_wishes WHERE id = ?', (wish_id,))
    db.commit()
    db.close()

    flash('Elternwunsch wurde gelöscht.', 'success')
    return redirect(url_for('wishes'))

@app.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    """Klasseneinteilungen generieren"""
    db = get_db()
    cursor = db.cursor()

    # Alle Schüler abrufen
    cursor.execute('SELECT * FROM students ORDER BY lastname, firstname')
    students = cursor.fetchall()

    # Alle Elternwünsche abrufen
    cursor.execute('SELECT * FROM parent_wishes')
    wishes = cursor.fetchall()

    db.close()

    if len(students) == 0:
        flash('Keine Schüler vorhanden. Bitte fügen Sie zuerst Schüler hinzu.', 'warning')
        return redirect(url_for('students'))

    # Anzahl der Klassen berechnen (max. 25 Schüler pro Klasse)
    num_classes = max(1, (len(students) + MAX_CLASS_SIZE - 1) // MAX_CLASS_SIZE)

    # Validierung: Warnung wenn Klassen sehr voll werden
    avg_class_size = len(students) / num_classes
    if avg_class_size > MAX_CLASS_SIZE - 2:  # Warnung ab 23+ Schüler pro Klasse
        flash(f'ℹ️ {num_classes} Klassen erstellt für {len(students)} Schüler (Ø {avg_class_size:.1f} pro Klasse, max. {MAX_CLASS_SIZE})', 'info')

    # Optionen aus POST oder Standardwerte
    if request.method == 'POST':
        # IB Min/Max
        ib_min = int(request.form.get('ib_min', '0'))
        ib_max = int(request.form.get('ib_max', '0'))

        # Validierung: min <= max
        if ib_min > ib_max and ib_max > 0:
            flash('IB-Minimum darf nicht größer als Maximum sein.', 'danger')
            ib_min = 0
            ib_max = 0

        # Spezialklassen
        specialized_classes = {}
        specialized_classes['sport'] = int(request.form.get('specialized_sport_count', '0'))

        # Freie Spezialklasse
        custom_count = int(request.form.get('specialized_custom_count', '0'))
        custom_name = request.form.get('specialized_custom_name', '').strip()
        if custom_count > 0 and custom_name:
            specialized_classes['custom'] = custom_count
            specialized_classes['custom_name'] = custom_name
        else:
            specialized_classes['custom'] = 0
            specialized_classes['custom_name'] = ''

        # Pre-Generation Check: Genug IB-Schüler?
        if ib_max > 0:
            ib_students = [s for s in students if s['schulform'] == 'IB']
            if len(ib_students) > num_classes * ib_max:
                flash(f'⚠️ Zu viele IB-Schüler ({len(ib_students)}) für {num_classes} Klassen mit max {ib_max} pro Klasse', 'warning')

        options = {
            'gender_balance': 'gender_balance' in request.form,
            'parent_wishes': 'parent_wishes' in request.form,
            'religion_distribute': 'religion_distribute' in request.form,
            'religion_group': 'religion_group' in request.form,
            'religion_bundle': 'religion_bundle' in request.form,
            'sportklasse': 'sportklasse' in request.form,
            'specialized_classes': specialized_classes,
            'ib_min': ib_min,
            'ib_max': ib_max,
        }
    else:
        options = {
            'gender_balance': True,
            'parent_wishes': True,
            'religion_distribute': True,
            'religion_group': False,
            'religion_bundle': False,
            'sportklasse': False,
            'specialized_classes': {'sport': 0, 'custom': 0, 'custom_name': ''},
            'ib_min': 2,
            'ib_max': 5,
        }

    # 3 verschiedene Einteilungen generieren
    proposals = []
    for i in range(3):
        proposal = generate_class_assignment(students, wishes, num_classes, i, options)
        proposals.append(proposal)

    # Proposals in Session speichern für Export
    session['last_proposals'] = proposals

    return render_template('generate.html', proposals=proposals, num_classes=num_classes, options=options)

def extract_city_from_wohnort(wohnort):
    """Extrahiere Stadt (PLZ + Stadtname) aus vollständiger Adresse"""
    import re
    if not wohnort or not wohnort.strip():
        return None
    match = re.search(r'(\d{5})\s+([^,]+)', wohnort)
    if match:
        plz = match.group(1)
        stadt = match.group(2).strip()
        # Entferne Klammern wie "(Taunus)"
        stadt = re.sub(r'\s*\([^)]*\)', '', stadt).strip()
        return f"{plz} {stadt}"
    return None

def extract_plz_from_wohnort(wohnort):
    """Extrahiere nur die PLZ aus vollständiger Adresse"""
    import re
    if not wohnort or not wohnort.strip():
        return None
    match = re.search(r'(\d{5})', wohnort)
    if match:
        return match.group(1)
    return None

def generate_class_assignment(students, wishes, num_classes, seed, options):
    """Intelligente Klasseneinteilung generieren"""
    random.seed(seed)

    # Schüler in Liste konvertieren
    student_list = [dict(s) for s in students]
    random.shuffle(student_list)

    # Spezialklassen: Mapping von Klassen-Indizes zu Spezialtypen
    specialized_mapping = {}
    specialized_classes = options.get('specialized_classes', {})
    class_idx = 0

    # Sport-Klassen zuerst
    sport_count = specialized_classes.get('sport', 0)
    for i in range(sport_count):
        if class_idx < num_classes:
            specialized_mapping[class_idx] = 'sport'
            class_idx += 1

    # Custom-Klassen danach
    custom_count = specialized_classes.get('custom', 0)
    custom_name = specialized_classes.get('custom_name', '')
    for i in range(custom_count):
        if class_idx < num_classes:
            specialized_mapping[class_idx] = 'custom'
            class_idx += 1

    # Bei Sportklassen: Schüler mit Sport-Interesse zuerst sortieren
    if sport_count > 0:
        interested = [s for s in student_list if s.get('sport_interesse')]
        not_interested = [s for s in student_list if not s.get('sport_interesse')]
        student_list = interested + not_interested

    # Bei Sportklasse: sportliche Schüler zuerst verteilen (backward compatibility)
    if options.get('sportklasse', False):
        sportliche = [s for s in student_list if s.get('sportlich')]
        andere = [s for s in student_list if not s.get('sportlich')]
        student_list = sportliche + andere

    # Klassen initialisieren
    classes = [[] for _ in range(num_classes)]

    # Geschlechterzähler pro Klasse
    gender_count = [{'m': 0, 'w': 0} for _ in range(num_classes)]

    # Wohnort-Zähler pro Klasse (für Schulweg-Gruppierung)
    wohnort_count = [{} for _ in range(num_classes)]

    # Städte-Zähler pro Klasse (für Städte-basierte Gruppierung)
    city_count = [{} for _ in range(num_classes)]

    # PLZ-Zähler pro Klasse (für PLZ-basierte Gruppierung)
    plz_count = [{} for _ in range(num_classes)]

    # Schulform-Zähler pro Klasse
    schulform_count = [{'H': 0, 'R': 0, 'G': 0, 'IB': 0, '': 0} for _ in range(num_classes)]

    # Religionszähler pro Klasse
    religion_count = [{'ethik': 0, 'katholisch': 0, 'evangelisch': 0, '': 0} for _ in range(num_classes)]

    # Inklusionszähler pro Klasse
    inklusion_count = [0 for _ in range(num_classes)]

    # IB-Zähler pro Klasse
    ib_count = [0 for _ in range(num_classes)]

    # Wünsche als Dictionary organisieren
    wish_dict = {}
    for wish in wishes:
        student_id = wish['student_id']
        if student_id not in wish_dict:
            wish_dict[student_id] = []
        wish_dict[student_id].append(wish)

    # Schüler auf Klassen verteilen
    for student in student_list:
        best_class = find_best_class(student, classes, gender_count, wohnort_count, city_count, plz_count, schulform_count, religion_count, inklusion_count, ib_count, wish_dict, num_classes, options, specialized_mapping)
        classes[best_class].append(student)

        # Geschlechterzähler aktualisieren
        gender = student.get('gender', 'm')
        if gender in gender_count[best_class]:
            gender_count[best_class][gender] += 1

        # Wohnort-Zähler aktualisieren
        wohnort = student.get('wohnort', '').strip()
        if wohnort:
            if wohnort in wohnort_count[best_class]:
                wohnort_count[best_class][wohnort] += 1
            else:
                wohnort_count[best_class][wohnort] = 1

            # Städte-Zähler aktualisieren (PLZ + Stadt)
            city = extract_city_from_wohnort(wohnort)
            if city:
                if city in city_count[best_class]:
                    city_count[best_class][city] += 1
                else:
                    city_count[best_class][city] = 1

            # PLZ-Zähler aktualisieren (nur PLZ)
            plz = extract_plz_from_wohnort(wohnort)
            if plz:
                if plz in plz_count[best_class]:
                    plz_count[best_class][plz] += 1
                else:
                    plz_count[best_class][plz] = 1

        # Schulform-Zähler aktualisieren
        schulform = student.get('schulform', '').strip()
        if schulform:
            if schulform in schulform_count[best_class]:
                schulform_count[best_class][schulform] += 1

        # Religionszähler aktualisieren
        religion = student.get('religion', '') or ''
        if religion in religion_count[best_class]:
            religion_count[best_class][religion] += 1

        # Inklusionszähler aktualisieren
        if student.get('special_needs', ''):
            inklusion_count[best_class] += 1

        # IB-Zähler aktualisieren
        if student.get('schulform') == 'IB':
            ib_count[best_class] += 1

    # Ergebnis formatieren
    result = {
        'classes': [],
        'statistics': {
            'total_students': len(student_list),
            'num_classes': num_classes,
            'gender_distribution': gender_count
        }
    }

    for i, cls in enumerate(classes):
        sport_count = sum(1 for s in cls if s.get('sportlich'))

        # Wohnorte vereinfachen: PLZ + Stadt extrahieren und gruppieren
        city_count = {}
        for wohnort, count in wohnort_count[i].items():
            # Extrahiere PLZ (erste 5 Ziffern) und Stadt
            import re
            match = re.search(r'(\d{5})\s+([^,]+)', wohnort)
            if match:
                plz = match.group(1)
                stadt = match.group(2).strip()
                # Entferne Klammern wie "(Taunus)"
                stadt = re.sub(r'\s*\([^)]*\)', '', stadt).strip()
                city_key = f"{plz} {stadt}"
                if city_key in city_count:
                    city_count[city_key] += count
                else:
                    city_count[city_key] = count

        # Bestimme Spezialklassen-Typ
        special_type = specialized_mapping.get(i, None)
        is_sportklasse = options.get('sportklasse', False) and i == 0  # Backward compatibility
        custom_name = options.get('specialized_classes', {}).get('custom_name', '') if special_type == 'custom' else ''

        result['classes'].append({
            'number': i + 1,
            'students': cls,
            'count': len(cls),
            'gender_count': gender_count[i],
            'wohnort_count': wohnort_count[i],
            'city_count': city_count,
            'schulform_count': schulform_count[i],
            'religion_count': religion_count[i],
            'inklusion_count': inklusion_count[i],
            'ib_count': ib_count[i],
            'sport_count': sport_count,
            'is_sportklasse': is_sportklasse,
            'special_type': special_type,
            'custom_name': custom_name
        })

    return result

def find_best_class(student, classes, gender_count, wohnort_count, city_count, plz_count, schulform_count, religion_count, inklusion_count, ib_count, wish_dict, num_classes, options, specialized_mapping=None):
    """Beste Klasse für einen Schüler finden"""
    scores = []
    ib_min = options.get('ib_min', 0)
    ib_max = options.get('ib_max', 0)
    is_ib_student = student.get('schulform') == 'IB'
    if specialized_mapping is None:
        specialized_mapping = {}

    for i, cls in enumerate(classes):
        score = 0

        # HARTE GRENZE: Maximale Klassengröße (25 Schüler)
        if len(cls) >= MAX_CLASS_SIZE:
            score -= 10000  # Extrem harte Blockade - Klasse ist voll
            scores.append(score)
            continue

        # Größenausgleich (bevorzuge kleinere Klassen)
        avg_size = sum(len(c) for c in classes) / num_classes
        size_diff = len(cls) - avg_size
        score -= size_diff * 10

        # Spezialklassen: Interesse-basiertes Scoring
        if i in specialized_mapping:
            special_type = specialized_mapping[i]
            # Nur für Sport-Klassen (Custom hat kein Interesse-Feld)
            if special_type == 'sport':
                if student.get('sport_interesse'):
                    score += 50  # Starker Bonus für passendes Interesse
                else:
                    score -= 20  # Strafe wenn Schüler kein Interesse hat

        # Wenn Schüler Sport-Interesse hat aber nicht in Sport-Spezialklasse
        if student.get('sport_interesse'):
            if specialized_mapping.get(i) != 'sport':
                score -= 10  # Leichte Strafe

        # Sportklasse (backward compatibility): Klasse 1 (Index 0) für sportliche Schüler
        if options.get('sportklasse', False):
            if student.get('sportlich'):
                if i == 0:
                    score += 50  # Sportliche stark in Klasse 1
                else:
                    score -= 30  # Sportliche weg von anderen Klassen
            else:
                if i == 0:
                    score -= 30  # Nicht-sportliche weg von Klasse 1

        # IB Min/Max Einschränkungen
        if ib_min > 0 and ib_max > 0 and is_ib_student:
            current_ib = ib_count[i]
            if current_ib == 0:
                pass  # OK um neue IB-Klasse zu starten
            elif current_ib < ib_min:
                score += 30  # Starker Push um Minimum zu erreichen
            elif ib_min <= current_ib < ib_max:
                score += 10  # Weiter auffüllen
            elif current_ib >= ib_max:
                score -= 1000  # Harte Blockade - Maximum erreicht

        # Geschlechterbalance (SEHR WICHTIG - höchste Priorität)
        if options.get('gender_balance', True):
            gender = student.get('gender', 'm')
            if gender in gender_count[i]:
                total = sum(gender_count[i].values())
                if total > 0:
                    gender_ratio = gender_count[i][gender] / total
                    score -= gender_ratio * 15  # Erhöht von 5 auf 15 für höhere Priorität

        # Schulweg-Gruppierung (WICHTIG - Schüler aus gleicher Stadt/PLZ zusammen)
        if options.get('schulweg_gruppe', True):
            wohnort = student.get('wohnort', '').strip()
            if wohnort:
                # Stadt-Gruppierung (PLZ + Stadtname)
                city = extract_city_from_wohnort(wohnort)
                if city and city in city_count[i]:
                    # HOHER Bonus für gleiche Stadt (Fahrgemeinschaften, soziale Verbindungen)
                    score += city_count[i][city] * 20

                # PLZ-Gruppierung (zusätzlicher Bonus wenn gleiche PLZ aber andere Stadt)
                plz = extract_plz_from_wohnort(wohnort)
                if plz and plz in plz_count[i]:
                    # Mittlerer Bonus für gleiche PLZ (regionale Nähe)
                    score += plz_count[i][plz] * 10

        # Schulform-Verteilung
        if options.get('schulform_balance', True):
            schulform = student.get('schulform', '').strip()
            if schulform:
                total = sum(schulform_count[i].values())
                if total > 0:
                    schulform_ratio = schulform_count[i].get(schulform, 0) / total
                    score -= schulform_ratio * 8

        # Religion verteilen (ZWEITRANGIG - reduzierte Priorität)
        if options.get('religion_distribute', False):
            religion = student.get('religion', '') or ''
            if religion and religion in religion_count[i]:
                total = sum(religion_count[i].values())
                if total > 0:
                    rel_ratio = religion_count[i][religion] / total
                    score -= rel_ratio * 2  # Reduziert von 5 auf 2

        # Religion gruppieren (ZWEITRANGIG - reduzierte Priorität)
        if options.get('religion_group', False):
            religion = student.get('religion', '') or ''
            if religion and religion in religion_count[i]:
                if religion_count[i][religion] > 0:
                    score += 2  # Reduziert von 5 auf 2

        # Religion-Bündelung (Ethik mit Konfessionen)
        if options.get('religion_bundle', False):
            religion = student.get('religion', '') or ''
            if religion == 'ethik':
                konfession_count = religion_count[i].get('katholisch', 0) + religion_count[i].get('evangelisch', 0)
                if konfession_count > 0:
                    score += 15  # Bonus für Vielfalt
                else:
                    score -= 20  # Strafe für Isolation (reine Ethik-Klasse vermeiden)
            elif religion in ['katholisch', 'evangelisch']:
                if religion_count[i].get('ethik', 0) > 0:
                    score += 8  # Bonus wenn Ethik vorhanden

        # Elternwünsche berücksichtigen (WICHTIG)
        if options.get('parent_wishes', True):
            student_id = student['id']
            if student_id in wish_dict:
                for wish in wish_dict[student_id]:
                    wish_type = wish['wish_type']
                    related_id = wish['related_student_id']

                    if related_id:
                        related_in_class = any(s['id'] == related_id for s in cls)

                        if wish_type == 'together' and related_in_class:
                            score += 20
                        elif wish_type == 'separated' and related_in_class:
                            score -= 20

        scores.append(score)

    # Klasse mit höchstem Score auswählen
    best_class = scores.index(max(scores))
    return best_class

@app.route('/wizard')
@login_required
def wizard():
    """Wizard starten oder fortsetzen"""
    # Wizard aktivieren
    session['wizard_active'] = True
    if 'wizard_step' not in session:
        session['wizard_step'] = 1

    return redirect(url_for('wizard_step', step=session['wizard_step']))

@app.route('/wizard/<int:step>')
@login_required
def wizard_step(step):
    """Wizard-Schritt anzeigen"""
    if not session.get('wizard_active'):
        return redirect(url_for('dashboard'))

    session['wizard_step'] = step

    db = get_db()
    cursor = db.cursor()

    # Statistiken für alle Schritte
    cursor.execute('SELECT COUNT(*) as count FROM students')
    student_count = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM parent_wishes')
    wish_count = cursor.fetchone()['count']

    db.close()

    return render_template('wizard.html',
                         step=step,
                         student_count=student_count,
                         wish_count=wish_count)

@app.route('/wizard/cancel')
@login_required
def wizard_cancel():
    """Wizard abbrechen"""
    session.pop('wizard_active', None)
    session.pop('wizard_step', None)
    flash('Wizard abgebrochen.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/wizard/restart')
@login_required
def wizard_restart():
    """Wizard neu starten"""
    session['wizard_active'] = True
    session['wizard_step'] = 1
    flash('Wizard wurde neu gestartet.', 'info')
    return redirect(url_for('wizard_step', step=1))

@app.route('/wizard/complete')
@login_required
def wizard_complete():
    """Wizard abschließen"""
    session.pop('wizard_active', None)
    session.pop('wizard_step', None)
    flash('Glückwunsch! Sie haben erfolgreich eine Klasseneinteilung erstellt! 🎉', 'success')
    return redirect(url_for('assignments'))

@app.route('/assignments')
@login_required
def assignments():
    """Gespeicherte Einteilungen anzeigen"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT ca.*, u.username
        FROM class_assignments ca
        LEFT JOIN users u ON ca.created_by = u.id
        ORDER BY ca.created_at DESC
    ''')
    assignments = cursor.fetchall()
    db.close()

    return render_template('assignments.html', assignments=assignments)

@app.route('/assignments/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    """Einzelne gespeicherte Einteilung anzeigen"""
    import json

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT ca.*, u.username
        FROM class_assignments ca
        LEFT JOIN users u ON ca.created_by = u.id
        WHERE ca.id = ?
    ''', (assignment_id,))
    assignment = cursor.fetchone()
    db.close()

    if not assignment:
        flash('Einteilung nicht gefunden.', 'danger')
        return redirect(url_for('assignments'))

    # Daten aus JSON parsen
    proposal = json.loads(assignment['data'])

    # Als einzelnes Proposal anzeigen (wie in generate.html, aber nur eines)
    return render_template('view_assignment.html',
                         assignment=assignment,
                         proposal=proposal,
                         num_classes=len(proposal['classes']))

@app.route('/save_assignment', methods=['POST'])
@login_required
def save_assignment():
    """Ausgewählte Einteilung speichern"""
    import json

    proposal_index = int(request.form.get('proposal_index', 0))
    proposals = session.get('last_proposals', [])

    if not proposals or proposal_index >= len(proposals):
        flash('Keine gültige Einteilung gefunden. Bitte generieren Sie zuerst eine Einteilung.', 'danger')
        return redirect(url_for('generate'))

    proposal = proposals[proposal_index]

    # Automatischen Namen generieren
    now = datetime.now()
    assignment_name = f"Einteilung vom {now.strftime('%d.%m.%Y %H:%M')}"

    # In Datenbank speichern
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO class_assignments (name, data, created_by, created_at)
        VALUES (?, ?, ?, ?)
    ''', (assignment_name, json.dumps(proposal), session['user_id'], now.strftime('%Y-%m-%d %H:%M:%S')))
    db.commit()
    db.close()

    num_classes = len(proposal['classes'])
    num_students = len([s for c in proposal['classes'] for s in c['students']])
    flash(f'Einteilung "{assignment_name}" erfolgreich gespeichert! ({num_classes} Klassen, {num_students} Schüler)', 'success')
    return redirect(url_for('assignments'))

@app.route('/assignments/<int:assignment_id>/export/<format_type>', methods=['POST'])
@login_required
def export_saved_assignment(assignment_id, format_type):
    """Exportiert eine gespeicherte Einteilung"""
    import json

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT data FROM class_assignments WHERE id = ?', (assignment_id,))
    assignment = cursor.fetchone()
    db.close()

    if not assignment:
        flash('Einteilung nicht gefunden.', 'danger')
        return redirect(url_for('assignments'))

    proposal = json.loads(assignment['data'])

    if format_type == 'excel':
        return generate_excel_export(proposal)
    elif format_type == 'csv':
        return generate_csv_export(proposal)
    elif format_type == 'pdf':
        return generate_pdf_export(proposal)
    else:
        flash('Ungültiges Export-Format.', 'danger')
        return redirect(url_for('view_assignment', assignment_id=assignment_id))

@app.route('/export/<format_type>', methods=['POST'])
@login_required
def export_classes(format_type):
    """Export Klasseneinteilung in verschiedenen Formaten"""
    from flask import make_response, send_file

    try:
        # Hole die Proposals aus der Session
        proposals = session.get('last_proposals', [])
        proposal_index = int(request.form.get('proposal_index', 0))

        if not proposals or proposal_index >= len(proposals):
            flash('Keine gültige Einteilung gefunden. Bitte generieren Sie zuerst eine Einteilung.', 'danger')
            return redirect(url_for('generate'))

        proposal = proposals[proposal_index]

        if format_type == 'excel':
            return generate_excel_export(proposal)
        elif format_type == 'csv':
            return generate_csv_export(proposal)
        elif format_type == 'pdf':
            return generate_pdf_export(proposal)
        else:
            flash('Ungültiges Export-Format.', 'danger')
            return redirect(url_for('generate'))
    except Exception as e:
        flash(f'Fehler beim Export: {str(e)}', 'danger')
        return redirect(url_for('generate'))

def generate_excel_export(proposal):
    """Generiert Excel-Export"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from io import BytesIO
    from flask import send_file

    wb = Workbook()
    wb.remove(wb.active)  # Entferne leeres Sheet

    # Erstelle ein Sheet pro Klasse
    for class_data in proposal['classes']:
        class_name = f"5{chr(96 + class_data['number'])}"
        ws = wb.create_sheet(title=class_name)

        # Header
        ws['A1'] = f"Klasse {class_name}"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:D1')

        # Statistiken
        ws['A3'] = 'Statistiken:'
        ws['A3'].font = Font(bold=True)
        ws['A4'] = f"Gesamt: {class_data['count']} Schüler"
        ws['A5'] = f"Männlich: {class_data['gender_count']['m']}"
        ws['A6'] = f"Weiblich: {class_data['gender_count']['w']}"

        if class_data.get('schulform_count'):
            row = 8
            ws[f'A{row}'] = 'Schulformen:'
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            for sf, count in class_data['schulform_count'].items():
                if count > 0 and sf:
                    ws[f'A{row}'] = f"{sf}: {count}"
                    row += 1

        # Schülerliste Header
        start_row = 14
        ws[f'A{start_row}'] = 'Nachname'
        ws[f'B{start_row}'] = 'Vorname'
        ws[f'C{start_row}'] = 'Geschlecht'
        ws[f'D{start_row}'] = 'Schulform'
        ws[f'E{start_row}'] = 'IB'
        ws[f'F{start_row}'] = 'Wohnort'

        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            ws[f'{col}{start_row}'].font = Font(bold=True)
            ws[f'{col}{start_row}'].fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')

        # Schüler eintragen
        row = start_row + 1
        for student in sorted(class_data['students'], key=lambda s: (s['lastname'], s['firstname'])):
            schulform = student.get('schulform', '')
            is_ib = 'Ja' if schulform == 'IB' else ''
            ws[f'A{row}'] = student['lastname']
            ws[f'B{row}'] = student['firstname']
            ws[f'C{row}'] = student.get('gender', '')
            ws[f'D{row}'] = schulform
            ws[f'E{row}'] = is_ib
            ws[f'F{row}'] = student.get('wohnort', '')
            row += 1

        # Spaltenbreite anpassen
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 8
        ws.column_dimensions['F'].width = 30

    # Speichern in BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'klasseneinteilung_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

def generate_csv_export(proposal):
    """Generiert CSV-Export"""
    from flask import make_response
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow(['Klasse', 'Nachname', 'Vorname', 'Geschlecht', 'Schulform', 'IB', 'Wohnort', 'Religion'])

    # Schüler pro Klasse
    for class_data in proposal['classes']:
        class_name = f"5{chr(96 + class_data['number'])}"
        for student in sorted(class_data['students'], key=lambda s: (s['lastname'], s['firstname'])):
            schulform = student.get('schulform', '')
            is_ib = 'Ja' if schulform == 'IB' else ''
            writer.writerow([
                class_name,
                student['lastname'],
                student['firstname'],
                student.get('gender', ''),
                schulform,
                is_ib,
                student.get('wohnort', ''),
                student.get('religion', '')
            ])

    # Response erstellen
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=klasseneinteilung_{datetime.now().strftime("%Y%m%d")}.csv'

    return response

def generate_pdf_export(proposal):
    """Generiert PDF-Export mit ReportLab"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO
    from flask import send_file
    import unicodedata

    def normalize_text(text):
        """Normalisiert Text für PDF-Export (entfernt diakritische Zeichen)"""
        if not text:
            return text
        # NFD = Normalization Form Decomposed - trennt Buchstaben von diakritischen Zeichen
        # Dann filtern wir nur die Basis-Buchstaben heraus
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

    # PDF erstellen
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Titel-Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1d1d1f'),
        spaceAfter=20
    )

    # Pro Klasse eine Seite
    for idx, class_data in enumerate(proposal['classes']):
        class_name = f"5{chr(96 + class_data['number'])}"

        # Titel
        elements.append(Paragraph(f"Klasse {class_name}", title_style))

        # Statistiken
        stats_data = [
            ['Gesamt:', f"{class_data['count']} Schueler"],
            ['Maennlich:', str(class_data['gender_count']['m'])],
            ['Weiblich:', str(class_data['gender_count']['w'])]
        ]

        stats_table = Table(stats_data, colWidths=[4*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6c757d')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 0.5*cm))

        # Schülerliste
        student_data = [['Nachname', 'Vorname', 'Geschlecht', 'Schulform', 'IB']]
        for student in sorted(class_data['students'], key=lambda s: (s['lastname'], s['firstname'])):
            schulform = student.get('schulform', '')
            is_ib = 'Ja' if schulform == 'IB' else ''
            student_data.append([
                normalize_text(student['lastname']),
                normalize_text(student['firstname']),
                student.get('gender', ''),
                schulform,
                is_ib
            ])

        student_table = Table(student_data, colWidths=[5*cm, 5*cm, 2.5*cm, 2.5*cm, 2*cm])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1d1d1f')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')])
        ]))
        elements.append(student_table)

        # Seitenumbruch nach jeder Klasse außer der letzten
        if idx < len(proposal['classes']) - 1:
            elements.append(PageBreak())

    # PDF generieren
    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'klasseneinteilung_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@app.route('/check_conflicts', methods=['POST'])
@login_required
def check_conflicts():
    """Check for conflicts after student movement"""
    data = request.get_json()
    student_id = data.get('student_id')
    target_class = data.get('target_class')
    modifications = data.get('modifications', {})

    conflicts = []

    try:
        db = get_db()
        cursor = db.cursor()

        # Get student data
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()

        if not student:
            return jsonify({'conflicts': []})

        # Get all parent wishes for this student
        cursor.execute('''
            SELECT pw.*,
                   s1.firstname || ' ' || s1.lastname as student_name,
                   s2.firstname || ' ' || s2.lastname as related_student_name
            FROM parent_wishes pw
            JOIN students s1 ON pw.student_id = s1.id
            LEFT JOIN students s2 ON pw.related_student_id = s2.id
            WHERE pw.student_id = ? OR pw.related_student_id = ?
        ''', (student_id, student_id))
        wishes = cursor.fetchall()

        # Check friend wishes
        for wish in wishes:
            if wish['wish_type'] == 'together':
                # Check if both students would still be in same class
                related_id = wish['related_student_id']
                if related_id:
                    # Check if related student was also moved
                    related_new_class = modifications.get(str(related_id), {}).get('to')
                    if related_new_class and related_new_class != target_class:
                        conflicts.append({
                            'type': 'friend_wish',
                            'severity': 'high',
                            'message': f"{wish['student_name']} möchte mit {wish['related_student_name']} zusammen sein"
                        })

            elif wish['wish_type'] == 'separated':
                # Check if students would be in same class
                related_id = wish['related_student_id']
                if related_id:
                    related_new_class = modifications.get(str(related_id), {}).get('to')
                    if related_new_class == target_class:
                        conflicts.append({
                            'type': 'separation_wish',
                            'severity': 'high',
                            'message': f"{wish['student_name']} soll von {wish['related_student_name']} getrennt sein"
                        })

        # Note: Full conflict checking would require the current proposal data
        # which is not easily accessible here. For now, we focus on wish-based conflicts.
        # Additional checks (IB limits, gender balance, inclusion) would need the complete
        # class composition, which should be tracked in the frontend or passed with the request.

        db.close()

        return jsonify({'conflicts': conflicts})

    except Exception as e:
        return jsonify({'conflicts': [], 'error': str(e)}), 500

@app.route('/suggest_swaps', methods=['POST'])
@login_required
def suggest_swaps():
    """Generate swap suggestions to resolve conflicts"""
    data = request.get_json()
    student_id = data.get('student_id')
    target_class = data.get('target_class')
    modifications = data.get('modifications', {})

    suggestions = []

    try:
        db = get_db()
        cursor = db.cursor()

        # Get student data
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()

        if not student:
            return jsonify({'suggestions': []})

        # Get related students from wishes
        cursor.execute('''
            SELECT DISTINCT s2.id, s2.firstname, s2.lastname, pw.wish_type
            FROM parent_wishes pw
            JOIN students s2 ON (pw.related_student_id = s2.id OR pw.student_id = s2.id)
            WHERE (pw.student_id = ? OR pw.related_student_id = ?)
            AND s2.id != ?
        ''', (student_id, student_id, student_id))
        related_students = cursor.fetchall()

        # Suggestion 1: Move friend together
        for related in related_students:
            if related['wish_type'] == 'together':
                suggestions.append({
                    'description': f"Verschiebe {related['firstname']} {related['lastname']} ebenfalls in die gleiche Klasse",
                    'score': 85,
                    'action': 'move_together',
                    'student_ids': [related['id']]
                })

        # Suggestion 2: Move to alternative class
        cursor.execute('SELECT COUNT(DISTINCT id) as total FROM students')
        total_students = cursor.fetchone()['total']
        num_classes = max(1, (total_students + 24) // 25)

        for i in range(num_classes):
            if str(i) != target_class:
                suggestions.append({
                    'description': f"Verschiebe Schüler stattdessen in Klasse 5{chr(97 + i)}",
                    'score': 60,
                    'action': 'move_to_alternative',
                    'class_id': str(i)
                })

        # Suggestion 3: Revert move
        suggestions.append({
            'description': "Änderung rückgängig machen und ursprüngliche Einteilung beibehalten",
            'score': 50,
            'action': 'revert'
        })

        db.close()

        # Sort by score
        suggestions = sorted(suggestions, key=lambda s: s['score'], reverse=True)[:3]

        return jsonify({'suggestions': suggestions})

    except Exception as e:
        return jsonify({'suggestions': [], 'error': str(e)}), 500

@app.route('/users')
@login_required
def users():
    """Benutzerverwaltung"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, created_at FROM users ORDER BY username')
    users = cursor.fetchall()
    db.close()
    
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Benutzer hinzufügen"""
    db = get_db()
    cursor = db.cursor()
    
    # Anzahl der User prüfen
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()['count']
    
    if user_count >= 10:
        flash('Maximale Anzahl von 10 Benutzern erreicht.', 'warning')
        db.close()
        return redirect(url_for('users'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not username or not password:
            flash('Benutzername und Passwort sind erforderlich.', 'danger')
        elif password != password_confirm:
            flash('Passwörter stimmen nicht überein.', 'danger')
        else:
            # Starke Passwort-Validierung
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                flash(error_msg, 'danger')
            else:
                # Prüfen ob Benutzername bereits existiert
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                if cursor.fetchone():
                    flash('Benutzername existiert bereits.', 'danger')
                else:
                    # Use pbkdf2 instead of scrypt for compatibility
                    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
                    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                                 (username, password_hash))
                    db.commit()
                    flash(f'Benutzer {username} wurde erstellt.', 'success')
                    db.close()
                    return redirect(url_for('users'))
    
    db.close()
    return render_template('add_user.html')

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Benutzer löschen"""
    # Verhindere Selbstlöschung
    if user_id == session['user_id']:
        flash('Sie können sich nicht selbst löschen.', 'danger')
        return redirect(url_for('users'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    db.close()

    flash('Benutzer wurde gelöscht.', 'success')
    return redirect(url_for('users'))

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    """404 Fehlerseite"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 Fehlerseite"""
    # Datenbank-Rollback bei Fehlern
    try:
        db = get_db()
        db.rollback()
        db.close()
    except:
        pass
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(error):
    """Rate Limit überschritten"""
    flash('Zu viele Anfragen. Bitte versuchen Sie es später erneut.', 'warning')
    return redirect(url_for('login')), 429

if __name__ == '__main__':
    # Datenbank initialisieren (immer ausführen für Migrationen)
    init_db()

    # App starten
    app.run(debug=True, host='0.0.0.0', port=5050)
