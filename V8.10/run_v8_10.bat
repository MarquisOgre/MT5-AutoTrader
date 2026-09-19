@echo off
cd /d "%~dp0"
title DEXORZO Innovations - MT5 AutoTrader V8.10
python v8_10_execution.py
if errorlevel 1 pause
