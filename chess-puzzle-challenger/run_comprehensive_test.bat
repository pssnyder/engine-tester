@echo off
REM Script to set up and run the Puzzle Challenger comprehensive test

echo Setting up Puzzle Challenger and running comprehensive test with Stockfish

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if database exists
if not exist puzzles.db (
    echo Importing puzzles from lichess_db_puzzle.csv...
    python -m src.main import-puzzles --file lichess_db_puzzle.csv
)

REM Run the comprehensive test
echo Running comprehensive test with Stockfish...
python test_stockfish.py

REM Open the results
echo Test complete! Results are in the reports directory.
start reports\performance_report.html

pause
