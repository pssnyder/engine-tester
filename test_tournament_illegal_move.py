#!/usr/bin/env python3
"""
Test script to reproduce the illegal move from the tournament.
Game 1: After 8. Nxe4, C0BR4 played Qxe4+ which was flagged as illegal.
"""

import subprocess
import sys
import time

def test_engine_move(engine_path, moves_sequence, expected_illegal_move=None):
    """Test engine with a specific move sequence."""
    print(f"Testing engine: {engine_path}")
    print(f"Move sequence: {' '.join(moves_sequence)}")
    
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
            print(f"Engine: {line}")
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
            print(f"Engine: {line}")
            if line == "readyok":
                break
            if not line:
                break
        
        # Start new game
        process.stdin.write("ucinewgame\n")
        process.stdin.flush()
        
        # Set position with moves
        position_cmd = "position startpos"
        if moves_sequence:
            position_cmd += f" moves {' '.join(moves_sequence)}"
        
        print(f"Sending: {position_cmd}")
        process.stdin.write(f"{position_cmd}\n")
        process.stdin.flush()
        
        # Request best move
        print("Sending: go movetime 1000")
        process.stdin.write("go movetime 1000\n")
        process.stdin.flush()
        
        # Read engine response
        best_move = None
        while True:
            line = process.stdout.readline().strip()
            print(f"Engine: {line}")
            if line.startswith("bestmove"):
                best_move = line.split()[1] if len(line.split()) > 1 else None
                break
            if not line:
                break
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=5)
        
        print(f"Engine returned best move: {best_move}")
        
        if expected_illegal_move and best_move == expected_illegal_move:
            print(f"WARNING: Engine returned the expected illegal move: {best_move}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error testing engine: {e}")
        return False

def main():
    """Test the specific tournament scenario."""
    engine_path = "engines/C0BR4/C0BR4_v2.6_FIXED.exe"
    
    # Game 1 sequence up to the illegal move
    # 1. e4 Nf6 2. Bc4 Nxe4 3. Nh3 d5 4. Bd3 Bxh3 5. Bxe4 dxe4 6. gxh3 Na6 7. Nc3 Qd4 8. Nxe4
    # After this, C0BR4 played Qxe4+ which was flagged as illegal
    moves_sequence = [
        "e2e4", "g8f6", "f1c4", "f6e4", "g1h3", "d7d5", 
        "c4d3", "c8h3", "d3e4", "d5e4", "g2h3", "b8a6", 
        "b1c3", "d8d4", "c3e4"
    ]
    
    print("=== Testing Tournament Illegal Move Scenario ===")
    print("Position after: 1. e4 Nf6 2. Bc4 Nxe4 3. Nh3 d5 4. Bd3 Bxh3 5. Bxe4 dxe4 6. gxh3 Na6 7. Nc3 Qd4 8. Nxe4")
    print("Tournament showed C0BR4 played Qxe4+ (illegal)")
    print()
    
    success = test_engine_move(engine_path, moves_sequence, "d4e4")
    
    if not success:
        print("CRITICAL: Engine reproduced the illegal move!")
        return 1
    else:
        print("Engine did not reproduce the illegal move in this test")
        return 0

if __name__ == "__main__":
    sys.exit(main())
