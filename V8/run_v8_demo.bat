@echo off
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
mode con: cols=100 lines=50
echo DEXORZO Innovations - MT5 AutoTrader V8 - DEMO ONLY
python -m pip install -r requirements.txt
python v8_execution.py
pause
