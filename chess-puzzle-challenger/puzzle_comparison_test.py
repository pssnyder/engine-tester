#!/usr/bin/env python3
"""
V7P3R vs SlowMate Puzzle Challenge Test
Compares V7P3R v7.0 and SlowMate v3.0 on tactical puzzles under 800 ELO.
"""

import os
import sys
import time
from pathlib import Path

# Add chess-puzzle-challenger to Python path
challenger_path = Path(__file__).parent / "chess-puzzle-challenger"
sys.path.insert(0, str(challenger_path))

from src.database import PuzzleDatabase
from src.engine_comparison import EnginePuzzleComparison

def run_v7p3r_vs_slowmate_puzzle_test():
    """Run a focused puzzle comparison between V7P3R v7.0 and SlowMate v3.0."""
    
    print("🏁 V7P3R v7.0 vs SlowMate v3.0 Puzzle Challenge")
    print("=" * 60)
    
    # Engine paths (using the validated .exe files)
    engines_dir = Path(__file__).parent / "engines"
    v7p3r_path = engines_dir / "V7P3R" / "V7P3R_v7.0.exe"
    slowmate_path = engines_dir / "SlowMate" / "SlowMate_v3.0.exe"
    
    # Verify engines exist
    if not v7p3r_path.exists():
        print(f"❌ V7P3R engine not found: {v7p3r_path}")
        return False
    
    if not slowmate_path.exists():
        print(f"❌ SlowMate engine not found: {slowmate_path}")
        return False
    
    print(f"✓ V7P3R engine: {v7p3r_path}")
    print(f"✓ SlowMate engine: {slowmate_path}")
    
    # Initialize puzzle database
    print("\n📚 Initializing puzzle database...")
    puzzle_db_path = challenger_path / "puzzles.db"
    db = PuzzleDatabase(str(puzzle_db_path))
    
    # Configure puzzle selection criteria
    puzzle_criteria = {
        'min_rating': 400,      # Lower bound
        'max_rating': 799,      # Under 800 as requested
        'themes': [             # Simple tactical themes
            'backRankMate',
            'fork',
            'pin',
            'skewer',
            'discoveredAttack',
            'deflection',
            'decoy',
            'attraction'
        ],
        'max_moves': 0,         # No move limit for now (0 = no limit)
        'limit': 20             # Test with 20 puzzles for focused comparison
    }
    
    print(f"\n🎯 Puzzle Selection Criteria:")
    print(f"   Rating Range: {puzzle_criteria['min_rating']}-{puzzle_criteria['max_rating']}")
    print(f"   Themes: {', '.join(puzzle_criteria['themes'][:5])}...")
    print(f"   Max Moves: {puzzle_criteria['max_moves']}")
    print(f"   Puzzle Count: {puzzle_criteria['limit']}")
    
    # Get puzzles matching criteria
    print("\n🔍 Selecting puzzles...")
    puzzles = []
    
    # Try each theme to get a diverse set
    puzzles_per_theme = puzzle_criteria['limit'] // len(puzzle_criteria['themes'])
    for theme in puzzle_criteria['themes']:
        theme_puzzles = db.query_puzzles(
            themes=[theme],
            min_rating=puzzle_criteria['min_rating'],
            max_rating=puzzle_criteria['max_rating'],
            limit_moves=puzzle_criteria['max_moves'],
            quantity=puzzles_per_theme,
            strict_themes=False
        )
        puzzles.extend(theme_puzzles)
        if len(puzzles) >= puzzle_criteria['limit']:
            break
    
    # Trim to exact limit and remove duplicates
    unique_puzzles = {}
    for puzzle in puzzles:
        if puzzle.id not in unique_puzzles:
            unique_puzzles[puzzle.id] = puzzle
    
    puzzles = list(unique_puzzles.values())[:puzzle_criteria['limit']]
    
    if not puzzles:
        print("❌ No puzzles found matching criteria!")
        return False
    
    print(f"✓ Selected {len(puzzles)} puzzles")
    
    # Display puzzle breakdown
    theme_counts = {}
    rating_counts = {}
    for puzzle in puzzles:
        # Count themes
        for theme in puzzle.themes.split():
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Count by rating ranges
        rating_range = f"{(puzzle.rating // 100) * 100}-{(puzzle.rating // 100) * 100 + 99}"
        rating_counts[rating_range] = rating_counts.get(rating_range, 0) + 1
    
    print(f"\n📊 Puzzle Breakdown:")
    print(f"   By Theme: {dict(list(theme_counts.items())[:5])}...")
    print(f"   By Rating: {rating_counts}")
    
    # Initialize comparison
    print(f"\n⚔️ Starting engine comparison...")
    comparison = EnginePuzzleComparison()
    
    # Run comparison with appropriate think time for tactical puzzles
    think_time = 3000  # 3 seconds per move for tactical analysis
    
    print(f"⏱️ Think Time: {think_time}ms per move")
    print(f"🎮 Starting puzzle solving...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Use the compare_engines method instead
        result = comparison.compare_engines(
            engine_1_path=str(v7p3r_path),
            engine_2_path=str(slowmate_path),
            themes=puzzle_criteria['themes'],
            quantity=puzzle_criteria['limit'],
            min_rating=puzzle_criteria['min_rating'],
            max_rating=puzzle_criteria['max_rating'],
            think_time_ms=think_time,
            db_path=str(puzzle_db_path)
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Display results in our format
        print("\n" + "=" * 60)
        print("🏆 PUZZLE CHALLENGE RESULTS")
        print("=" * 60)
        
        # Extract results from comparison result
        v7p3r_results = result.engine_1_results
        slowmate_results = result.engine_2_results
        
        # Display individual results
        for engine_name, engine_results in [(result.engine_1_name, v7p3r_results), (result.engine_2_name, slowmate_results)]:
            print(f"\n🤖 {engine_name}:")
            print(f"   Puzzles Solved: {engine_results['solved']}/{engine_results['total']}")
            print(f"   Success Rate: {(engine_results['solved']/engine_results['total']*100):.1f}%")
            print(f"   Avg Time per Puzzle: {(engine_results['time_taken']/engine_results['total']):.2f}s")
            
            # Theme performance
            if engine_results.get('by_theme'):
                print(f"   Best Themes: ", end="")
                theme_performance = [(theme, stats['solved']/stats['total']) 
                                   for theme, stats in engine_results['by_theme'].items() 
                                   if stats['total'] > 0]
                if theme_performance:
                    theme_performance.sort(key=lambda x: x[1], reverse=True)
                    print(", ".join([f"{theme}({rate:.0%})" for theme, rate in theme_performance[:3]]))
                else:
                    print("No theme data")
        
        # Head-to-head comparison
        comparison_metrics = result.comparison_metrics
        
        print(f"\n🥊 HEAD-TO-HEAD COMPARISON:")
        print(f"   Winner: {comparison_metrics['overall_winner']}")
        if comparison_metrics['success_rate_difference'] != 0:
            print(f"   Success Rate Difference: {comparison_metrics['success_rate_difference']:.1%}")
        
        v7p3r_rate = v7p3r_results['solved'] / v7p3r_results['total']
        slowmate_rate = slowmate_results['solved'] / slowmate_results['total']
        
        print(f"   V7P3R Speed: {(v7p3r_results['time_taken']/v7p3r_results['total']):.2f}s avg")
        print(f"   SlowMate Speed: {(slowmate_results['time_taken']/slowmate_results['total']):.2f}s avg")
        
        print(f"\n⏱️ Total Test Time: {total_time:.1f} seconds")
        print(f"📈 Puzzles per Engine: {len(puzzles)}")
        print(f"🎯 Rating Range: {puzzle_criteria['min_rating']}-{puzzle_criteria['max_rating']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_v7p3r_vs_slowmate_puzzle_test()
    if success:
        print("\n✅ Puzzle comparison completed successfully!")
    else:
        print("\n❌ Puzzle comparison failed!")
        sys.exit(1)
