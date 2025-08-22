#!/bin/bash
# Script to run the Puzzle Challenger application

case "$1" in
    "install")
        echo "Installing dependencies..."
        pip install -r requirements.txt
        ;;
    "import")
        echo "Importing puzzles from lichess_db_puzzle.csv..."
        python -m src.main import-puzzles --file lichess_db_puzzle.csv
        ;;
    "info")
        echo "Displaying database information..."
        python -m src.main info "${@:2}"
        ;;
    "solve")
        echo "Solving puzzles..."
        python -m src.main solve "${@:2}"
        ;;
    "create")
        echo "Creating a new puzzle..."
        python -m src.main create "${@:2}"
        ;;
    "test")
        echo "Running tests..."
        pytest
        ;;
    *)
        echo "Puzzle Challenger - Chess Engine Testing Tool"
        echo
        echo "Usage: ./run.sh COMMAND [OPTIONS]"
        echo
        echo "Commands:"
        echo "  install     Install dependencies"
        echo "  import      Import puzzles from lichess_db_puzzle.csv"
        echo "  info        Display database information"
        echo "  solve       Solve puzzles with a chess engine"
        echo "  create      Create a new puzzle"
        echo "  test        Run tests"
        echo
        echo "For more detailed help, use:"
        echo "  python -m src.main --help"
        echo "  python -m src.main COMMAND --help"
        ;;
esac
