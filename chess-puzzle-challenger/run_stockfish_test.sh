#!/bin/bash
# Script to run Stockfish tests

echo "Running Stockfish comprehensive tests"

# Parse arguments
SAMPLE_SIZE=10
OUTPUT_DIR="reports"
STOCKFISH_PATH="src/stockfish.exe"
DB_PATH="puzzles.db"

if [ "$1" != "" ]; then
    SAMPLE_SIZE=$1
fi

# Run the tests
python run_tests.py stockfish --stockfish "$STOCKFISH_PATH" --db "$DB_PATH" --output "$OUTPUT_DIR" --sample-size "$SAMPLE_SIZE"

# On Linux, try to open the HTML report if it exists
if [ -f "$OUTPUT_DIR/performance_report.html" ]; then
    echo ""
    echo "Opening performance report..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "$OUTPUT_DIR/performance_report.html"
    elif command -v open &> /dev/null; then
        open "$OUTPUT_DIR/performance_report.html"
    else
        echo "Report saved to $OUTPUT_DIR/performance_report.html"
    fi
fi
