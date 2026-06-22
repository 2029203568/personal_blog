@echo off
chcp 65001 >nul
cd /d "%~dp0"
set HOST=127.0.0.1
set PORT=8000
set RELOAD=1
python start_site.py
pause
