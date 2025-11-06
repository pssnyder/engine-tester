@echo off
REM VPR Arena Deployment Launcher
REM Revolutionary Dual-Brain Chess Engine: "We create chaos, they respond traditionally, we capitalize"

REM Change to the engine directory
cd /d "%~dp0"

REM Use the working Python 3.13 installation
"C:\Users\patss\AppData\Local\Programs\Python\Python313\python.exe"  src/vpr_engine.py

REM Pause if there's an error
if errorlevel 1 (
    echo.
    echo Error starting VPR Engine
    echo.
    pause
)