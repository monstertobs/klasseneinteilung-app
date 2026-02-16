@echo off
chcp 65001 >nul 2>&1
cls
echo ========================================================
echo      Klasseneinteilung - Portable Version
echo ========================================================
echo.

REM Pruefe ob portable Python existiert
if not exist python-portable\python.exe (
    echo Portable Python nicht gefunden!
    echo.
    echo Bitte fuehren Sie zuerst "PORTABLE-SETUP-WIN11.bat" aus.
    echo.
    pause
    exit /b 1
)

REM Pruefe ob .env existiert, wenn nicht -> automatisch erstellen
if not exist .env (
    echo .env Datei nicht gefunden - erstelle automatisch...
    echo.
    python-portable\python.exe -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .env
    echo FLASK_DEBUG=False >> .env
    echo DATABASE_PATH=klasseneinteilung.db >> .env
    echo SESSION_LIFETIME=2 >> .env
    echo MAX_USERS=10 >> .env
    echo MAX_STUDENTS=250 >> .env
    echo .env Datei erfolgreich erstellt!
    echo.
)

REM Pruefe ob Datenbank initialisiert werden muss
if not exist klasseneinteilung.db (
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
    python-portable\python.exe -c "from app import init_db; init_db()"
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
python-portable\python.exe app.py
