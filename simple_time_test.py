#!/usr/bin/env python3
"""
Simple V7P3R Time Test

Tests V7P3R with different time allocations on a single puzzle
to quickly determine optimal thinking time.
"""

import os
import sys
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
    
    print("V7P3R Simple Time Test")
    print("=" * 40)
    
    # Create analyzer
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Use a specific test position (middlegame tactical)
    test_fen = "r4rk1/pp3ppp/2n1b3/q1pp2B1/8/P1Q2NP1/1PP1PP1P/2KR3R w - - 0 15"
    print(f"Test position: {test_fen}")
    print()
    
    # Test different time limits
    time_limits = [5, 10, 15, 20, 30, 45, 60]
    
    print("Testing V7P3R with different time limits:")
    print("Time | Result     | Actual Time")
    print("-" * 35)
    
    for time_limit in time_limits:
        print(f"{time_limit:3d}s | ", end="", flush=True)
        
        start_time = time.time()
        move = analyzer.get_v7p3r_move(test_fen, time_limit)
        actual_time = time.time() - start_time
        
        if move:
            print(f"{move:8s} | {actual_time:8.1f}s")
        else:
            print(f"{'TIMEOUT':8s} | {actual_time:8.1f}s")
        
        # Brief pause between tests
        time.sleep(1)
    
    print()
    print("Now test with Stockfish for comparison:")
    
    try:
        stockfish_moves = analyzer.get_stockfish_top_moves(test_fen, 5, 2.0)
        if stockfish_moves:
            print("Stockfish top 5 moves:")
            for i, (move, score) in enumerate(stockfish_moves, 1):
                print(f"  {i}. {move} (score: {score:+d})")
        else:
            print("❌ Stockfish analysis failed")
    except Exception as e:
        print(f"❌ Stockfish error: {e}")
    
    print("\n📝 Quick Test Recommendations:")
    print("- If V7P3R consistently times out at low times, increase gradually")
    print("- If V7P3R returns moves quickly, it may not need as much time")
    print("- Compare V7P3R's moves against Stockfish's top moves")
    print("- Look for the sweet spot where V7P3R returns good moves reliably")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
