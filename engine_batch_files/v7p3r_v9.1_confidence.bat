@echo off
REM V7P3R v9.1 Confidence System
REM New confidence-based multithreaded evaluation

cd /d "%~dp0../V7P3R Chess Engine/v7p3r-chess-engine"

REM Check if engine exists
if not exist "src/v7p3r_uci.py" (
    echo Error: src/v7p3r_uci.py not found!
    echo Please ensure the V7P3R source is available.
    pause
    exit /b 1
)

echo Starting V7P3R v9.1 Confidence System...
python src/v7p3r_uci.py
