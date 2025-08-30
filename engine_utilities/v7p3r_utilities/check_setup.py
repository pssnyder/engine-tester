#!/usr/bin/env python3
"""
Environment Setup Verification for V7P3R Puzzle Analyzer

Check that all required components are available before running analysis
"""

import os
import subprocess
import sys

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists and report result"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    if not exists:
        print(f"    File not found!")
    return exists

def check_engine_uci(engine_path: str, engine_name: str) -> bool:
    """Test if an engine responds to UCI commands"""
    try:
        print(f"Testing {engine_name} UCI interface...")
        process = subprocess.Popen(
            engine_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        
        # Send UCI command
        stdout, stderr = process.communicate(input="uci\nquit\n", timeout=5)
        
        if "uciok" in stdout:
            print(f"✅ {engine_name} UCI interface working")
            return True
        else:
            print(f"❌ {engine_name} UCI interface not responding properly")
            print(f"    stdout: {stdout[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ {engine_name} UCI test failed: {e}")
        return False

def main():
    print("V7P3R Puzzle Analyzer - Environment Check")
    print("=" * 60)
    
    # Define paths
    v7p3r_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R\V7P3R_v7.0.exe"
    stockfish_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe"
    puzzle_db_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\chess-puzzle-challenger\puzzles.db"
    database_module = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\chess-puzzle-challenger\src\database.py"
    
    print("\n1. Checking file existence:")
    all_files_exist = True
    all_files_exist &= check_file_exists(v7p3r_path, "V7P3R Engine")
    all_files_exist &= check_file_exists(stockfish_path, "Stockfish Engine")
    all_files_exist &= check_file_exists(puzzle_db_path, "Puzzle Database")
    all_files_exist &= check_file_exists(database_module, "Database Module")
    
    if not all_files_exist:
        print("\n❌ Some required files are missing!")
        print("\nTo fix this:")
        print("1. Make sure puzzle database exists (run puzzle importer if needed)")
        print("2. Verify engine paths are correct")
        return False
    
    print("\n2. Testing engine UCI interfaces:")
    engines_working = True
    engines_working &= check_engine_uci(v7p3r_path, "V7P3R")
    engines_working &= check_engine_uci(stockfish_path, "Stockfish")
    
    if not engines_working:
        print("\n❌ Engine UCI interfaces not working properly!")
        return False
    
    print("\n3. Testing Python imports:")
    try:
        import chess
        import chess.engine
        print("✅ python-chess library available")
    except ImportError:
        print("❌ python-chess library not available")
        print("    Install with: pip install python-chess")
        return False
    
    # Test database import
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'chess-puzzle-challenger', 'src'))
        from database import PuzzleDatabase, Puzzle
        print("✅ Puzzle database module available")
        
        # Test database connection
        db = PuzzleDatabase(puzzle_db_path)
        test_puzzles = db.query_puzzles(quantity=1)
        if test_puzzles:
            print(f"✅ Puzzle database accessible ({len(test_puzzles)} test puzzle found)")
        else:
            print("⚠️ Puzzle database empty or no puzzles match criteria")
            
    except Exception as e:
        print(f"❌ Puzzle database module error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Environment check passed! Ready to run V7P3R Puzzle Analyzer")
    print("\nTo run the analyzer:")
    print("  python test_v7p3r_analyzer.py     # Quick 5-puzzle test")
    print("  python v7p3r_puzzle_analyzer.py  # Full 100-puzzle analysis")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
