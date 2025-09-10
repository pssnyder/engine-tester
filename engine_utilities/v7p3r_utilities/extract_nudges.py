#!/usr/bin/env python3
"""
Simple runner for V7P3R nudge extraction
"""

import os
import subprocess
import sys

def main():
    """Run nudge extraction with default paths"""
    
    # Default paths for your environment
    pgn_dir = r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-metrics\game_records"
    stockfish_path = r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\downloaded_engines\stockfish\stockfish-windows-x86-64-avx2.exe"
    
    print("🚀 V7P3R Nudge Extractor - Quick Run")
    print("="*40)
    print(f"PGN Directory: {pgn_dir}")
    print(f"Stockfish: {stockfish_path}")
    print()
    
    # Check if paths exist
    if not os.path.exists(pgn_dir):
        print(f"❌ PGN directory not found: {pgn_dir}")
        return 1
    
    if not os.path.exists(stockfish_path):
        print(f"❌ Stockfish not found: {stockfish_path}")
        return 1
    
    # Run extraction
    cmd = [
        sys.executable,
        "quick_nudge_extractor.py",
        "--pgn-dir", pgn_dir,
        "--stockfish", stockfish_path,
        "--output", "v7p3r_nudge_database.json",
        "--min-frequency", "3"  # Only positions that occur 3+ times
    ]
    
    print("🏃 Running extraction...")
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Nudge extraction complete!")
        print("📁 Output: v7p3r_nudge_database.json")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Extraction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
