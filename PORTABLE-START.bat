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

REM Pruefe ob Datenbank initialisiert werden muss
if not exist klasseneinteilung.db (
    echo Erstmalige Nutzung - Initialisiere Datenbank...
    python-portable\python.exe -c "from app import init_db; init_db()" 2>nul
    if errorlevel 1 (
        echo Datenbank-Initialisierung fehlgeschlagen
        echo (wird beim Start automatisch erstellt)
    ) else (
        echo Datenbank erstellt
    )
    echo.
)

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
echo     Passwort:     admin123
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
