#!/usr/bin/env python3
"""
V18.3 vs V18.4 Puzzle Performance Comparison
Runs both engines through the same puzzle set and compares tactical accuracy
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add directories to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "engine_utilities"))
sys.path.insert(0, str(current_dir / "databases"))

from universal_puzzle_analyzer import UniversalPuzzleAnalyzer, TimeControl


def run_puzzle_test(engine_name, engine_path, num_puzzles=30, min_rating=1200, max_rating=1800, 
                    time_per_position=10, themes=None, force_puzzle_ids=None):
    """Run puzzle analysis for a single engine"""
    print(f"\n{'='*70}")
    print(f"Testing {engine_name}")
    print(f"{'='*70}\n")
    
    try:
        analyzer = UniversalPuzzleAnalyzer(
            engine_path=str(engine_path),
            stockfish_path=r"e:\Programming Stuff\Chess Engines\Tournament Engines\Stockfish\stockfish-windows-x86-64-avx2.exe",
            puzzle_db_path=r"e:\Programming Stuff\Chess Engines\Chess Engine Playground\engine-tester\databases\puzzles.db",
            time_control=TimeControl(30.0, 2.0)
        )
        
        results = analyzer.run_analysis(
            num_puzzles=num_puzzles,
            rating_min=min_rating,
            rating_max=max_rating,
            suggested_time=time_per_position,
            themes_filter=themes,
            force_puzzle_ids=force_puzzle_ids
        )
        
        if results:
            report = analyzer.generate_report(results)
            
            # Save results with version-specific filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            engine_safe_name = engine_name.replace(' ', '_').replace('.', '_')
            results_file = f"puzzle_results_{engine_safe_name}_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'engine_name': engine_name,
                        'engine_path': str(engine_path),
                        'test_date': datetime.now().isoformat(),
                        'num_puzzles': num_puzzles,
                        'rating_range': [min_rating, max_rating],
                        'time_per_position': time_per_position,
                        'themes': themes
                    },
                    'report': report,
                    'results': results
                }, f, indent=2)
            
            print(f"\n✅ Results saved to: {results_file}")
            return report, results_file
        else:
            print(f"❌ No results generated for {engine_name}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error testing {engine_name}: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def compare_reports(v18_3_report, v18_4_report):
    """Generate comparison summary"""
    print(f"\n{'='*70}")
    print("V18.3 vs V18.4 PUZZLE PERFORMANCE COMPARISON")
    print(f"{'='*70}\n")
    
    if not v18_3_report or not v18_4_report:
        print("❌ Cannot compare - missing report data")
        return
    
    # Overall metrics
    seq_3 = v18_3_report.get('sequence_metrics', {})
    seq_4 = v18_4_report.get('sequence_metrics', {})
    
    print("## Overall Performance")
    print(f"  Weighted Accuracy:")
    print(f"    v18.3: {seq_3.get('avg_weighted_accuracy', 0):.1f}%")
    print(f"    v18.4: {seq_4.get('avg_weighted_accuracy', 0):.1f}%")
    improvement = seq_4.get('avg_weighted_accuracy', 0) - seq_3.get('avg_weighted_accuracy', 0)
    print(f"    Δ: {improvement:+.1f}%")
    print()
    
    print(f"  Perfect Sequences:")
    print(f"    v18.3: {seq_3.get('perfect_sequences', 0)}/{v18_3_report['total_puzzles']}")
    print(f"    v18.4: {seq_4.get('perfect_sequences', 0)}/{v18_4_report['total_puzzles']}")
    print()
    
    print(f"  Average Depth:")
    print(f"    v18.3: {seq_3.get('avg_depth', 0):.1f}")
    print(f"    v18.4: {seq_4.get('avg_depth', 0):.1f}")
    depth_improvement = seq_4.get('avg_depth', 0) - seq_3.get('avg_depth', 0)
    print(f"    Δ: {depth_improvement:+.1f}")
    print()
    
    # Theme comparison
    print("## Theme Performance (Top 5)")
    themes_3 = v18_3_report.get('theme_performance', {})
    themes_4 = v18_4_report.get('theme_performance', {})
    
    all_themes = set(themes_3.keys()) | set(themes_4.keys())
    theme_comparisons = []
    
    for theme in all_themes:
        acc_3 = themes_3.get(theme, {}).get('avg_weighted_accuracy', 0)
        acc_4 = themes_4.get(theme, {}).get('avg_weighted_accuracy', 0)
        count_3 = themes_3.get(theme, {}).get('count', 0)
        count_4 = themes_4.get(theme, {}).get('count', 0)
        
        if count_3 > 0 and count_4 > 0:  # Only compare themes both engines saw
            theme_comparisons.append({
                'theme': theme,
                'v18_3_acc': acc_3,
                'v18_4_acc': acc_4,
                'improvement': acc_4 - acc_3,
                'count': (count_3 + count_4) / 2
            })
    
    # Sort by absolute improvement
    theme_comparisons.sort(key=lambda x: abs(x['improvement']), reverse=True)
    
    print(f"{'Theme':<20} {'v18.3':<10} {'v18.4':<10} {'Δ':<10} {'Count'}")
    print("-" * 60)
    for tc in theme_comparisons[:10]:  # Top 10 themes
        print(f"{tc['theme']:<20} {tc['v18_3_acc']:>6.1f}%    {tc['v18_4_acc']:>6.1f}%    {tc['improvement']:>+6.1f}%    {tc['count']:.0f}")
    
    print(f"\n{'='*70}")
    
    # Determine verdict
    if improvement > 5.0:
        print("✅ SIGNIFICANT IMPROVEMENT - v18.4 shows clear tactical gains")
    elif improvement > 2.0:
        print("✅ MODERATE IMPROVEMENT - v18.4 performs better overall")
    elif improvement > -2.0:
        print("➖ NEUTRAL - Performance similar between versions")
    else:
        print("⚠️  REGRESSION - v18.4 underperforming v18.3")
    
    print(f"{'='*70}\n")


def main():
    """Run comparison test"""
    print("\n" + "="*70)
    print("V7P3R v18.3 vs v18.4 Tactical Puzzle Comparison")
    print("="*70)
    
    # Engine paths
    v18_3_path = Path(r"e:\Programming Stuff\Chess Engines\Tournament Engines\V7P3R\V7P3R_v18.3\V7P3R_v18.3.bat")
    v18_4_path = Path(r"e:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\development\V7P3R_v18.4_20260415\V7P3R_v18.4.bat")
    
    # Verify engines exist
    if not v18_3_path.exists():
        print(f"❌ v18.3 engine not found: {v18_3_path}")
        return 1
    if not v18_4_path.exists():
        print(f"❌ v18.4 engine not found: {v18_4_path}")
        return 1
    
    # Test configuration - mate and tactical themes to test v18.4's improvements
    test_config = {
        'num_puzzles': 30,  # Reasonable size for comparison
        'min_rating': 1200,  # v7p3r's rating range
        'max_rating': 1800,
        'time_per_position': 10,  # 10s per position
        'themes': ['mate', 'mateIn1', 'mateIn2', 'pin', 'fork', 'skewer', 'discoveredAttack', 'attackingF2F7']
    }
    
    print("\nTest Configuration:")
    print(f"  Puzzles: {test_config['num_puzzles']}")
    print(f"  Rating: {test_config['min_rating']}-{test_config['max_rating']}")
    print(f"  Time: {test_config['time_per_position']}s per position")
    print(f"  Themes: {', '.join(test_config['themes'])}")
    print()
    
    # Run v18.3 first to get puzzle IDs
    print("STEP 1: Testing v18.3 (baseline)...")
    v18_3_report, v18_3_file = run_puzzle_test(
        "v18.3",
        v18_3_path,
        **test_config
    )
    
    if not v18_3_report:
        print("❌ v18.3 test failed, aborting comparison")
        return 1
    
    # Extract puzzle IDs from v18.3 results to ensure same puzzles tested
    puzzle_ids = None
    if v18_3_file:
        try:
            with open(v18_3_file, 'r') as f:
                v18_3_data = json.load(f)
                puzzle_ids = [r['puzzle_id'] for r in v18_3_data.get('results', [])]
                print(f"\n✓ Extracted {len(puzzle_ids)} puzzle IDs from v18.3 results")
        except Exception as e:
            print(f"⚠️  Could not extract puzzle IDs: {e}")
    
    # Run v18.4 with same puzzles
    print("\nSTEP 2: Testing v18.4 (candidate)...")
    v18_4_report, v18_4_file = run_puzzle_test(
        "v18.4",
        v18_4_path,
        **test_config,
        force_puzzle_ids=puzzle_ids  # Use same puzzles as v18.3
    )
    
    if not v18_4_report:
        print("❌ v18.4 test failed, aborting comparison")
        return 1
    
    # Generate comparison
    compare_reports(v18_3_report, v18_4_report)
    
    print("\n✅ Puzzle comparison complete!")
    print(f"\nResult files:")
    print(f"  v18.3: {v18_3_file}")
    print(f"  v18.4: {v18_4_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
