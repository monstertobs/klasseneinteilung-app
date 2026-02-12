import os
import sqlite3
import random
import csv
import io
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

try:
    from openpyxl import load_workbook
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Sicherheits-Konfiguration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF-Token läuft mit Session ab
app.config['WTF_CSRF_SSL_STRICT'] = False  # Für Entwicklung

# CSRF-Schutz aktivieren
csrf = CSRFProtect(app)

# Rate Limiting aktivieren (verhindert Brute-Force-Angriffe)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

DATABASE = 'klasseneinteilung.db'

def get_db():
    """Datenbankverbindung herstellen"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
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
        ('schulform', 'TEXT DEFAULT ""')
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
        password_hash = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      ('admin', password_hash))
    
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
                         wizard_step=wizard_step)

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
        special_needs = request.form.get('special_needs', '').strip()
        notes = request.form.get('notes', '').strip()

        if firstname and lastname:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO students (firstname, lastname, gender, wohnort, schulform, religion, sportlich, special_needs, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (firstname, lastname, gender, wohnort, schulform, religion, sportlich, special_needs, notes, session['user_id']))
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
        special_needs = request.form.get('special_needs', '').strip()
        notes = request.form.get('notes', '').strip()

        if firstname and lastname:
            cursor.execute('''
                UPDATE students
                SET firstname = ?, lastname = ?, gender = ?, wohnort = ?, schulform = ?, religion = ?,
                    sportlich = ?, special_needs = ?, notes = ?
                WHERE id = ?
            ''', (firstname, lastname, gender, wohnort, schulform, religion, sportlich, special_needs, notes, student_id))
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

    # Optionen aus POST oder Standardwerte
    if request.method == 'POST':
        max_inklusion = request.form.get('max_inklusion', '0')
        try:
            max_inklusion = int(max_inklusion)
        except ValueError:
            max_inklusion = 0

        options = {
            'gender_balance': 'gender_balance' in request.form,
            'parent_wishes': 'parent_wishes' in request.form,
            'religion_distribute': 'religion_distribute' in request.form,
            'religion_group': 'religion_group' in request.form,
            'max_inklusion': max_inklusion,
            'sportklasse': 'sportklasse' in request.form,
        }
    else:
        options = {
            'gender_balance': True,
            'parent_wishes': True,
            'religion_distribute': True,
            'religion_group': False,
            'max_inklusion': 0,
            'sportklasse': False,
        }

    # Anzahl der Klassen berechnen (ca. 25 Schüler pro Klasse)
    num_classes = max(1, (len(students) + 24) // 25)

    # 3 verschiedene Einteilungen generieren
    proposals = []
    for i in range(3):
        proposal = generate_class_assignment(students, wishes, num_classes, i, options)
        proposals.append(proposal)

    return render_template('generate.html', proposals=proposals, num_classes=num_classes, options=options)

def generate_class_assignment(students, wishes, num_classes, seed, options):
    """Intelligente Klasseneinteilung generieren"""
    random.seed(seed)

    # Schüler in Liste konvertieren
    student_list = [dict(s) for s in students]
    random.shuffle(student_list)

    # Bei Sportklasse: sportliche Schüler zuerst verteilen
    if options.get('sportklasse', False):
        sportliche = [s for s in student_list if s.get('sportlich')]
        andere = [s for s in student_list if not s.get('sportlich')]
        student_list = sportliche + andere

    # Klassen initialisieren
    classes = [[] for _ in range(num_classes)]

    # Geschlechterzähler pro Klasse
    gender_count = [{'m': 0, 'w': 0, 'd': 0} for _ in range(num_classes)]

    # Wohnort-Zähler pro Klasse (für Schulweg-Gruppierung)
    wohnort_count = [{} for _ in range(num_classes)]

    # Schulform-Zähler pro Klasse
    schulform_count = [{'H': 0, 'R': 0, 'G': 0, 'IB': 0, '': 0} for _ in range(num_classes)]

    # Religionszähler pro Klasse
    religion_count = [{'ethik': 0, 'katholisch': 0, 'evangelisch': 0, '': 0} for _ in range(num_classes)]

    # Inklusionszähler pro Klasse
    inklusion_count = [0 for _ in range(num_classes)]

    # Wünsche als Dictionary organisieren
    wish_dict = {}
    for wish in wishes:
        student_id = wish['student_id']
        if student_id not in wish_dict:
            wish_dict[student_id] = []
        wish_dict[student_id].append(wish)

    # Schüler auf Klassen verteilen
    for student in student_list:
        best_class = find_best_class(student, classes, gender_count, wohnort_count, schulform_count, religion_count, inklusion_count, wish_dict, num_classes, options)
        classes[best_class].append(student)

        # Geschlechterzähler aktualisieren
        gender = student.get('gender', 'd')
        if gender in gender_count[best_class]:
            gender_count[best_class][gender] += 1

        # Wohnort-Zähler aktualisieren
        wohnort = student.get('wohnort', '').strip()
        if wohnort:
            if wohnort in wohnort_count[best_class]:
                wohnort_count[best_class][wohnort] += 1
            else:
                wohnort_count[best_class][wohnort] = 1

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
            'sport_count': sport_count,
            'is_sportklasse': options.get('sportklasse', False) and i == 0
        })

    return result

def find_best_class(student, classes, gender_count, wohnort_count, schulform_count, religion_count, inklusion_count, wish_dict, num_classes, options):
    """Beste Klasse für einen Schüler finden"""
    scores = []
    max_inklusion = options.get('max_inklusion', 0)

    for i, cls in enumerate(classes):
        score = 0

        # Größenausgleich (bevorzuge kleinere Klassen)
        avg_size = sum(len(c) for c in classes) / num_classes
        size_diff = len(cls) - avg_size
        score -= size_diff * 10

        # Sportklasse: Klasse 1 (Index 0) für sportliche Schüler
        if options.get('sportklasse', False):
            if student.get('sportlich'):
                if i == 0:
                    score += 50  # Sportliche stark in Klasse 1
                else:
                    score -= 30  # Sportliche weg von anderen Klassen
            else:
                if i == 0:
                    score -= 30  # Nicht-sportliche weg von Klasse 1

        # Inklusion: Limit pro Klasse
        if max_inklusion > 0 and student.get('special_needs', ''):
            if inklusion_count[i] >= max_inklusion:
                score -= 1000  # Klasse ist voll → stark vermeiden

        # Geschlechterbalance (SEHR WICHTIG - höchste Priorität)
        if options.get('gender_balance', True):
            gender = student.get('gender', 'd')
            if gender in gender_count[i]:
                total = sum(gender_count[i].values())
                if total > 0:
                    gender_ratio = gender_count[i][gender] / total
                    score -= gender_ratio * 15  # Erhöht von 5 auf 15 für höhere Priorität

        # Schulweg-Gruppierung (wichtig für Fahrgemeinschaften)
        if options.get('schulweg_gruppe', True):
            wohnort = student.get('wohnort', '').strip()
            if wohnort:
                if wohnort in wohnort_count[i]:
                    # Bonus für gleichen Wohnort (Fahrgemeinschaften möglich)
                    score += wohnort_count[i][wohnort] * 12

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
                    password_hash = generate_password_hash(password)
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
