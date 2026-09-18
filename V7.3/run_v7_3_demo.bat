@echo off
rem DEXORZO Innovations - MT5 AutoTrader V7.3 DEMO
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
mode con: cols=100 lines=50
python -m pip install -r requirements.txt
python v7_3_execution.py
pause
