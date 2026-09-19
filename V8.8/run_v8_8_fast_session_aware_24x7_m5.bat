@echo off
if /I not "%~1"=="MAX" (
  start "DEXORZO Innovations - MT5 AutoTrader V8.8" /MAX cmd /k ""%~f0" MAX"
  exit /b
)
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title DEXORZO Innovations - MT5 AutoTrader V8.8 - FAST 24x7 M5
python --version
python v8_8_execution.py
pause
