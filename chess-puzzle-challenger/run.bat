@echo off
REM Script to run the Puzzle Challenger application

if "%1" == "install" (
    echo Installing dependencies...
    pip install -r requirements.txt
    goto end
)

if "%1" == "import" (
    echo Importing puzzles from lichess_db_puzzle.csv...
    python -m src.main import-puzzles --file lichess_db_puzzle.csv
    goto end
)

if "%1" == "info" (
    echo Displaying database information...
    python -m src.main info %2 %3 %4 %5 %6 %7 %8 %9
    goto end
)

if "%1" == "solve" (
    echo Solving puzzles...
    python -m src.main solve %2 %3 %4 %5 %6 %7 %8 %9
    goto end
)

if "%1" == "create" (
    echo Creating a new puzzle...
    python -m src.main create %2 %3 %4 %5 %6 %7 %8 %9
    goto end
)

if "%1" == "test" (
    echo Running tests...
    pytest
    goto end
)

echo Puzzle Challenger - Chess Engine Testing Tool
echo.
echo Usage: run.bat COMMAND [OPTIONS]
echo.
echo Commands:
echo   install     Install dependencies
echo   import      Import puzzles from lichess_db_puzzle.csv
echo   info        Display database information
echo   solve       Solve puzzles with a chess engine
echo   create      Create a new puzzle
echo   test        Run tests
echo.
echo For more detailed help, use:
echo   python -m src.main --help
echo   python -m src.main COMMAND --help

:end
