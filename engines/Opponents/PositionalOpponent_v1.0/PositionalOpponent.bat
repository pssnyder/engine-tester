@echo off

REM Opponent Engine
REM Engine Type: Position-Driven Engine
REM Updated: November 2025

cd /d "%~dp0"

REM Launch engine with Python 3.13
"C:\Users\patss\AppData\Local\Programs\Python\Python313\python.exe" positional_opponent.py

REM Error handling for Arena
if errorlevel 1 (
    echo Error: Could not start the Opponent Engine
    echo Check that Python 3.13 is installed at the specified path
    echo Required packages: python-chess (install via: pip install python-chess)
    echo Verify that the engine is located at the correct path
    pause
)