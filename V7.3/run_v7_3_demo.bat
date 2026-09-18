@echo off
rem ================================================================
rem DEXORZO Innovations - MT5 AutoTrader V7.3 - DEMO ONLY
rem ================================================================
if /i not "%DEXORZO_MAXIMIZED_CHILD%"=="1" (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        set "DEXORZO_MAXIMIZED_CHILD=1"
        start "" wt.exe --maximized --window new --size 100,50 cmd /k call "%~f0"
        exit /b
    )
)
cd /d "%~dp0"
mode con: cols=100 lines=50
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
echo.
python --version
python -m pip install -r requirements.txt
python v7_3_execution.py
pause
