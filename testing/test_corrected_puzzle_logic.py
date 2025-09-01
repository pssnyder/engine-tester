#!/usr/bin/env python3
"""
Test the corrected puzzle challenge logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'chess-puzzle-challenger', 'src'))

from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
from database import PuzzleDatabase

def test_puzzle_challenge_logic():
    """Test the corrected puzzle challenge position logic"""
    
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Get the same test puzzle from before
    db = PuzzleDatabase(r"chess-puzzle-challenger\puzzles.db")
    puzzles = db.query_puzzles(
        min_rating=1400,
        max_rating=1600,
        quantity=1
    )
    
    if not puzzles:
        print("No puzzles found!")
        return
    
    puzzle = puzzles[0]
    print("Testing Corrected Puzzle Challenge Logic")
    print("=" * 50)
    print(f"Puzzle ID: {puzzle.id}")
    print(f"Original FEN: {puzzle.fen}")
    print(f"Solution moves: {puzzle.moves}")
    print()
    
    # Test the corrected logic
    challenge_fen, expected_move, is_valid, context_info = analyzer.get_puzzle_challenge_position(puzzle)
    
    print("CORRECTED ANALYSIS:")
    print(f"Challenge FEN: {challenge_fen}")
    print(f"Expected move: {expected_move}")
    print(f"Valid: {is_valid}")
    print(f"Context: {context_info}")
    print()
    
    if is_valid:
        # Get Stockfish analysis of the challenge position
        stockfish_moves = analyzer.get_stockfish_top_moves(challenge_fen, 5, 2.0)
        print("Stockfish analysis of CHALLENGE position:")
        for i, (move, score) in enumerate(stockfish_moves, 1):
            indicator = "🎯" if move == expected_move else "  "
            print(f"  {i}. {move} (score: {score:+d}) {indicator}")
        
        expected_in_top5 = any(expected_move == sf_move for sf_move, _ in stockfish_moves)
        print(f"\nExpected move in Stockfish top 5: {'✅ YES' if expected_in_top5 else '❌ NO'}")
        
        if expected_in_top5:
            rank = next(i for i, (sf_move, _) in enumerate(stockfish_moves, 1) if sf_move == expected_move)
            print(f"Expected move ranks #{rank}")

if __name__ == "__main__":
    test_puzzle_challenge_logic()
