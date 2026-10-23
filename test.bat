@echo off
title ScamShield AI Test Suite
echo ========================================================
echo   ScamShield AI - Test Suite Verification
echo   KLE BCA Coding Club - Problem AI . 03
echo ========================================================
echo.
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error activating .venv. Ensure virtualenv exists.
    pause
    exit /b 1
)
echo Running full automated test suite (83 tests)...
pytest tests/ -v
echo.
pause
