#!/usr/bin/env python3
"""
Quick validation script to check if the V7P3R analysis tools can find all necessary files
"""

import os
from pathlib import Path

def check_path(path, description):
    """Check if a path exists and report"""
    if os.path.exists(path):
        if os.path.isdir(path):
            files = list(os.listdir(path))
            print(f"✅ {description}: {path} ({len(files)} items)")
            return True
        else:
            print(f"✅ {description}: {path} (file exists)")
            return True
    else:
        print(f"❌ {description}: {path} (not found)")
        return False

def main():
    print("🔍 V7P3R v11 Analysis Tools - Environment Check")
    print("="*60)
    
    # Default paths
    base_engine_playground = r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground"
    
    paths_to_check = [
        (
            os.path.join(base_engine_playground, "engine-metrics", "game_records"),
            "PGN game records directory"
        ),
        (
            os.path.join(base_engine_playground, "engine-tester", "engines", "V7P3R"),
            "V7P3R engines directory"
        ),
        (
            os.path.join(base_engine_playground, "engine-tester", "downloaded_engines", "stockfish", "stockfish.exe"),
            "Stockfish executable"
        ),
        (
            r"s:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\src\v7p3r_utilities",
            "V7P3R utilities directory"
        )
    ]
    
    all_good = True
    for path, description in paths_to_check:
        if not check_path(path, description):
            all_good = False
    
    print("\n" + "="*60)
    
    if all_good:
        print("🎉 All paths found! Ready to run V7P3R v11 analysis.")
        print("\n📋 Quick start commands:")
        print("cd src/v7p3r_utilities")
        print("python run_v11_analysis.py --mode both")
    else:
        print("⚠️  Some paths missing. You may need to adjust paths when running analysis.")
        print("\n📋 Manual path specification:")
        print("python run_v11_analysis.py \\")
        print("  --pgn-dir 'path/to/pgn/files' \\")
        print("  --stockfish-path 'path/to/stockfish.exe' \\")
        print("  --engine-dir 'path/to/v7p3r/engines'")
    
    # Check specific contents
    print("\n🔍 Detailed Content Check:")
    
    # Check for V7P3R engines
    v7p3r_dir = os.path.join(base_engine_playground, "engine-tester", "engines", "V7P3R")
    if os.path.exists(v7p3r_dir):
        v7p3r_engines = [f for f in os.listdir(v7p3r_dir) if f.startswith('V7P3R_') and f.endswith('.exe')]
        print(f"📁 V7P3R engines found: {len(v7p3r_engines)}")
        for engine in sorted(v7p3r_engines)[:5]:  # Show first 5
            print(f"   - {engine}")
        if len(v7p3r_engines) > 5:
            print(f"   ... and {len(v7p3r_engines) - 5} more")
    
    # Check for recent PGN files
    pgn_dir = os.path.join(base_engine_playground, "engine-metrics", "game_records")
    if os.path.exists(pgn_dir):
        recent_dirs = sorted([d for d in os.listdir(pgn_dir) if d.startswith('Engine Battle')])[-5:]
        print(f"\n📁 Recent game record directories: {len(recent_dirs)}")
        for directory in recent_dirs:
            pgn_file = os.path.join(pgn_dir, directory, f"{directory}.pgn")
            if os.path.exists(pgn_file):
                file_size = os.path.getsize(pgn_file) // 1024  # KB
                print(f"   - {directory}: {file_size} KB")

if __name__ == "__main__":
    main()
