@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
color 0A
cls

REM Absoluter Pfad zum App-Verzeichnis (funktioniert auch ohne CD-Rechte)
set "APP_DIR=%~dp0"

echo.
echo ================================================================
echo KLASSENEINTEILUNG - PORTABLE INSTALLATION
echo Fuer Windows 11 ohne Administrator-Rechte
echo ================================================================
echo.
echo Diese Installation laeuft komplett automatisch.
echo Bitte warten Sie, bis der Vorgang abgeschlossen ist...
echo.
timeout /t 2 /nobreak >nul

set PYTHON_URL=https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip
set PIP_URL=https://bootstrap.pypa.io/get-pip.py

echo [SCHRITT 1/6] Pruefe Python...
if exist "%APP_DIR%python-portable\python.exe" (
    echo Python bereits vorhanden. Ueberspringe Download.
    goto :install_pip
)

echo [SCHRITT 2/6] Erstelle Verzeichnis...
if not exist "%APP_DIR%python-portable" mkdir "%APP_DIR%python-portable"
if not exist "%APP_DIR%python-portable" (
    echo FEHLER: Verzeichnis konnte nicht erstellt werden.
    echo Bitte stellen Sie sicher, dass Sie Schreibrechte fuer diesen Ordner haben.
    pause
    exit /b 1
)

echo [SCHRITT 3/6] Lade Python herunter (ca. 20 MB)...
echo Dies kann 1-2 Minuten dauern...
echo.
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%APP_DIR%python-portable\python.zip'"

if not exist "%APP_DIR%python-portable\python.zip" (
    echo.
    echo FEHLER: Download fehlgeschlagen!
    echo.
    echo Moegliche Ursachen:
    echo - Keine Internetverbindung
    echo - Firewall blockiert Download
    echo.
    pause
    exit /b 1
)

echo [SCHRITT 3/6] Entpacke Python...
powershell -Command "Expand-Archive -Path '%APP_DIR%python-portable\python.zip' -DestinationPath '%APP_DIR%python-portable' -Force"
del "%APP_DIR%python-portable\python.zip"

echo [SCHRITT 3/6] Konfiguriere Python...
echo python311.zip> "%APP_DIR%python-portable\python311._pth"
echo .>> "%APP_DIR%python-portable\python311._pth"
echo Lib\site-packages>> "%APP_DIR%python-portable\python311._pth"
echo import site>> "%APP_DIR%python-portable\python311._pth"

:install_pip
echo [SCHRITT 4/6] Installiere pip...
if not exist "%APP_DIR%python-portable\get-pip.py" (
    powershell -Command "Invoke-WebRequest -Uri '%PIP_URL%' -OutFile '%APP_DIR%python-portable\get-pip.py'"
)
"%APP_DIR%python-portable\python.exe" "%APP_DIR%python-portable\get-pip.py" --no-warn-script-location >nul 2>&1

echo [SCHRITT 5/6] Installiere Abhaengigkeiten...
echo Dies kann 2-3 Minuten dauern...
"%APP_DIR%python-portable\python.exe" -m pip install --no-warn-script-location "--target=%APP_DIR%python-portable\Lib\site-packages" Flask==3.0.0 Flask-WTF==1.2.1 Werkzeug==3.0.1 Flask-Limiter==3.5.0 Flask-Session==0.8.0 python-dotenv==1.0.0 openpyxl==3.1.2 reportlab==4.0.9 >nul 2>&1

echo [SCHRITT 6/6] Generiere Sicherheitsschluessel...
if not exist "%APP_DIR%.env" (
    echo Erstelle .env Datei...
    "%APP_DIR%python-portable\python.exe" -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > "%APP_DIR%.env"
    echo FLASK_DEBUG=False >> "%APP_DIR%.env"
    echo DATABASE_PATH=klasseneinteilung.db >> "%APP_DIR%.env"
    echo SESSION_LIFETIME=2 >> "%APP_DIR%.env"
    echo MAX_USERS=10 >> "%APP_DIR%.env"
    echo MAX_STUDENTS=250 >> "%APP_DIR%.env"
    echo.
    echo Sicherheitsschluessel wurde generiert.
) else (
    echo .env Datei bereits vorhanden.
)

echo.
echo Erstelle Desktop-Verknuepfung...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Klasseneinteilung.lnk'); $s.TargetPath = '%APP_DIR%PORTABLE-START.bat'; $s.WorkingDirectory = '%APP_DIR%'; $s.Save()"

cls
color 0A
echo.
echo ================================================================
echo INSTALLATION ERFOLGREICH!
echo ================================================================
echo.
echo Die App ist jetzt einsatzbereit!
echo Desktop-Verknuepfung wurde erstellt.
echo.
echo WICHTIGER HINWEIS:
echo Das Admin-Passwort wird beim ERSTEN START in der Konsole
echo angezeigt. Bitte notieren Sie es!
echo.
echo Die App wird in 5 Sekunden gestartet...
echo.
timeout /t 5 /nobreak >nul

start "" "%APP_DIR%PORTABLE-START.bat"
exit
