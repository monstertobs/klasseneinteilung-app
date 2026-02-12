@echo off
chcp 65001 >nul
cls
echo ═══════════════════════════════════════════════════════
echo      Klasseneinteilung - Portable Version
echo ═══════════════════════════════════════════════════════
echo.

REM Prüfe ob portable Python existiert
if not exist python-portable\python.exe (
    echo ❌ Portable Python nicht gefunden!
    echo.
    echo Bitte führen Sie zuerst "PORTABLE-SETUP.bat" aus.
    echo.
    pause
    exit /b 1
)

REM Prüfe ob Datenbank initialisiert werden muss
if not exist klasseneinteilung.db (
    echo Erstmalige Nutzung - Initialisiere Datenbank...
    python-portable\python.exe -c "from app import init_db; init_db()" 2>nul
    if errorlevel 1 (
        echo ⚠ Datenbank-Initialisierung fehlgeschlagen
        echo (wird beim Start automatisch erstellt)
    ) else (
        echo ✓ Datenbank erstellt
    )
    echo.
)

echo ✓ Starte Klasseneinteilung-App (Portable)...
echo.
echo ┌─────────────────────────────────────────────────────┐
echo │  Die App läuft jetzt! (Portable Mode)              │
echo │                                                      │
echo │  Browser öffnet automatisch in 3 Sekunden...        │
echo │  Falls nicht: http://localhost:5050                 │
echo │                                                      │
echo │  Login:                                              │
echo │    Benutzername: admin                              │
echo │    Passwort:     admin123                           │
echo │                                                      │
echo │  ℹ️  PORTABLE MODE:                                  │
echo │  Keine Installation - läuft von diesem Ordner       │
echo │  Kann auf USB-Stick kopiert werden                  │
echo │  Funktioniert auf jedem Windows 11 PC               │
echo │                                                      │
echo │  Zum Beenden: Dieses Fenster schließen oder Strg+C │
echo └─────────────────────────────────────────────────────┘
echo.

REM Warte 3 Sekunden
timeout /t 3 /nobreak >nul

REM Öffne Browser
start http://localhost:5050

REM Starte Flask mit portable Python
python-portable\python.exe app.py
