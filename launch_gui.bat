@echo off
cd /d "%~dp0"

:: Launch the new GUI Application
start .\.venv\Scripts\pythonw.exe gui_app.py
