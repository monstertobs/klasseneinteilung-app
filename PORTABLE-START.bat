@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM Absoluter Pfad zum App-Verzeichnis (funktioniert auch ohne CD-Rechte)
set "APP_DIR=%~dp0"

cls
echo ========================================================
echo      Klasseneinteilung - Portable Version
echo ========================================================
echo.

REM Pruefe ob portable Python existiert
if not exist "%APP_DIR%python-portable\python.exe" (
    echo Portable Python nicht gefunden!
    echo.
    echo Bitte fuehren Sie zuerst "PORTABLE-SETUP-WIN11.bat" aus.
    echo.
    pause
    exit /b 1
)

REM Pruefe ob .env existiert, wenn nicht -> automatisch erstellen
if not exist "%APP_DIR%.env" (
    echo .env Datei nicht gefunden - erstelle automatisch...
    echo.
    "%APP_DIR%python-portable\python.exe" -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > "%APP_DIR%.env"
    echo FLASK_DEBUG=False >> "%APP_DIR%.env"
    echo DATABASE_PATH=klasseneinteilung.db >> "%APP_DIR%.env"
    echo SESSION_LIFETIME=2 >> "%APP_DIR%.env"
    echo MAX_USERS=10 >> "%APP_DIR%.env"
    echo MAX_STUDENTS=250 >> "%APP_DIR%.env"
    echo .env Datei erfolgreich erstellt!
    echo.
)

REM Pruefe ob Datenbank initialisiert werden muss
if not exist "%APP_DIR%klasseneinteilung.db" (
    echo Erstmalige Nutzung - Initialisiere Datenbank...
    echo.
    echo ========================================================
    echo   WICHTIG: ADMIN-PASSWORT WIRD NUR EINMAL ANGEZEIGT!
    echo ========================================================
    echo.
    echo Bitte notieren Sie sich das Passwort aus der folgenden
    echo Ausgabe. Es wird nicht erneut angezeigt!
    echo.
    timeout /t 3 /nobreak >nul
    echo.
    "%APP_DIR%python-portable\python.exe" -c "import sys; sys.path.insert(0, r'%APP_DIR%'); from app import init_db; init_db()"
    echo.
    echo ========================================================
    echo.
    timeout /t 10 /nobreak
) else (
    echo Datenbank gefunden.
)

echo.
echo Starte Klasseneinteilung-App (Portable)...
echo.
echo --------------------------------------------------------
echo   Die App laeuft jetzt! (Portable Mode)
echo.
echo   Browser oeffnet automatisch in 3 Sekunden...
echo   Falls nicht: http://localhost:5050
echo.
echo   Login:
echo     Benutzername: admin
echo     Passwort: Siehe Konsole beim ERSTEN START
echo.
echo   WICHTIG:
echo   - Aendern Sie das Passwort nach dem ersten Login!
echo   - Mindestens 8 Zeichen
echo   - Gross-, Kleinbuchstaben, Ziffern
echo.
echo   PORTABLE MODE:
echo   - Keine Installation - laeuft von diesem Ordner
echo   - Kann auf USB-Stick kopiert werden
echo   - Funktioniert auf jedem Windows 11 PC
echo.
echo   Zum Beenden: Dieses Fenster schliessen oder Strg+C
echo --------------------------------------------------------
echo.

REM Warte 3 Sekunden
timeout /t 3 /nobreak >nul

REM Oeffne Browser
start http://localhost:5050

REM Starte Flask mit portable Python
"%APP_DIR%python-portable\python.exe" "%APP_DIR%app.py"
