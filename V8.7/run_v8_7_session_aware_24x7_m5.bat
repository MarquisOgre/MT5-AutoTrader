@echo off
setlocal
if /i not "%DEXORZO_MAX_CHILD%"=="1" (
  set "DEXORZO_MAX_CHILD=1"
  start "" /max "%ComSpec%" /k call "%~f0"
  exit /b
)
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
title DEXORZO Innovations - MT5 AutoTrader V8.7 - Session Aware 24x7 M5
cls
echo ==============================================================================
echo DEXORZO Innovations - MT5 AutoTrader V8.7 - Session Aware 24x7 M5
echo ==============================================================================
echo.
python --version
if errorlevel 1 (echo ERROR: Python was not found.&pause&exit /b 1)
echo.
echo Starting V8.7 Session-Aware 24x7 Dynamic M5 AutoTrader...
echo Weekend: Crypto first; FX is skipped. Weekday: FX first.
echo.
python v8_7_execution.py
echo.
pause
