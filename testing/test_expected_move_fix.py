#!/usr/bin/env python3
"""
Test the expected move fix in puzzle analyzer
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'chess-puzzle-challenger', 'src'))

from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
from database import PuzzleDatabase

def test_expected_move_validation():
    """Test the new expected move validation on a few puzzles"""
    
    # Initialize analyzer with V7P3R v9.6
    analyzer = V7P3RPuzzleAnalyzer(
        v7p3r_path=r"engines\v7p3r\V7P3R_v9.6.exe"
    )
    
    # Get a few test puzzles
    db = PuzzleDatabase(r"chess-puzzle-challenger\puzzles.db")
    puzzles = db.query_puzzles(
        min_rating=1400,
        max_rating=1600,
        quantity=3
    )
    
    print("Testing Expected Move Validation Fix")
    print("=" * 50)
    
    for i, puzzle in enumerate(puzzles, 1):
        print(f"\nTest Puzzle {i}:")
        print(f"ID: {puzzle.id}")
        print(f"FEN: {puzzle.fen}")
        print(f"Raw moves: {puzzle.moves}")
        
        # Test the new expected move method
        expected_move, is_valid, turn_info = analyzer.get_correct_expected_move(puzzle)
        print(f"Expected move: {expected_move}")
        print(f"Valid: {is_valid}")
        print(f"Turn info: {turn_info}")
        
        # Get Stockfish moves for comparison
        stockfish_moves = analyzer.get_stockfish_top_moves(puzzle.fen, 5, 2.0)
        print("Stockfish top 5:")
        for j, (move, score) in enumerate(stockfish_moves[:5], 1):
            indicator = "✅" if move == expected_move else "  "
            print(f"  {j}. {move} (score: {score:+d}) {indicator}")
        
        if is_valid:
            expected_in_top5 = any(expected_move == sf_move for sf_move, _ in stockfish_moves)
            print(f"Expected move in Stockfish top 5: {'✅ Yes' if expected_in_top5 else '❌ No'}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_expected_move_validation()
