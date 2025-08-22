@echo off
REM Setup script for Puzzle Challenger

echo Setting up Puzzle Challenger...

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Download Stockfish if not present
if not exist src\stockfish.exe (
    echo Downloading Stockfish...
    python setup_stockfish.py
)

REM Import puzzles if database doesn't exist
if not exist puzzles.db (
    echo Importing puzzles from Lichess database...
    python -m src.main import-puzzles --file lichess_db_puzzle.csv
)

echo Setup complete!
echo.
echo To run the project:
echo 1. Activate the virtual environment: venv\Scripts\activate
echo 2. Run the CLI: python -m src.main --help
echo 3. Run tests: python run_tests.py unit
echo 4. Run Stockfish tests: run_stockfish_test.bat
echo.
echo For more information, see README.md
