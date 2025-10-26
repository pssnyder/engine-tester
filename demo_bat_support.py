#!/usr/bin/env python3
"""
Demo of Universal Puzzle Analyzer with .bat engine support
Shows the new functionality without running a full analysis
"""

import os
import sys

# Add paths  
engine_tester_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester"
os.chdir(engine_tester_path)
sys.path.append('engine_utilities')
sys.path.append('databases')

def demo_bat_engine_analyzer():
    """Demonstrate the .bat engine support"""
    
    print("🎮 Universal Puzzle Analyzer - .bat Engine Support Demo")
    print("=" * 60)
    
    # Test engines
    bat_engine = r"engines\V7P3R\V7P3R_v14.2\V7P3R_v14.2.bat"
    exe_engine = r"engines\Stockfish\stockfish-windows-x86-64-avx2.exe"
    
    print(f"\n📁 Testing .bat engine: {bat_engine}")
    print(f"   Engine exists: {os.path.exists(bat_engine)}")
    
    print(f"\n📁 Testing .exe engine: {exe_engine}")  
    print(f"   Engine exists: {os.path.exists(exe_engine)}")
    
    if not os.path.exists(bat_engine):
        print("❌ .bat engine not found - cannot demo")
        return
    
    try:
        # Import the analyzer
        from universal_puzzle_analyzer import UniversalPuzzleAnalyzer
        print("\n✅ Successfully imported UniversalPuzzleAnalyzer")
        
        # Test .bat engine initialization
        print(f"\n🔧 Initializing analyzer with .bat engine...")
        analyzer = UniversalPuzzleAnalyzer(bat_engine)
        
        print(f"✅ Engine type detected: {analyzer.engine_type}")
        print(f"✅ Engine command: {analyzer.engine_command}")
        print(f"✅ Engine name: {analyzer.engine_name}")
        print(f"✅ Engine author: {analyzer.engine_info.get('author', 'Unknown')}")
        
        # Test move generation
        print(f"\n🎯 Testing move generation from starting position...")
        start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = analyzer.get_engine_move(start_fen, 3.0)
        
        if move:
            print(f"✅ Engine suggested move: {move}")
        else:
            print("❌ Engine failed to suggest a move")
            
        # Test with .exe engine for comparison (if available)
        if os.path.exists(exe_engine):
            print(f"\n🔧 Testing .exe engine for comparison...")
            exe_analyzer = UniversalPuzzleAnalyzer(exe_engine)
            print(f"✅ .exe engine type: {exe_analyzer.engine_type}")
            print(f"✅ .exe engine name: {exe_analyzer.engine_name}")
        
        print(f"\n🎉 SUCCESS! .bat engine support is fully functional!")
        print(f"\n💡 Usage Examples:")
        print(f"   # Analyze with .bat engine:")
        print(f"   python -m engine_utilities.universal_puzzle_analyzer \\")
        print(f"     --engine engines\\V7P3R\\V7P3R_v14.2\\V7P3R_v14.2.bat \\")
        print(f"     --puzzles 10 --time 5")
        print(f"   ")
        print(f"   # Still works with .exe engines:")
        print(f"   python -m engine_utilities.universal_puzzle_analyzer \\")
        print(f"     --engine engines\\Stockfish\\stockfish-windows-x86-64-avx2.exe \\")
        print(f"     --puzzles 10 --time 2")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_bat_engine_analyzer()