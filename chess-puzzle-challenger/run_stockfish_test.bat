@echo off
REM Script to run Stockfish tests

echo Running Stockfish comprehensive tests

REM Parse arguments
set SAMPLE_SIZE=10
set OUTPUT_DIR=reports
set STOCKFISH_PATH=src\stockfish.exe
set DB_PATH=puzzles.db

if "%1" NEQ "" set SAMPLE_SIZE=%1

REM Run the tests
python run_tests.py stockfish --stockfish %STOCKFISH_PATH% --db %DB_PATH% --output %OUTPUT_DIR% --sample-size %SAMPLE_SIZE%

REM Open the HTML report if it exists
if exist %OUTPUT_DIR%\performance_report.html (
    echo.
    echo Opening performance report...
    start %OUTPUT_DIR%\performance_report.html
)
