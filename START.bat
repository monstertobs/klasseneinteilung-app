@echo off
chcp 65001 >nul
cls
echo ═══════════════════════════════════════════════════════
echo         Klasseneinteilung - App wird gestartet
echo ═══════════════════════════════════════════════════════
echo.

REM Prüfe ob Installation durchgeführt wurde
if not exist venv (
    echo ❌ App wurde noch nicht installiert!
    echo.
    echo Bitte führen Sie zuerst "INSTALLATION.bat" aus.
    echo.
    pause
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call venv\Scripts\activate.bat

REM Starte App
echo ✓ Starte Klasseneinteilung-App...
echo.
echo ┌─────────────────────────────────────────────────────┐
echo │  Die App läuft jetzt!                               │
echo │                                                      │
echo │  Browser öffnet automatisch in 3 Sekunden...        │
echo │  Falls nicht: http://localhost:5050                 │
echo │                                                      │
echo │  Login:                                              │
echo │    Benutzername: admin                              │
echo │    Passwort:     admin123                           │
echo │                                                      │
echo │  Zum Beenden: Dieses Fenster schließen oder Strg+C │
echo └─────────────────────────────────────────────────────┘
echo.

REM Warte 3 Sekunden
timeout /t 3 /nobreak >nul

REM Öffne Browser
start http://localhost:5050

REM Starte Flask
python app.py
