@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
title DEXORZO Innovations - MT5 AutoTrader V8.5.1 - Intelligent 24x7 M5
cls
echo ================================================================================
echo DEXORZO Innovations - MT5 AutoTrader V8.5.1 - Intelligent 24x7 M5
echo ================================================================================
echo.
python --version
if errorlevel 1 (
  echo ERROR: Python was not found.
  pause
  exit /b 1
)
python v8_5_execution.py
pause
