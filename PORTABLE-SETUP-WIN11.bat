@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
color 0A
cls

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

echo [SCHRITT 1/5] Pruefe Python...
if exist python-portable\python.exe (
    echo Python bereits vorhanden. Ueberspringe Download.
    goto :install_pip
)

echo [SCHRITT 2/5] Erstelle Verzeichnis...
if not exist python-portable mkdir python-portable

echo [SCHRITT 3/5] Lade Python herunter (ca. 20 MB)...
echo Dies kann 1-2 Minuten dauern...
echo.
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile 'python-portable\python.zip'"

if not exist python-portable\python.zip (
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

echo [SCHRITT 3/5] Entpacke Python...
powershell -Command "Expand-Archive -Path 'python-portable\python.zip' -DestinationPath 'python-portable' -Force"
del python-portable\python.zip

echo [SCHRITT 3/5] Konfiguriere Python...
echo python311.zip> python-portable\python311._pth
echo .>> python-portable\python311._pth
echo Lib\site-packages>> python-portable\python311._pth
echo import site>> python-portable\python311._pth

:install_pip
echo [SCHRITT 4/5] Installiere pip...
if not exist python-portable\get-pip.py (
    powershell -Command "Invoke-WebRequest -Uri '%PIP_URL%' -OutFile 'python-portable\get-pip.py'"
)
python-portable\python.exe python-portable\get-pip.py --no-warn-script-location >nul 2>&1

echo [SCHRITT 5/5] Installiere Abhaengigkeiten...
echo Dies kann 2-3 Minuten dauern...
python-portable\python.exe -m pip install --no-warn-script-location --target=python-portable\Lib\site-packages Flask==3.0.0 Flask-WTF==1.2.1 Werkzeug==3.0.1 Flask-Limiter==3.5.0 python-dotenv==1.0.0 openpyxl==3.1.2 >nul 2>&1

echo.
echo Erstelle Desktop-Verknuepfung...
set SCRIPT_DIR=%CD%
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Klasseneinteilung.lnk'); $s.TargetPath = '%SCRIPT_DIR%\PORTABLE-START.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"

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
echo Die App wird in 5 Sekunden gestartet...
echo.
timeout /t 5 /nobreak >nul

start "" PORTABLE-START.bat
exit
