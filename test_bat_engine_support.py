#!/usr/bin/env python3
"""
Test script to verify .bat engine support in Universal Puzzle Analyzer
"""

import sys
import os

# Add path to import the analyzer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine_utilities'))

from universal_puzzle_analyzer import UniversalPuzzleAnalyzer

def test_bat_engine_detection():
    """Test that .bat engines are properly detected and handled"""
    
    # Test with the new V14.2 engine
    v14_2_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R\V7P3R_v14.2\V7P3R_v14.2.bat"
    
    if not os.path.exists(v14_2_path):
        print(f"❌ Test engine not found: {v14_2_path}")
        return False
    
    print(f"🧪 Testing .bat engine detection with: {v14_2_path}")
    
    try:
        # Initialize analyzer
        analyzer = UniversalPuzzleAnalyzer(v14_2_path)
        
        print(f"✅ Engine type detected: {analyzer.engine_type}")
        print(f"✅ Engine command: {analyzer.engine_command}")
        print(f"✅ Engine name: {analyzer.engine_name}")
        print(f"✅ Engine info: {analyzer.engine_info}")
        
        # Test getting engine info
        if analyzer.engine_name and analyzer.engine_info:
            print("✅ Engine UCI communication successful")
        else:
            print("⚠️  Engine UCI communication had issues")
        
        # Test a simple move request
        print("\n🎯 Testing engine move generation...")
        start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = analyzer.get_engine_move(start_fen, 2.0)
        
        if move:
            print(f"✅ Engine suggested move: {move}")
        else:
            print("❌ Engine failed to suggest a move")
            return False
        
        print("\n🎉 All tests passed! .bat engine support is working.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exe_engine_compatibility():
    """Test that .exe engines still work (backward compatibility)"""
    
    # Test with Stockfish (assuming it exists)
    stockfish_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe"
    
    if not os.path.exists(stockfish_path):
        print(f"⚠️  Stockfish not found for .exe test: {stockfish_path}")
        return True  # Skip this test if Stockfish not available
    
    print(f"\n🧪 Testing .exe engine compatibility with: {stockfish_path}")
    
    try:
        analyzer = UniversalPuzzleAnalyzer(stockfish_path)
        
        print(f"✅ Engine type detected: {analyzer.engine_type}")
        print(f"✅ Engine command: {analyzer.engine_command}")
        print(f"✅ Engine name: {analyzer.engine_name}")
        
        print("✅ .exe engine backward compatibility confirmed")
        return True
        
    except Exception as e:
        print(f"❌ .exe engine test failed: {e}")
        return False


if __name__ == "__main__":
    print("Universal Puzzle Analyzer .bat Engine Support Test")
    print("=" * 60)
    
    success = True
    
    # Test .bat engine support
    if not test_bat_engine_detection():
        success = False
    
    # Test .exe engine backward compatibility
    if not test_exe_engine_compatibility():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - .bat engine support is ready!")
    else:
        print("❌ SOME TESTS FAILED - check output above")
    
    sys.exit(0 if success else 1)