# Puzzle Challenger

## A platform for testing chess engine implementations by solving puzzles.

This project provides a comprehensive Python-based testing environment for chess enthusiasts and developers to test their chess engines against a wide range of puzzles. It allows users to solve selective puzzles, analyze engine performance, and create new challenges for the community.

**Credit for current puzzle set goes to [Lichess.org](https://lichess.org)**

### Features

- **Puzzle Library**: A collection of chess puzzles of varying difficulty with detailed tagging information.
- **Engine Integration**: Support for any UCI-compatible chess engine (e.g., Stockfish, Leela Chess Zero).
- **Performance Analysis**: Get immediate feedback on your engine's performance with detailed metrics.
- **Visualization**: Generate performance charts and HTML reports to analyze engine strengths and weaknesses.
- **Customizable Testing**: Filter puzzles by themes, difficulty, or create your own test scenarios.
- **Database Management**: Import and manage large puzzle collections efficiently.
- **CLI Interface**: Simple command-line interface with comprehensive options.
- **Custom Puzzles**: Create and share your own puzzles with the community.

### Prerequisites

- Python 3.7 or higher
- A UCI-compatible chess engine (e.g., Stockfish, Leela Chess Zero)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/puzzle-challenger.git
   cd puzzle-challenger
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Unix/MacOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Import puzzles from the Lichess database:
   ```
   python -m src.main import-puzzles --file lichess_db_puzzle.csv
   ```

### Usage

Display help information:
```
python -m src.main --help
```

#### Importing Puzzles

Import puzzles from the Lichess database:
```
python -m src.main import-puzzles --file lichess_db_puzzle.csv --db puzzles.db
```

#### Solving Puzzles

Solve puzzles using a chess engine:
```
python -m src.main solve --engine path/to/engine.exe --quantity 10
```

Solve specific puzzles by ID:
```
python -m src.main solve --engine path/to/engine.exe --puzzle id1 --puzzle id2
```

Solve puzzles with specific themes:
```
python -m src.main solve --engine path/to/engine.exe --themes mate --themes middlegame --quantity 5
```

Limit puzzle difficulty:
```
python -m src.main solve --engine path/to/engine.exe --difficulty 1800 --quantity 10
```

Generate visualizations of results:
```
python -m src.main solve --engine path/to/engine.exe --quantity 10 --visualize --output-dir reports
```

Save results to a JSON file:
```
python -m src.main solve --engine path/to/engine.exe --quantity 10 --save-results results.json
```

#### Creating Custom Puzzles

Create a new puzzle:
```
python -m src.main create --fen "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" --engine path/to/engine.exe --moves e2e4 e7e5 --themes opening
```

#### Database Information

View database statistics:
```
python -m src.main info
```

List all available puzzle themes:
```
python -m src.main info --themes
```

### Command-Line Options

- `-h` or `--help`: Show help message.
- `-f` or `--fen`: Specify a FEN string to load a specific position to solve.
- `-p` or `--puzzle`: Specify puzzle IDs to solve.
- `-e` or `--engine`: Specify the chess engine to use.
- `-c` or `--create`: Create a new puzzle entry.
- `-r` or `--report`: Generate a performance report for the engine.
- `-q` or `--quantity`: Specify the number of puzzles to solve in a session.
- `-t` or `--themes`: Specify themes to filter puzzles by.
- `-s` or `--strictness`: Specify the strictness for puzzle selection queries (true for strict querying of matches to all themes, false for loose querying matching any themes).
- `-l` or `--limit`: Limit puzzles by number of moves. (2-99, 0 returns any number of moves).
- `-d` or `--difficulty` or `--elo`: Specify the max difficulty level of puzzles by ELO rating (400-3500, 0 returns any difficulty).

### Development

### Running Tests

The project includes comprehensive test suites for validating functionality.

#### Unit Tests

Run all unit tests:
```
python run_tests.py unit
```

Run a specific test file:
```
python run_tests.py unit tests/test_puzzle_challenger.py
```

#### Comprehensive Engine Tests

Run the Stockfish test suite (Windows):
```
run_stockfish_test.bat [sample_size]
```

Run the Stockfish test suite (Linux/Mac):
```
./run_stockfish_test.sh [sample_size]
```

Or run directly:
```
python run_tests.py stockfish --stockfish path/to/stockfish.exe --db puzzles.db --output reports --sample-size 100
```

### Project Structure

```
puzzle-challenger/
├── src/                 # Source code
│   ├── __init__.py
│   ├── database.py      # Database management
│   ├── engine.py        # UCI engine interface
│   ├── solver.py        # Puzzle solver implementation
│   ├── cli.py           # Command line interface
│   ├── visualization.py # Results visualization
│   └── main.py          # Main entry point
├── tests/               # Test suite
│   ├── test_puzzle_challenger.py # Unit tests
│   └── test_stockfish.py         # Stockfish integration tests
├── requirements.txt     # Project dependencies
├── setup.py             # Setup configuration
├── run_tests.py         # Test runner
├── run_stockfish_test.bat # Windows test script
├── run_stockfish_test.sh  # Linux/Mac test script
└── README.md            # Project documentation
```

### Next Steps

The following enhancements are planned for future releases:

1. **Web Interface**: Develop a web interface for easier interaction with the system.
2. **Multi-Engine Comparison**: Support comparing multiple engines on the same puzzle set.
3. **Advanced Analytics**: Add more detailed performance metrics and analysis tools.
4. **Puzzle Rating System**: Implement a system to rate puzzles based on engine performance.
5. **Cloud Integration**: Add support for cloud-based engines and puzzle databases.
6. **Tournament Mode**: Create a tournament system to compare multiple engines.
7. **Puzzle Generation**: Automated puzzle creation from game positions.
8. **Interactive Learning**: Add an interactive mode for learning from engine solutions.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
