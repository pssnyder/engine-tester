#!/usr/bin/env python3
"""
Magic Bitboard Verification Test
===============================
This tests if C0BR4's magic bitboards are generating correct rook attacks
by comparing with known correct implementations.
"""

import chess
import subprocess
import sys
from pathlib import Path

def test_rook_attacks_position(engine_path: str, fen: str, square_name: str):
    """Test rook attacks from a specific square in a position."""
    
    print(f"\n🔍 Testing rook attacks from {square_name}")
    print(f"Position: {fen}")
    
    # Parse with python-chess for reference
    board = chess.Board(fen)
    square = chess.parse_square(square_name)
    
    # Get python-chess rook attacks
    piece_at_square = board.piece_at(square)
    if piece_at_square is None or piece_at_square.piece_type != chess.ROOK:
        print(f"❌ No rook at {square_name}")
        return
        
    # Get attacks using python-chess
    occupancy = board.occupied
    python_attacks = chess.BB_RANK_ATTACKS[square][chess.BB_RANK_MASKS[square] & occupancy] | \
                    chess.BB_FILE_ATTACKS[square][chess.BB_FILE_MASKS[square] & occupancy]
    
    python_attack_squares = []
    for target_square in chess.SQUARES:
        if python_attacks & chess.BB_SQUARES[target_square]:
            python_attack_squares.append(chess.square_name(target_square))
    
    print(f"✅ Python-chess rook attacks from {square_name}: {sorted(python_attack_squares)}")
    
    # Now test with C0BR4 debug mode
    try:
        process = subprocess.Popen(
            [engine_path, "debug-rook", square_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send position
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.write("quit\n")
        process.stdin.flush()
        
        stdout, stderr = process.communicate(timeout=10)
        
        print(f"C0BR4 debug output:")
        print(stdout)
        if stderr:
            print(f"C0BR4 stderr: {stderr}")
            
    except Exception as e:
        print(f"❌ Error testing C0BR4: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python magic_bitboard_test.py <engine_path>")
        sys.exit(1)
    
    engine_path = sys.argv[1]
    
    if not Path(engine_path).exists():
        print(f"❌ Engine not found: {engine_path}")
        sys.exit(1)
    
    print("🧪 Magic Bitboard Verification Test")
    print("=" * 50)
    
    # Test the problematic positions
    test_cases = [
        {
            'fen': 'r6r/pp2kb2/3p1p2/1N1Pp3/3bP3/P2B2P1/1P1Q2PP/7K b - - 7 28',
            'square': 'h8',
            'description': 'Position where C0BR4 played illegal h8h1'
        },
        {
            'fen': '8/5p1k/5Ppb/2p3P1/qp6/8/KB5Q/8 w - - 5 59',
            'square': 'a2', 
            'description': 'Position where C0BR4 played illegal a2a1'
        },
        {
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'square': 'a1',
            'description': 'Starting position rook test'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['description']}")
        test_rook_attacks_position(engine_path, test_case['fen'], test_case['square'])

if __name__ == "__main__":
    main()
