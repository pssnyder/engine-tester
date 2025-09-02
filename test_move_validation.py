#!/usr/bin/env python3
"""
Test script to validate move generation vs move validation.
Check if the engine can generate illegal moves that it then considers valid.
"""

import subprocess
import sys
import time

def test_move_validation(engine_path, fen_position, test_move):
    """Test if a specific move is considered legal by the engine."""
    print(f"Testing move validation for: {test_move}")
    print(f"Position: {fen_position}")
    
    try:
        # Start the engine
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send UCI initialization
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Read until uciok
        while True:
            line = process.stdout.readline().strip()
            if line == "uciok":
                break
            if not line:
                break
        
        # Send isready
        process.stdin.write("isready\n")
        process.stdin.flush()
        
        # Read until readyok
        while True:
            line = process.stdout.readline().strip()
            if line == "readyok":
                break
            if not line:
                break
        
        # Set position
        process.stdin.write(f"position fen {fen_position}\n")
        process.stdin.flush()
        
        # Try to make the move
        process.stdin.write(f"position fen {fen_position} moves {test_move}\n")
        process.stdin.flush()
        
        # Request best move to see if position is valid
        process.stdin.write("go movetime 100\n")
        process.stdin.flush()
        
        # Read engine response
        valid = True
        error_msg = None
        while True:
            line = process.stdout.readline().strip()
            if line.startswith("bestmove"):
                break
            if line.startswith("info string Error") or "illegal" in line.lower():
                valid = False
                error_msg = line
                break
            if not line:
                break
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=5)
        
        return valid, error_msg
        
    except Exception as e:
        print(f"Error testing move validation: {e}")
        return False, str(e)

def main():
    """Test move validation scenarios."""
    engine_path = "engines/C0BR4/C0BR4_v2.6_FIXED.exe"
    
    # Test the position from the tournament where Qxe4+ was flagged as illegal
    # Position after: 1. e4 Nf6 2. Bc4 Nxe4 3. Nh3 d5 4. Bd3 Bxh3 5. Bxe4 dxe4 6. gxh3 Na6 7. Nc3 Qd4 8. Nxe4
    test_fen = "r3k2r/ppp1pppp/n7/8/3qN3/7P/PPPP1P1P/R1BQKB1R b KQkq - 0 8"
    
    print("=== Testing Move Validation ===")
    print("Testing the tournament position where Qxe4+ was flagged as illegal")
    print()
    
    # Test the supposedly illegal move
    valid, error = test_move_validation(engine_path, test_fen, "d4e4")
    
    if valid:
        print("Engine considers d4e4 (Qxe4+) as VALID")
        print("This suggests the tournament software incorrectly flagged it as illegal!")
    else:
        print("Engine considers d4e4 (Qxe4+) as INVALID")
        print(f"Error: {error}")
    
    # Test some obviously legal moves for comparison
    print("\nTesting obviously legal moves for comparison:")
    moves_to_test = ["d4a4", "d4b4", "d4c4", "d4d3", "d4d2", "d4d1"]
    
    for move in moves_to_test:
        valid, error = test_move_validation(engine_path, test_fen, move)
        status = "VALID" if valid else "INVALID"
        print(f"  {move}: {status}")
        if not valid and error:
            print(f"    Error: {error}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
