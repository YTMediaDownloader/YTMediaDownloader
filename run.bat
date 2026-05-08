@echo off
cd /d "%~dp0"

:: Pass any arguments straight to the python script
:: If no arguments are provided, the script will show the interactive menu
.\.venv\Scripts\python.exe download_playlist.py %*

pause
