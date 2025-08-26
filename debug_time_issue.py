#!/usr/bin/env python3
"""
Debug V7P3R Time Issue

Test the specific position that's failing to see if it's position-dependent
"""

import os
import sys
import time

sys.path.append(os.path.dirname(__file__))

try:
    from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
    
    print("Debugging V7P3R Time Issue")
    print("=" * 40)
    
    # Create analyzer
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Test the failing position from the analysis
    failing_fen = "1qr2rk1/pb2bppp/8/8/2p1N3/P1Bn2P1/2Q2PBP/1R3RK1 b - - 3 23"
    print(f"Testing failing position: {failing_fen}")
    print()
    
    # Test with different time limits on this specific position
    time_limits = [20, 25, 30, 35, 40, 45]
    
    print("Time | Result     | Actual Time")
    print("-" * 35)
    
    for time_limit in time_limits:
        print(f"{time_limit:3d}s | ", end="", flush=True)
        
        start_time = time.time()
        move = analyzer.get_v7p3r_move(failing_fen, time_limit)
        actual_time = time.time() - start_time
        
        if move:
            print(f"{move:8s} | {actual_time:8.1f}s")
        else:
            print(f"{'TIMEOUT':8s} | {actual_time:8.1f}s")
        
        # Brief pause between tests
        time.sleep(1)
    
    print()
    print("Compare with our known working position:")
    working_fen = "r4rk1/pp3ppp/2n1b3/q1pp2B1/8/P1Q2NP1/1PP1PP1P/2KR3R w - - 0 15"
    
    print(f"Working position: {working_fen}")
    start_time = time.time()
    move = analyzer.get_v7p3r_move(working_fen, 30)
    actual_time = time.time() - start_time
    print(f"30s test: {move} in {actual_time:.1f}s")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
