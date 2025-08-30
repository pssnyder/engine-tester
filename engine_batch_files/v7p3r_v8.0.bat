@echo off
REM V7P3R v8.0 Enhanced
REM Enhanced version with regressions

cd /d "%~dp0engines"

REM Check if engine exists
if not exist "V7P3R_v8.0.exe" (
    echo Error: V7P3R_v8.0.exe not found!
    echo Please place the engine executable in the engines directory.
    pause
    exit /b 1
)

echo Starting V7P3R v8.0 Enhanced...
V7P3R_v8.0.exe
