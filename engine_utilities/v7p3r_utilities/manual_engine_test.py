#!/usr/bin/env python3
"""
Manual Engine Test
Direct test of V7P3R engine with manual commands
"""

import os
import sys

def main():
    print("=" * 60)
    print("MANUAL V7P3R ENGINE TEST")
    print("=" * 60)
    
    # Change to engine directory
    engine_dir = r"s:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine"
    
    if not os.path.exists(engine_dir):
        print(f"ERROR: Engine directory not found: {engine_dir}")
        return
    
    print(f"Engine directory: {engine_dir}")
    
    uci_file = os.path.join(engine_dir, "src", "v7p3r_uci.py")
    if not os.path.exists(uci_file):
        print(f"ERROR: UCI file not found: {uci_file}")
        return
    
    print(f"UCI file: {uci_file}")
    print()
    
    print("To manually test the engine:")
    print("1. Open a new terminal")
    print(f"2. Navigate to: {engine_dir}")
    print("3. Run: python src/v7p3r_uci.py")
    print("4. Type: uci")
    print("5. Type: position fen r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    print("6. Type: go movetime 3000")
    print("7. Wait for bestmove (should be Qxf7# or Qf7)")
    print("8. Type: quit")
    print()
    
    # Test positions for analysis
    positions = [
        ("Scholar's Mate Setup", "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"),
        ("King and Pawn Endgame", "8/8/8/8/8/3k4/3P4/3K4 w - - 0 1"),
        ("Tactical Position", "r2qkbnr/ppp1pppp/2n5/3p4/3P1Bb1/2N2N2/PPP1PPPP/R2QKB1R w KQkq - 4 5")
    ]
    
    print("Test Positions:")
    print("-" * 40)
    for i, (name, fen) in enumerate(positions, 1):
        print(f"{i}. {name}")
        print(f"   FEN: {fen}")
        print()
    
    print("Expected Results:")
    print("1. Scholar's Mate: Should find Qxf7# (checkmate)")
    print("2. King and Pawn: Should push the pawn (d3 or d4)")
    print("3. Tactical: Should develop or defend")
    print()
    
    print("Commands to create a quick test script:")
    print("-" * 40)
    
    test_script = f'''#!/bin/bash
cd "{engine_dir}"
echo "Testing V7P3R v9.1 Confidence System"
echo "=================================="

python -c "
import subprocess
import sys

def test_engine():
    process = subprocess.Popen(['python', 'src/v7p3r_uci.py'], 
                             stdin=subprocess.PIPE, 
                             stdout=subprocess.PIPE, 
                             text=True)
    
    # Test sequence
    commands = [
        'uci',
        'position fen r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
        'go movetime 3000',
        'quit'
    ]
    
    for cmd in commands:
        process.stdin.write(cmd + '\\\\n')
        process.stdin.flush()
        if cmd == 'go movetime 3000':
            # Wait for response
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                print(line.strip())
                if line.startswith('bestmove'):
                    break
        elif cmd == 'uci':
            # Wait for uciok
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                print(line.strip())
                if 'uciok' in line:
                    break

test_engine()
"
'''
    
    print(test_script)
    
    # Also save this script for easy use
    with open("manual_test_instructions.txt", "w") as f:
        f.write("V7P3R Engine Manual Test Instructions\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Engine Directory: {engine_dir}\n")
        f.write(f"UCI File: {uci_file}\n\n")
        f.write("Manual Test Steps:\n")
        f.write("1. Open terminal\n")
        f.write(f"2. cd \"{engine_dir}\"\n")
        f.write("3. python src/v7p3r_uci.py\n")
        f.write("4. uci\n")
        f.write("5. position fen r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4\n")
        f.write("6. go movetime 3000\n")
        f.write("7. quit\n\n")
        f.write("Expected: bestmove should be Qxf7 or similar (checkmate)\n")
    
    print("Instructions saved to: manual_test_instructions.txt")

if __name__ == "__main__":
    main()
