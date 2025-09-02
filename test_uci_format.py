#!/usr/bin/env python3
"""
Test C0BR4's UCI move format output to see if there are parsing issues.
"""

import subprocess
import sys

def test_uci_move_format():
    """Test what format C0BR4 outputs moves in."""
    engine_path = "engines/C0BR4/C0BR4_v2.6_FIXED.exe"
    
    print("=== Testing C0BR4 UCI Move Format ===")
    
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
        
        # Test starting position
        print("Testing starting position moves:")
        process.stdin.write("position startpos\n")
        process.stdin.flush()
        
        process.stdin.write("go movetime 100\n")
        process.stdin.flush()
        
        while True:
            line = process.stdout.readline().strip()
            print(f"Engine: {line}")
            if line.startswith("bestmove"):
                move = line.split()[1] if len(line.split()) > 1 else "NONE"
                print(f"Best move format: '{move}' (length: {len(move)})")
                break
        
        # Test a few different positions to see move format patterns
        test_positions = [
            ("position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "After 1.e4"),
            ("position fen rnbqkb1r/pppp1ppp/5n2/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 2 3", "After 1.e4 e5 2...Nf6"),
        ]
        
        for pos_cmd, desc in test_positions:
            print(f"\nTesting {desc}:")
            process.stdin.write(f"{pos_cmd}\n")
            process.stdin.flush()
            
            process.stdin.write("go movetime 100\n")
            process.stdin.flush()
            
            while True:
                line = process.stdout.readline().strip()
                if line.startswith("bestmove"):
                    move = line.split()[1] if len(line.split()) > 1 else "NONE"
                    print(f"  Best move: '{move}' (length: {len(move)})")
                    
                    # Check for common UCI format issues
                    if len(move) != 4 and len(move) != 5:  # 5 for promotion
                        print(f"  WARNING: Unusual move length: {len(move)}")
                    
                    if not move[0:2].isalnum() or not move[2:4].isalnum():
                        print(f"  WARNING: Move format doesn't match UCI standard")
                    
                    break
        
        # Test perft to see move list format
        print(f"\nTesting perft move list format:")
        process.stdin.write("position startpos\n")
        process.stdin.flush()
        
        process.stdin.write("go perft 1\n")
        process.stdin.flush()
        
        move_count = 0
        while True:
            line = process.stdout.readline().strip()
            if ": " in line and not line.startswith("info"):
                move = line.split(":")[0].strip()
                if len(move) == 4:  # Standard UCI move
                    move_count += 1
                    if move_count <= 5:  # Show first 5 moves
                        print(f"  Perft move: '{move}'")
            elif "Nodes searched:" in line or "perft" in line.lower():
                break
        
        print(f"  Total perft moves found: {move_count}")
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=5)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_uci_move_format()
