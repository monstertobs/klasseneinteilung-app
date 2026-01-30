#!/usr/bin/env python3
"""
Test-Daten Generator für Klasseneinteilung-Webapp

Dieses Skript füllt die Datenbank mit Beispieldaten zum Testen.
ACHTUNG: Nur für Testzwecke verwenden!
"""

import sqlite3
import random
from werkzeug.security import generate_password_hash

# Deutsche Vornamen
VORNAMEN_M = [
    "Alexander", "Ben", "Daniel", "Emil", "Felix", "Jonas", "Leon", "Luca",
    "Maximilian", "Noah", "Paul", "Tim", "Tom", "Elias", "Finn", "Jan",
    "Luis", "Lukas", "Niklas", "Oscar", "Samuel", "Simon", "David", "Max"
]

VORNAMEN_W = [
    "Anna", "Clara", "Emma", "Hannah", "Julia", "Laura", "Lea", "Lena",
    "Lisa", "Maria", "Mia", "Paula", "Sarah", "Sophie", "Charlotte", "Emily",
    "Emilia", "Johanna", "Lara", "Luisa", "Marie", "Nele", "Amelie", "Zoe"
]

NACHNAMEN = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner",
    "Becker", "Schulz", "Hoffmann", "Koch", "Bauer", "Richter", "Klein",
    "Wolf", "Schröder", "Neumann", "Braun", "Werner", "Schwarz", "Zimmermann",
    "Krüger", "Hartmann", "Lange", "Schmitt", "Krause", "Meier", "Lehmann",
    "Huber", "Mayer", "Herrmann", "König", "Walter", "Peters", "Lang"
]

BESONDERE_BEDÜRFNISSE = [
    "", "", "", "", "", "", "", "",  # Meistens keine
    "hoerschaedigung",
    "sprache",
    "sozial_emotional",
    "lernen"
]

def init_test_db():
    """Testdatenbank initialisieren"""
    db = sqlite3.connect('klasseneinteilung.db')
    cursor = db.cursor()
    
    # Prüfen ob bereits Daten vorhanden sind
    cursor.execute('SELECT COUNT(*) FROM students')
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"⚠️  Datenbank enthält bereits {count} Schüler.")
        antwort = input("Möchten Sie die Datenbank zurücksetzen? (ja/nein): ")
        if antwort.lower() != 'ja':
            print("Abgebrochen.")
            db.close()
            return
        
        # Daten löschen
        cursor.execute('DELETE FROM parent_wishes')
        cursor.execute('DELETE FROM students')
        cursor.execute('DELETE FROM class_assignments')
        db.commit()
        print("✅ Datenbank zurückgesetzt.")
    
    # Test-Benutzer erstellen (falls nicht vorhanden)
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('testuser',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash('test123')
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      ('testuser', password_hash))
        print("✅ Test-Benutzer 'testuser' erstellt (Passwort: test123)")
    
    # Schüler generieren (100-150 Schüler)
    anzahl_schueler = random.randint(100, 150)
    print(f"\n📝 Generiere {anzahl_schueler} Schüler...")
    
    schueler_ids = []
    
    for i in range(anzahl_schueler):
        geschlecht = random.choice(['m', 'w', 'd'])
        
        if geschlecht == 'm':
            vorname = random.choice(VORNAMEN_M)
        else:
            vorname = random.choice(VORNAMEN_W)
        
        nachname = random.choice(NACHNAMEN)
        besondere_bedürfnisse = random.choice(BESONDERE_BEDÜRFNISSE)
        
        # Manchmal eine Notiz hinzufügen
        notizen = ""
        if random.random() < 0.1:  # 10% Chance
            notizen = random.choice([
                "Sehr schüchtern",
                "Sehr aufgeweckt",
                "Braucht Unterstützung",
                "Sehr sozial",
                "Eher zurückhaltend"
            ])
        
        religion = random.choice(['ethik', 'katholisch', 'evangelisch', ''])
        sportlich = 1 if random.random() < 0.2 else 0  # 20% sportlich

        cursor.execute('''
            INSERT INTO students (firstname, lastname, gender, religion, sportlich, special_needs, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vorname, nachname, geschlecht, religion, sportlich, besondere_bedürfnisse, notizen, 1))
        
        schueler_ids.append(cursor.lastrowid)
    
    print(f"✅ {anzahl_schueler} Schüler erstellt")
    
    # Elternwünsche generieren (ca. 20-30% der Schüler)
    anzahl_wuensche = random.randint(int(anzahl_schueler * 0.2), int(anzahl_schueler * 0.3))
    print(f"\n💬 Generiere {anzahl_wuensche} Elternwünsche...")
    
    for i in range(anzahl_wuensche):
        student_id = random.choice(schueler_ids)
        wish_type = random.choice(['together', 'together', 'separated'])  # Mehr "zusammen" als "getrennt"
        
        # Zufälligen anderen Schüler auswählen
        related_student_id = random.choice([sid for sid in schueler_ids if sid != student_id])
        
        beschreibung = ""
        if random.random() < 0.3:  # 30% Chance für Beschreibung
            if wish_type == 'together':
                beschreibung = random.choice([
                    "Beste Freunde",
                    "Geschwister",
                    "Nachbarskinder",
                    "Gemeinsamer Schulweg"
                ])
            else:
                beschreibung = random.choice([
                    "Konflikt",
                    "Konkurrenzsituation",
                    "Besser getrennt"
                ])
        
        cursor.execute('''
            INSERT INTO parent_wishes (student_id, wish_type, related_student_id, description)
            VALUES (?, ?, ?, ?)
        ''', (student_id, wish_type, related_student_id, beschreibung))
    
    print(f"✅ {anzahl_wuensche} Elternwünsche erstellt")
    
    db.commit()
    db.close()
    
    print("\n🎉 Testdaten erfolgreich generiert!")
    print("\n📊 Zusammenfassung:")
    print(f"   - Schüler: {anzahl_schueler}")
    print(f"   - Elternwünsche: {anzahl_wuensche}")
    print(f"   - Empfohlene Klassenanzahl: {max(1, (anzahl_schueler + 24) // 25)}")
    print("\n🔐 Zugangsdaten:")
    print("   - Admin: admin / admin123")
    print("   - Test-User: testuser / test123")
    print("\n⚠️  WICHTIG: Diese Testdaten sind nur für Demonstrationszwecke!")
    print("   Löschen Sie sie vor dem Produktiveinsatz!")

if __name__ == '__main__':
    print("=" * 60)
    print("  Klasseneinteilung - Test-Daten Generator")
    print("=" * 60)
    print()
    
    try:
        init_test_db()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        print("\nStellen Sie sicher, dass:")
        print("  1. Die Datenbank 'klasseneinteilung.db' existiert")
        print("  2. Sie die app.py mindestens einmal ausgeführt haben")
        print("  3. Sie die nötigen Schreibrechte haben")
