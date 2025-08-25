#!/usr/bin/env python3
"""
V7P3R Time Testing Script

Tests V7P3R with different time allocations to find the optimal thinking time:
- Tests 5, 10, 20, 30, 45, and 60 seconds per puzzle
- Uses just 3 puzzles to keep testing quick
- Reports success rate and move quality for each time setting
- Helps determine V7P3R's optimal time allocation
"""

import os
import sys
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
    
    print("V7P3R Time Allocation Testing")
    print("=" * 50)
    print("Finding optimal thinking time for V7P3R...")
    print()
    
    # Create analyzer instance
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Test different time allocations
    time_tests = [5, 10, 20, 30, 45, 60]  # seconds
    
    # Get a consistent set of test puzzles
    print("🎯 Getting test puzzles...")
    sys.path.append(os.path.join(os.path.dirname(__file__), 'chess-puzzle-challenger', 'src'))
    from database import PuzzleDatabase
    db = PuzzleDatabase(analyzer.puzzle_db_path)
    test_puzzles = db.query_puzzles(
        themes=["middlegame", "opening"],  # Focus on V7P3R's strong areas
        min_rating=1200,
        max_rating=1800,  # Mid-level puzzles
        quantity=3
    )
    
    if not test_puzzles:
        print("❌ No test puzzles found!")
        sys.exit(1)
    
    print(f"Using {len(test_puzzles)} test puzzles:")
    for i, puzzle in enumerate(test_puzzles, 1):
        themes_str = puzzle.themes[:50] + "..." if len(puzzle.themes) > 50 else puzzle.themes
        print(f"  {i}. {puzzle.id} (Rating: {puzzle.rating}) - {themes_str}")
    print()
    
    # Run time tests
    results_by_time = {}
    
    for test_time in time_tests:
        print(f"⏱️ TESTING {test_time} SECOND TIME LIMIT")
        print("-" * 40)
        
        successes = 0
        total_scores = 0
        analysis_times = []
        
        for i, puzzle in enumerate(test_puzzles, 1):
            print(f"Puzzle {i}/3: {puzzle.id}")
            
            # Test V7P3R with this time limit
            start_time = time.time()
            v7p3r_move = analyzer.get_v7p3r_move(puzzle.fen, test_time)
            actual_time = time.time() - start_time
            analysis_times.append(actual_time)
            
            if v7p3r_move:
                print(f"  ✅ V7P3R returned: {v7p3r_move} (took {actual_time:.1f}s)")
                successes += 1
                
                # Quick Stockfish comparison
                stockfish_moves = analyzer.get_stockfish_top_moves(puzzle.fen, 5, 1.0)
                if stockfish_moves:
                    score, rank = analyzer.score_v7p3r_move(v7p3r_move, stockfish_moves)
                    total_scores += score
                    if rank > 0:
                        print(f"    📊 Ranked #{rank} by Stockfish - Score: {score}/5")
                    else:
                        print(f"    📊 Not in top 5 - Score: 0/5")
                else:
                    print(f"    ⚠️ Stockfish analysis failed")
            else:
                print(f"  ❌ V7P3R failed to return move (timeout after {actual_time:.1f}s)")
        
        # Calculate metrics for this time setting
        success_rate = (successes / len(test_puzzles)) * 100
        avg_score = total_scores / len(test_puzzles) if len(test_puzzles) > 0 else 0
        avg_time = sum(analysis_times) / len(analysis_times) if analysis_times else 0
        max_time = max(analysis_times) if analysis_times else 0
        
        results_by_time[test_time] = {
            'success_rate': success_rate,
            'average_score': avg_score,
            'average_time': avg_time,
            'max_time': max_time,
            'successes': successes,
            'total_puzzles': len(test_puzzles)
        }
        
        print(f"📈 Results for {test_time}s limit:")
        print(f"   Success Rate: {success_rate:.0f}% ({successes}/{len(test_puzzles)})")
        print(f"   Average Score: {avg_score:.1f}/5.0")
        print(f"   Average Time: {avg_time:.1f}s")
        print(f"   Max Time: {max_time:.1f}s")
        print()
    
    # Summary analysis
    print("=" * 60)
    print("📊 TIME ALLOCATION SUMMARY")
    print("=" * 60)
    
    print("Time Limit | Success Rate | Avg Score | Avg Time | Max Time")
    print("-" * 55)
    for test_time in time_tests:
        data = results_by_time[test_time]
        print(f"{test_time:8d}s | {data['success_rate']:10.0f}% | {data['average_score']:7.1f}/5 | {data['average_time']:6.1f}s | {data['max_time']:6.1f}s")
    
    # Find optimal time
    print(f"\n🎯 RECOMMENDATIONS:")
    
    # Find minimum time for 100% success rate
    min_reliable_time = None
    for test_time in time_tests:
        if results_by_time[test_time]['success_rate'] == 100:
            min_reliable_time = test_time
            break
    
    if min_reliable_time:
        print(f"✅ Minimum time for 100% success: {min_reliable_time} seconds")
        print(f"   Average actual time used: {results_by_time[min_reliable_time]['average_time']:.1f}s")
    else:
        # Find best success rate
        best_time = max(time_tests, key=lambda t: results_by_time[t]['success_rate'])
        best_rate = results_by_time[best_time]['success_rate']
        print(f"⚠️ No time limit achieved 100% success")
        print(f"   Best: {best_time}s with {best_rate:.0f}% success rate")
    
    # Find time with best score quality
    best_score_time = max(time_tests, key=lambda t: results_by_time[t]['average_score'])
    best_score = results_by_time[best_score_time]['average_score']
    print(f"🏆 Best average score: {best_score:.1f}/5.0 at {best_score_time}s")
    
    # Efficiency analysis
    efficient_times = []
    for test_time in time_tests:
        data = results_by_time[test_time]
        if data['success_rate'] == 100 and data['average_time'] < test_time * 0.8:
            efficient_times.append(test_time)
    
    if efficient_times:
        recommended_time = min(efficient_times)
        print(f"⚡ Recommended time: {recommended_time}s (reliable + efficient)")
    elif min_reliable_time:
        print(f"⚡ Recommended time: {min_reliable_time}s (minimum reliable)")
    else:
        print(f"⚡ Recommended time: {max(time_tests)}s+ (needs more time)")
    
    print(f"\n📝 NEXT STEPS:")
    if min_reliable_time and min_reliable_time <= 30:
        print(f"✅ V7P3R is ready for larger puzzle analysis with {min_reliable_time}s per puzzle")
    elif min_reliable_time:
        print(f"⚠️ V7P3R needs {min_reliable_time}s per puzzle - consider smaller batch sizes")
    else:
        print(f"🔧 V7P3R needs optimization - consider 60s+ per puzzle or investigate timeout issues")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("1. Make sure all engines are working")
    print("2. Try running check_setup.py first") 
    print("3. Check puzzle database access")
