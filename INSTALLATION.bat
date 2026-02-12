@echo off
chcp 65001 >nul
cls
echo ═══════════════════════════════════════════════════════
echo    Klasseneinteilung - Automatische Installation
echo ═══════════════════════════════════════════════════════
echo.

REM Prüfe ob Python installiert ist
echo [1/6] Prüfe Python-Installation...
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ❌ FEHLER: Python ist nicht installiert!
        echo.
        echo Bitte installieren Sie Python von:
        echo https://www.python.org/downloads/
        echo.
        echo WICHTIG: Haken bei "Add Python to PATH" setzen!
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)
echo ✓ Python gefunden

REM Erstelle virtuelle Umgebung
echo.
echo [2/6] Erstelle virtuelle Umgebung...
if exist venv (
    echo ⚠ Virtuelle Umgebung existiert bereits
) else (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo ❌ Fehler beim Erstellen der virtuellen Umgebung
        pause
        exit /b 1
    )
    echo ✓ Virtuelle Umgebung erstellt
)

REM Aktiviere virtuelle Umgebung
echo.
echo [3/6] Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Fehler beim Aktivieren der virtuellen Umgebung
    pause
    exit /b 1
)
echo ✓ Virtuelle Umgebung aktiviert

REM Installiere Dependencies
echo.
echo [4/6] Installiere benötigte Pakete (dauert 1-2 Minuten)...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Fehler beim Installieren der Pakete
    pause
    exit /b 1
)
echo ✓ Alle Pakete installiert

REM Initialisiere Datenbank
echo.
echo [5/6] Initialisiere Datenbank...
%PYTHON_CMD% -c "from app import init_db; init_db()" >nul 2>&1
if errorlevel 1 (
    echo ⚠ Warnung: Datenbank-Initialisierung fehlgeschlagen
    echo (wird beim ersten Start automatisch erstellt)
) else (
    echo ✓ Datenbank initialisiert
)

REM Erstelle Desktop-Verknüpfung
echo.
echo [6/6] Erstelle Desktop-Verknüpfung...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Klasseneinteilung.lnk'); $Shortcut.TargetPath = '%CD%\START.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = 'C:\Windows\System32\shell32.dll,21'; $Shortcut.Description = 'Klasseneinteilung App starten'; $Shortcut.Save()" >nul 2>&1
if errorlevel 1 (
    echo ⚠ Desktop-Verknüpfung konnte nicht erstellt werden
) else (
    echo ✓ Desktop-Verknüpfung erstellt
)

echo.
echo ═══════════════════════════════════════════════════════
echo            ✅ Installation erfolgreich!
echo ═══════════════════════════════════════════════════════
echo.
echo Die App wurde erfolgreich installiert!
echo.
echo So starten Sie die App:
echo.
echo   1. Doppelklick auf "START.bat" in diesem Ordner
echo   2. ODER Doppelklick auf "Klasseneinteilung" auf dem Desktop
echo.
echo Nach dem Start:
echo   - Browser öffnet automatisch
echo   - Login: admin / admin123
echo.
echo Drücken Sie eine Taste, um die App jetzt zu starten...
pause >nul

REM Starte App
call START.bat
