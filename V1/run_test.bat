@echo off
title MT5 AutoTrader - Connection Test
py -m pip install -r requirements.txt
py test_connection.py
pause
