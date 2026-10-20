@echo off
title ScamShield AI Server
echo ========================================================
echo   ScamShield AI - AI Scam & Phishing Detection System
echo   KLE BCA Coding Club - Problem AI . 03
echo ========================================================
echo.
echo Activating virtual environment (.venv)...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error activating .venv. Ensure virtualenv exists.
    pause
    exit /b 1
)
echo.
echo Starting Uvicorn web server on http://127.0.0.1:8000 ...
echo   - Web Dashboard: http://127.0.0.1:8000
echo   - API Swagger UI: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
