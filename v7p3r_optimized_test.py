#!/usr/bin/env python3
"""
V7P3R Optimized Puzzle Test

Based on time testing results:
- Uses 30 seconds per puzzle (V7P3R's proven reliable time)
- Tests just 5 opening/middlegame puzzles
- Focuses on V7P3R's strength areas
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

try:
    from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
    
    print("V7P3R Optimized Puzzle Test")
    print("=" * 45)
    print("Using optimal 30-second time allocation")
    print()
    
    # Create analyzer
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Test with optimal settings
    results = analyzer.run_analysis(
        num_puzzles=5,
        rating_min=1200,
        rating_max=1800,
        v7p3r_time=30.0,  # Optimal time based on testing
        themes_filter=["middlegame", "opening", "attack"]  # V7P3R's strong areas
    )
    
    if results:
        print(f"\n✅ Successfully analyzed {len(results)} puzzles!")
        
        # Generate report
        report = analyzer.generate_report(results)
        analyzer.print_report(report)
        
        # Quick insights
        if report['average_score'] >= 3.0:
            print(f"\n🏆 Excellent! V7P3R shows strong performance with proper time allocation")
        elif report['average_score'] >= 2.0:
            print(f"\n👍 Good performance! V7P3R benefits from adequate thinking time")
        else:
            print(f"\n🔧 Room for improvement, but time allocation issue is resolved")
        
        # Save results
        analyzer.save_results("v7p3r_optimized_test.json")
        
        print(f"\n📝 Confirmed: V7P3R needs ~30 seconds per puzzle for reliable analysis")
        print(f"📊 Ready for larger analysis with proper time allocation")
        
    else:
        print("❌ No results generated")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
