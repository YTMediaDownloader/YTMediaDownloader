@echo off
cd /d "%~dp0"

if "%~1"=="" (
    echo No URL provided. Using default personal playlist...
    .\.venv\Scripts\python.exe download_playlist.py "https://www.youtube.com/playlist?list=PLNyPiL5e4F2bo2ruSM_ivlbH5xrXMSF7f"
) else (
    :: Run the python script using the provided arguments
    .\.venv\Scripts\python.exe download_playlist.py %*
)

pause
