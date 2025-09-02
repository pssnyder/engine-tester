#!/usr/bin/env python3
"""
Test the exact position from the PGN to see if we can reproduce the issue.
"""

import subprocess
import sys

def convert_pgn_to_uci_moves(pgn_moves):
    """Convert PGN notation to UCI moves (simplified conversion)."""
    # This is a basic conversion - for full accuracy we'd need a chess library
    uci_moves = []
    move_map = {
        "e4": "e2e4", "Nf6": "g8f6", "Bc4": "f1c4", "Nxe4": "f6e4",
        "Nh3": "g1h3", "d5": "d7d5", "Bd3": "c4d3", "Bxh3": "c8h3",
        "Bxe4": "d3e4", "dxe4": "d5e4", "gxh3": "g2h3", "Na6": "b8a6",
        "Nc3": "b1c3", "Qd4": "d8d4", "Nxe4": "c3e4"
    }
    
    for move in pgn_moves:
        if move in move_map:
            uci_moves.append(move_map[move])
        else:
            print(f"Warning: Could not convert PGN move: {move}")
    
    return uci_moves

def test_exact_tournament_position():
    """Test the exact position and move from the tournament."""
    engine_path = "engines/C0BR4/C0BR4_v2.6_FIXED.exe"
    
    # Exact PGN from the tournament up to the illegal move
    pgn_moves = ["e4", "Nf6", "Bc4", "Nxe4", "Nh3", "d5", "Bd3", "Bxh3", 
                 "Bxe4", "dxe4", "gxh3", "Na6", "Nc3", "Qd4", "Nxe4"]
    
    print("=== Testing Exact Tournament Position ===")
    print("PGN moves:", " ".join(pgn_moves))
    
    # Convert to UCI format
    uci_moves = convert_pgn_to_uci_moves(pgn_moves)
    print("UCI moves:", " ".join(uci_moves))
    
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
        
        # Set the exact position
        moves_str = " ".join(uci_moves)
        position_cmd = f"position startpos moves {moves_str}"
        print(f"Sending: {position_cmd}")
        
        process.stdin.write(f"{position_cmd}\n")
        process.stdin.flush()
        
        # Get all legal moves
        process.stdin.write("go perft 1\n")
        process.stdin.flush()
        
        legal_moves = []
        while True:
            line = process.stdout.readline().strip()
            print(f"Engine: {line}")
            if line.startswith("Nodes searched:") or "perft" in line.lower():
                break
            if ": " in line and not line.startswith("info"):
                move = line.split(":")[0].strip()
                if len(move) == 4:  # UCI move format
                    legal_moves.append(move)
        
        print(f"Legal moves from engine: {legal_moves}")
        
        # Check if d4e4 is in the legal moves
        if "d4e4" in legal_moves:
            print("✓ d4e4 (Qxe4+) IS in the legal moves list")
        else:
            print("✗ d4e4 (Qxe4+) is NOT in the legal moves list")
            print("This might explain why it was flagged as illegal!")
        
        # Test making the move explicitly
        print("\nTesting explicit move application:")
        process.stdin.write(f"{position_cmd} d4e4\n")
        process.stdin.flush()
        
        process.stdin.write("go movetime 100\n")
        process.stdin.flush()
        
        error_found = False
        while True:
            line = process.stdout.readline().strip()
            print(f"Engine after d4e4: {line}")
            if "error" in line.lower() or "illegal" in line.lower():
                error_found = True
            if line.startswith("bestmove"):
                break
        
        if error_found:
            print("ERROR: Engine reported error when trying to apply d4e4")
        else:
            print("Engine successfully applied d4e4")
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.wait(timeout=5)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_exact_tournament_position()
