import os
import sqlite3
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

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
            religion TEXT DEFAULT '',
            sportlich INTEGER DEFAULT 0,
            special_needs TEXT,
            notes TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Spalten nachträglich hinzufügen (für bestehende Datenbanken)
    for col, coldef in [('religion', 'TEXT DEFAULT ""'), ('sportlich', 'INTEGER DEFAULT 0')]:
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

@app.route('/')
def index():
    """Startseite - weiterleiten zu Dashboard oder Login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
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
    
    return render_template('dashboard.html', 
                         student_count=student_count,
                         wish_count=wish_count,
                         assignment_count=assignment_count)

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
        religion = request.form.get('religion', '')
        sportlich = 1 if 'sportlich' in request.form else 0
        special_needs = request.form.get('special_needs', '').strip()
        notes = request.form.get('notes', '').strip()

        if firstname and lastname:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO students (firstname, lastname, gender, religion, sportlich, special_needs, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (firstname, lastname, gender, religion, sportlich, special_needs, notes, session['user_id']))
            db.commit()
            db.close()
            
            flash(f'Schüler {firstname} {lastname} wurde hinzugefügt.', 'success')
            return redirect(url_for('students'))
        else:
            flash('Vorname und Nachname sind erforderlich.', 'danger')
    
    return render_template('add_student.html')

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
        best_class = find_best_class(student, classes, gender_count, religion_count, inklusion_count, wish_dict, num_classes, options)
        classes[best_class].append(student)

        # Geschlechterzähler aktualisieren
        gender = student.get('gender', 'd')
        if gender in gender_count[best_class]:
            gender_count[best_class][gender] += 1

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
        result['classes'].append({
            'number': i + 1,
            'students': cls,
            'count': len(cls),
            'gender_count': gender_count[i],
            'religion_count': religion_count[i],
            'inklusion_count': inklusion_count[i],
            'sport_count': sport_count,
            'is_sportklasse': options.get('sportklasse', False) and i == 0
        })

    return result

def find_best_class(student, classes, gender_count, religion_count, inklusion_count, wish_dict, num_classes, options):
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

        # Geschlechterbalance
        if options.get('gender_balance', True):
            gender = student.get('gender', 'd')
            if gender in gender_count[i]:
                total = sum(gender_count[i].values())
                if total > 0:
                    gender_ratio = gender_count[i][gender] / total
                    score -= gender_ratio * 5

        # Religion verteilen
        if options.get('religion_distribute', False):
            religion = student.get('religion', '') or ''
            if religion and religion in religion_count[i]:
                total = sum(religion_count[i].values())
                if total > 0:
                    rel_ratio = religion_count[i][religion] / total
                    score -= rel_ratio * 5

        # Religion gruppieren
        if options.get('religion_group', False):
            religion = student.get('religion', '') or ''
            if religion and religion in religion_count[i]:
                if religion_count[i][religion] > 0:
                    score += 5

        # Elternwünsche berücksichtigen
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
        elif len(password) < 6:
            flash('Passwort muss mindestens 6 Zeichen lang sein.', 'danger')
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

if __name__ == '__main__':
    # Datenbank initialisieren (immer ausführen für Migrationen)
    init_db()

    # App starten
    app.run(debug=True, host='0.0.0.0', port=5050)
