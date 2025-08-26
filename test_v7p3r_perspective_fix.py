#!/usr/bin/env python3
"""
Test V7P3R Perspective Fix

Verify that V7P3R now evaluates positions correctly from its own perspective
"""

import sys
import os
sys.path.append(r"S:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\src")

import chess
from v7p3r import V7P3RCleanEngine

def test_perspective_fix():
    """Test the perspective fix"""
    engine = V7P3RCleanEngine()
    
    print("Testing V7P3R Perspective Fix")
    print("=" * 50)
    
    # Test starting position as White
    board = chess.Board()
    print("Testing as WHITE from starting position:")
    print(f"Position: {board.fen()}")
    print(f"Turn: {board.turn} ({'White' if board.turn else 'Black'})")
    
    # Get evaluation
    score = engine._evaluate_position(board, board.turn)
    print(f"V7P3R evaluation: {score:.2f}")
    print(f"Should be positive (favoring White) or near 0")
    
    print()
    
    # Test starting position as Black (after 1.e4)
    board.push_san("e4")
    print("Testing as BLACK after 1.e4:")
    print(f"Position: {board.fen()}")
    print(f"Turn: {board.turn} ({'White' if board.turn else 'Black'})")
    
    # Get evaluation from Black's perspective
    score = engine._evaluate_position(board, board.turn)
    print(f"V7P3R evaluation: {score:.2f}")
    print(f"Should be reasonable (slightly negative for Black)")
    
    print()
    
    # Test a position where White is clearly better
    board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 4 4")
    print("Testing position where White is better:")
    print(f"Position: {board.fen()}")
    print(f"Turn: {board.turn} ({'White' if board.turn else 'Black'})")
    
    # White's evaluation
    score_white = engine._evaluate_position(board, chess.WHITE)
    print(f"From White's perspective: {score_white:.2f} (should be positive)")
    
    # Black's evaluation
    score_black = engine._evaluate_position(board, chess.BLACK)
    print(f"From Black's perspective: {score_black:.2f} (should be negative)")
    
    print()
    print("✅ If White perspective is positive and Black perspective is negative")
    print("   for the same position, the fix is working correctly!")
    
    # Test actual search with UCI output
    print("\n" + "=" * 50)
    print("Testing UCI output (should show reasonable evaluations):")
    print("=" * 50)
    
    # Test as White
    board = chess.Board()
    print("\nAs WHITE on starting position:")
    move = engine.search(board, 2.0)
    print(f"Best move: {move}")
    
    # Test as Black
    board.push_san("e4")
    print(f"\nAs BLACK after 1.e4:")
    move = engine.search(board, 2.0)
    print(f"Best move: {move}")

if __name__ == "__main__":
    test_perspective_fix()
