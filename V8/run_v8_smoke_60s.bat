@echo off
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
mode con: cols=100 lines=30
echo DEXORZO V8 - 60 SECOND DEMO ORDER SMOKE TEST
python -m pip install -r requirements.txt
python v8_smoke_test_60s.py
pause
