"""
Tests for the Puzzle Challenger modules.
"""

import os
import pytest
import tempfile
from src.database import PuzzleDatabase, Puzzle
from src.engine import UCIEngine
from src.solver import PuzzleSolver

# Mock data for testing
TEST_PUZZLES = [
    {
        'id': 'test001',
        'fen': 'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3',
        'moves': 'Bb5 a6 Bxc6 dxc6',
        'rating': 1200,
        'themes': 'opening middlegame',
    },
    {
        'id': 'test002',
        'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
        'moves': 'O-O Nxe4 Re1 d5',
        'rating': 1500,
        'themes': 'opening tactical',
    }
]

@pytest.fixture
def db_file():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close file descriptor immediately
    yield path
    try:
        if os.path.exists(path):
            os.unlink(path)
    except PermissionError:
        # On Windows, sometimes we can't immediately delete the file
        # Just log a message and continue
        print(f"Warning: Could not delete temporary file {path}")
        pass

def test_database_creation(db_file):
    """Test creating a database and tables."""
    db = PuzzleDatabase(db_file)
    db.create_tables()
    
    # Add test puzzles
    session = db.Session()
    for puzzle_data in TEST_PUZZLES:
        puzzle = Puzzle(**puzzle_data)
        session.add(puzzle)
    session.commit()
    
    # Query puzzles
    puzzles = db.query_puzzles(themes=['opening'], quantity=10)
    assert len(puzzles) == 2
    
    # Close the session and dispose the engine
    session.close()
    db.engine.dispose()
    
    # Query with strict theme matching
    puzzles = db.query_puzzles(themes=['tactical'], strict_themes=True, quantity=10)
    assert len(puzzles) == 1
    assert puzzles[0].id == 'test002'
    
    # Get puzzle by ID
    puzzle = db.get_puzzle_by_id('test001')
    assert puzzle is not None
    assert puzzle.id == 'test001'
    assert puzzle.rating == 1200

# Skip engine tests if no engine is available
@pytest.mark.skipif(not os.environ.get('TEST_ENGINE_PATH'), reason="No test engine specified")
def test_engine():
    """Test the UCI engine interface."""
    engine_path = os.environ.get('TEST_ENGINE_PATH')
    engine = UCIEngine(engine_path)
    
    try:
        engine.start()
        assert engine.ready
        assert engine.name != "Unknown Engine"
        
        # Test with a simple position
        import chess
        board = chess.Board()
        move = engine.get_best_move(board, 100)
        assert move is not None
        assert len(move) >= 4  # UCI moves are at least 4 chars
        
    finally:
        engine.stop()

# Skip solver tests if no engine is available
@pytest.mark.skipif(not os.environ.get('TEST_ENGINE_PATH'), reason="No test engine specified")
def test_solver(db_file):
    """Test the puzzle solver."""
    engine_path = os.environ.get('TEST_ENGINE_PATH')
    
    # Set up test database
    db = PuzzleDatabase(db_file)
    db.create_tables()
    
    session = db.Session()
    for puzzle_data in TEST_PUZZLES:
        puzzle = Puzzle(**puzzle_data)
        session.add(puzzle)
    session.commit()
    
    solver = PuzzleSolver(engine_path)
    
    try:
        # Get puzzles
        puzzles = db.query_puzzles(quantity=2)
        assert len(puzzles) == 2
        
        # We don't know if the engine will solve these correctly,
        # so just check that the code runs without errors
        results = solver.solve_multiple_puzzles(puzzles, think_time_ms=100, verbose=False)
        
        assert results['total'] == 2
        assert results['solved'] + results['failed'] == 2
        
        # Check report generation
        report = solver.get_performance_report()
        assert isinstance(report, str)
        assert "Performance Report" in report
        
    finally:
        solver.close()
