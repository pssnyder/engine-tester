#!/usr/bin/env python3
"""
Test script to verify PGN file access
"""
import chess.pgn
from pathlib import Path

def test_pgn_access():
    base_dir = Path("s:/Maker Stuff/Programming/Chess Engines/Copycat Chess AI/copycat_chess_engine")
    pgn_path = base_dir / "training_positions" / "games.pgn"
    
    print(f"Testing access to: {pgn_path}")
    print(f"File exists: {pgn_path.exists()}")
    
    if pgn_path.exists():
        with open(pgn_path, encoding='utf-8') as pgn_file:
            first_game = chess.pgn.read_game(pgn_file)
            if first_game:
                print("\nFirst game headers:")
                for header, value in first_game.headers.items():
                    print(f"{header}: {value}")
            else:
                print("No games found in PGN file")

if __name__ == "__main__":
    test_pgn_access()
