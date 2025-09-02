#!/usr/bin/env python3
"""
Test C0BR4 against external validation using python-chess library.
This will help us identify if C0BR4 is generating truly illegal moves.
"""

import subprocess
import sys
import time

try:
    import chess
    import chess.engine
except ImportError:
    print("This test requires python-chess library. Install with: pip install python-chess")
    sys.exit(1)

def test_move_legality_comparison():
    """Compare C0BR4's move generation with python-chess for validation."""
    engine_path = "engines/C0BR4/C0BR4_v2.6_FIXED.exe"
    
    # Test positions from the tournament where illegal moves occurred
    test_positions = [
        {
            "fen": "rnbqkbnr/pppp1ppp/8/4p3/3nP3/7P/PPPP1P1P/RNBQKBNR w KQkq - 1 9",
            "description": "Position after 8...Qxe4+ (claimed illegal in tournament)",
        },
        {
            "fen": "r3k2r/ppp1pppp/n7/8/3qN3/7P/PPPP1P1P/R1BQKB1R b KQkq - 0 8",
            "description": "Position where d4e4 (Qxe4+) was flagged as illegal",
        }
    ]
    
    print("=== Comparing C0BR4 vs Python-Chess Move Legality ===")
    
    for test_case in test_positions:
        fen = test_case["fen"]
        desc = test_case["description"]
        
        print(f"\nTesting: {desc}")
        print(f"FEN: {fen}")
        
        # Get legal moves from python-chess
        board = chess.Board(fen)
        python_legal_moves = set()
        for move in board.legal_moves:
            python_legal_moves.add(str(move))
        
        print(f"Python-chess legal moves ({len(python_legal_moves)}):")
        for move in sorted(python_legal_moves):
            print(f"  {move}")
        
        # Get legal moves from C0BR4
        c0br4_moves = get_c0br4_moves(engine_path, fen)
        
        print(f"C0BR4 legal moves ({len(c0br4_moves)}):")
        for move in sorted(c0br4_moves):
            print(f"  {move}")
        
        # Compare the move sets
        python_only = python_legal_moves - set(c0br4_moves)
        c0br4_only = set(c0br4_moves) - python_legal_moves
        common_moves = python_legal_moves & set(c0br4_moves)
        
        print(f"\nComparison:")
        print(f"  Common moves: {len(common_moves)}")
        print(f"  Python-chess only: {len(python_only)}")
        if python_only:
            for move in sorted(python_only):
                print(f"    {move}")
        
        print(f"  C0BR4 only (POTENTIALLY ILLEGAL): {len(c0br4_only)}")
        if c0br4_only:
            for move in sorted(c0br4_only):
                print(f"    {move} *** POTENTIALLY ILLEGAL ***")
        
        # Check specifically for the moves that were flagged in tournament
        problem_moves = ["d4e4", "d8e4"]  # Common patterns from tournament
        for move in problem_moves:
            if move in c0br4_moves and move not in python_legal_moves:
                print(f"  *** CONFIRMED ILLEGAL MOVE: {move} ***")
            elif move in python_legal_moves and move in c0br4_moves:
                print(f"  Move {move} is legal according to both engines")

def get_c0br4_moves(engine_path, fen):
    """Get list of legal moves from C0BR4 engine."""
    try:
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # UCI initialization
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        while True:
            line = process.stdout.readline().strip()
            if line == "uciok":
                break
        
        process.stdin.write("isready\n")
        process.stdin.flush()
        
        while True:
            line = process.stdout.readline().strip()
            if line == "readyok":
                break
        
        # Set position
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        # Get moves using perft 1
        process.stdin.write("go perft 1\n")
        process.stdin.flush()
        
        moves = []
        while True:
            line = process.stdout.readline().strip()
            if ": " in line and not line.startswith("info"):
                move = line.split(":")[0].strip()
                if len(move) >= 4:  # UCI move format
                    moves.append(move)
            elif "Nodes searched:" in line or "perft" in line.lower():
                break
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=5)
        
        return moves
        
    except Exception as e:
        print(f"Error getting C0BR4 moves: {e}")
        return []

if __name__ == "__main__":
    test_move_legality_comparison()
