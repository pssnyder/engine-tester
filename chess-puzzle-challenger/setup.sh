#!/bin/bash
# Setup script for Puzzle Challenger

echo "Setting up Puzzle Challenger..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download Stockfish if not present
if [ ! -f "src/stockfish" ]; then
    echo "Downloading Stockfish..."
    python setup_stockfish.py
fi

# Import puzzles if database doesn't exist
if [ ! -f "puzzles.db" ]; then
    echo "Importing puzzles from Lichess database..."
    python -m src.main import-puzzles --file lichess_db_puzzle.csv
fi

echo "Setup complete!"
echo ""
echo "To run the project:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the CLI: python -m src.main --help"
echo "3. Run tests: python run_tests.py unit"
echo "4. Run Stockfish tests: ./run_stockfish_test.sh"
echo ""
echo "For more information, see README.md"
