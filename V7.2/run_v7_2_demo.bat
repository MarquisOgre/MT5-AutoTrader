@echo off
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo ================================================================
echo DEXORZO INNOVATIONS - MT5 AUTOTRADER V7.2 - DEMO ONLY
echo ================================================================
echo Created By DEXORZO Innovations
echo.
python -m pip install -r requirements.txt
python v7_2_execution.py
pause
