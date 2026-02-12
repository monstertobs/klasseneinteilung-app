@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
color 0A
mode con cols=80 lines=30
cls

echo.
echo    ================================================================
echo    KLASSENEINTEILUNG - PORTABLE INSTALLATION
echo    Fuer Windows 11 ohne Administrator-Rechte
echo    ================================================================
echo.
echo    Diese Installation laeuft komplett automatisch.
echo    Bitte warten Sie, bis der Vorgang abgeschlossen ist...
echo.
timeout /t 2 /nobreak >nul

REM Fortschritt initialisieren
set progress=0

:progress_update
cls
echo.
echo    ================================================================
echo    KLASSENEINTEILUNG - PORTABLE INSTALLATION
echo    ================================================================
echo.
call :draw_progress %progress%
echo.
goto :progress_continue

:draw_progress
set /a bars=%1/2
set /a spaces=50-%bars%
set "bar_string="
set "space_string="
for /l %%i in (1,1,%bars%) do set "bar_string=!bar_string!#"
for /l %%i in (1,1,%spaces%) do set "space_string=!space_string!."
echo    [!bar_string!!space_string!] %1%%
exit /b

:progress_continue
if %progress%==0 (
    echo    Status: Vorbereitung...
    echo.
    set progress=5
    timeout /t 1 /nobreak >nul
)

REM Pruefe ob portable Python schon existiert
if %progress%==5 (
    if exist python-portable\python.exe (
        echo    Python bereits vorhanden
        set progress=25
        timeout /t 1 /nobreak >nul
        goto :install_packages_progress
    )
    set progress=10
)

if %progress%==10 (
    echo    [SCHRITT 1/4] Erstelle Portable-Umgebung...
    if not exist python-portable mkdir python-portable
    set progress=15
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==15 (
    echo    [SCHRITT 2/4] Lade Python herunter (20 MB)...
    echo    Dies kann 30-60 Sekunden dauern...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip' -OutFile 'python-portable\python-embed.zip'}" >nul 2>&1

    if not exist python-portable\python-embed.zip (
        cls
        color 0C
        echo.
        echo    ================================================================
        echo    FEHLER
        echo    ================================================================
        echo.
        echo    Download fehlgeschlagen!
        echo.
        echo    Moegliche Ursachen:
        echo    - Keine Internet-Verbindung
        echo    - Firewall blockiert den Download
        echo.
        echo    ALTERNATIVE:
        echo    1. Oeffnen Sie: https://www.python.org/downloads/windows/
        echo    2. Laden Sie "Windows embeddable package (64-bit)" herunter
        echo    3. Entpacken Sie die Datei in den Ordner "python-portable"
        echo    4. Fuehren Sie dieses Script erneut aus
        echo.
        pause
        exit /b 1
    )
    set progress=25
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==25 (
    echo    [SCHRITT 2/4] Entpacke Python...
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; Expand-Archive -Path 'python-portable\python-embed.zip' -DestinationPath 'python-portable' -Force" >nul 2>&1
    if exist python-portable\python-embed.zip del python-portable\python-embed.zip >nul 2>&1
    set progress=35
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==35 (
    echo    [SCHRITT 2/4] Konfiguriere Python-Umgebung...
    echo import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Lib', 'site-packages')) > python-portable\sitecustomize.py
    (
    echo python311.zip
    echo .
    echo Lib\site-packages
    echo import site
    ) > python-portable\python311._pth
    set progress=40
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

:install_packages_progress
if %progress%==40 (
    echo    [SCHRITT 3/4] Installiere Paket-Manager (pip)...
    if not exist python-portable\get-pip.py (
        powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python-portable\get-pip.py'}" >nul 2>&1
    )
    python-portable\python.exe python-portable\get-pip.py --no-warn-script-location >nul 2>&1
    set progress=50
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==50 (
    echo    [SCHRITT 4/4] Installiere Web-Framework (Flask)...
    python-portable\python.exe -m pip install --no-warn-script-location --target=python-portable\Lib\site-packages Flask==3.0.0 >nul 2>&1
    set progress=60
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==60 (
    echo    [SCHRITT 4/4] Installiere Sicherheits-Module...
    python-portable\python.exe -m pip install --no-warn-script-location --target=python-portable\Lib\site-packages Flask-WTF==1.2.1 Werkzeug==3.0.1 >nul 2>&1
    set progress=70
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==70 (
    echo    [SCHRITT 4/4] Installiere Rate-Limiting...
    python-portable\python.exe -m pip install --no-warn-script-location --target=python-portable\Lib\site-packages Flask-Limiter==3.5.0 >nul 2>&1
    set progress=80
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==80 (
    echo    [SCHRITT 4/4] Installiere Zusatz-Module...
    python-portable\python.exe -m pip install --no-warn-script-location --target=python-portable\Lib\site-packages python-dotenv==1.0.0 openpyxl==3.1.2 >nul 2>&1
    set progress=90
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==90 (
    echo    Erstelle Desktop-Verknuepfung...
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Klasseneinteilung.lnk'); $Shortcut.TargetPath = '%CD%\PORTABLE-START.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = 'C:\Windows\System32\imageres.dll,3'; $Shortcut.Description = 'Klasseneinteilung App (Portable - Keine Installation erforderlich)'; $Shortcut.Save()" >nul 2>&1
    set progress=95
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==95 (
    echo    Finalisiere Installation...
    set progress=100
    timeout /t 1 /nobreak >nul
    goto :progress_update
)

if %progress%==100 (
    cls
    color 0A
    echo.
    echo    ================================================================
    echo    INSTALLATION ERFOLGREICH!
    echo    ================================================================
    echo.
    call :draw_progress 100
    echo.
    echo    Die Klasseneinteilung-App ist jetzt einsatzbereit!
    echo    Desktop-Verknuepfung wurde erstellt
    echo    Keine Installation erforderlich
    echo    Kann auf USB-Stick kopiert werden
    echo.
    echo    ----------------------------------------------------------------
    echo.
    echo    Die App wird automatisch in 5 Sekunden gestartet...
    echo.
    echo    Oder druecken Sie eine beliebige Taste zum sofortigen Start.
    echo.
    timeout /t 5 >nul

    REM Starte die App
    start "" PORTABLE-START.bat
    exit
)
