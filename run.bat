@echo off
cd /d "%~dp0"

if "%~1"=="" (
    echo No URL provided. Launching interactive menu...
    .\.venv\Scripts\python.exe download_playlist.py
) else (
    :: Run the python script using the provided arguments
    .\.venv\Scripts\python.exe download_playlist.py %*
)

pause
