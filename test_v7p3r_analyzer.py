#!/usr/bin/env python3
"""
Simple test runner for V7P3R Puzzle Analyzer

Run a quick test with a small number of puzzles to verify everything works
"""

import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
    
    print("V7P3R Puzzle Analyzer - Quick Test")
    print("=" * 50)
    
    # Create analyzer instance
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Run a small test with just 5 puzzles
    print("Running test with 5 puzzles...")
    results = analyzer.run_analysis(
        num_puzzles=5,
        rating_min=1200,
        rating_max=1800,
        v7p3r_time=5.0,  # Reduce to 5 seconds per puzzle for testing
        themes_filter=None
    )
    
    if results:
        print(f"\nSuccessfully analyzed {len(results)} puzzles!")
        
        # Generate report
        report = analyzer.generate_report(results)
        analyzer.print_report(report)
        
        # Save results
        analyzer.save_results("test_results.json")
        
        print("\n✅ Test completed successfully!")
    else:
        print("❌ No results generated")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure V7P3R engine exists at the expected path")
    print("2. Make sure Stockfish engine exists at the expected path") 
    print("3. Make sure puzzle database exists")
    print("4. Check that chess-puzzle-challenger directory is available")
