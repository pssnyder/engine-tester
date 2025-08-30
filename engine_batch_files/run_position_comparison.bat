@echo off
REM V7P3R Engine Positional Comparison Tool
REM Runs the positional analyzer with all available engines

echo ================================
echo V7P3R Positional Analysis Tool
echo ================================
echo.

cd /d "%~dp0.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found! Please install Python 3.7+ and add to PATH.
    pause
    exit /b 1
)

REM Check if positional analyzer exists
if not exist "v7p3r_positional_analyzer.py" (
    echo Error: v7p3r_positional_analyzer.py not found!
    echo Please ensure you're running this from the engine-tester directory.
    pause
    exit /b 1
)

echo Running positional analysis...
echo This will compare engine performance across historical game positions.
echo.

python v7p3r_positional_analyzer.py

echo.
echo Analysis complete! Check the generated JSON report for detailed results.
pause
