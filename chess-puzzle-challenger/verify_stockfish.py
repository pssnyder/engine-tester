#!/usr/bin/env python3
"""
Stockfish Puzzle Verification Test
Tests Stockfish on the same puzzle set to verify our testing framework works correctly
"""

import os
import sys
from pathlib import Path

# Add the chess-puzzle-challenger src to the path
puzzle_challenger_dir = Path(__file__).parent
src_dir = puzzle_challenger_dir / "src"
sys.path.insert(0, str(src_dir))

from engine_comparison import EnginePuzzleComparison

def main():
    """Run Stockfish on the same puzzle set to verify testing framework"""
    
    # Configuration
    engine_tester_base = puzzle_challenger_dir.parent
    stockfish_local = puzzle_challenger_dir / "src" / "stockfish.exe"
    stockfish_engines = engine_tester_base / "engines" / "Stockfish" / "stockfish-windows-x86-64-avx2.exe"
    db_path = puzzle_challenger_dir / "puzzles.db"
    
    # Try to find Stockfish
    stockfish_path = None
    if stockfish_local.exists():
        stockfish_path = stockfish_local
    elif stockfish_engines.exists():
        stockfish_path = stockfish_engines
    else:
        print("❌ Stockfish not found in expected locations")
        print(f"   Checked: {stockfish_local}")
        print(f"   Checked: {stockfish_engines}")
        return False
    
    # Initialize comparison tool with dashboard output
    dashboard_data_dir = engine_tester_base / "analytics_and_dashboard" / "dashboard" / "data"
    comparer = EnginePuzzleComparison(str(dashboard_data_dir))
    
    # Test parameters - same as the V7P3R vs SlowMate test for comparison
    themes = ["middlegame", "endgame", "mate", "mateIn2", "mateIn3", "pin", "fork", "skewer", "tactics"]
    quantity = 100
    min_rating = 400
    max_rating = 1200
    think_time_ms = 3000  # 3 seconds should be plenty for Stockfish
    
    print("🔬 STOCKFISH PUZZLE VERIFICATION TEST")
    print("🎯 Purpose: Verify puzzle challenger framework accuracy")
    print(f"📊 Test Parameters:")
    print(f"   • Puzzles: {quantity}")
    print(f"   • Themes: {', '.join(themes)}")
    print(f"   • Rating Range: {min_rating}-{max_rating}")
    print(f"   • Think Time: {think_time_ms}ms per move")
    print(f"   • Engine: {stockfish_path}")
    print(f"   • Results → {dashboard_data_dir}")
    
    # Verify files exist
    if not db_path.exists():
        print(f"❌ Puzzle database not found: {db_path}")
        return False
    
    print(f"✅ Stockfish engine found: {stockfish_path}")
    print(f"✅ Puzzle database found: {db_path}")
    
    try:
        # Run Stockfish test
        print(f"\n{'='*80}")
        print("🚀 Starting Stockfish Verification Test...")
        print(f"{'='*80}")
        
        result = comparer.test_single_engine(
            engine_path=str(stockfish_path),
            themes=themes,
            quantity=quantity,
            min_rating=min_rating,
            max_rating=max_rating,
            think_time_ms=think_time_ms,
            db_path=str(db_path)
        )
        
        # Analyze results
        total_puzzles = result.total
        solved_puzzles = result.solved
        success_rate = (solved_puzzles / total_puzzles) * 100 if total_puzzles > 0 else 0
        avg_time = result.time_taken / total_puzzles if total_puzzles > 0 else 0
        
        print(f"\n{'='*80}")
        print("📊 STOCKFISH VERIFICATION RESULTS")
        print(f"{'='*80}")
        print(f"✅ Total Puzzles: {total_puzzles}")
        print(f"🎯 Solved: {solved_puzzles}")
        print(f"❌ Failed: {total_puzzles - solved_puzzles}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Average Time: {avg_time:.2f}s per puzzle")
        print(f"🕒 Total Time: {result.time_taken:.1f}s")
        
        # Save results
        from datetime import datetime
        import json
        
        stockfish_results = {
            "test_type": "stockfish_verification",
            "timestamp": datetime.now().isoformat(),
            "engine_name": result.engine_name,
            "engine_path": str(stockfish_path),
            "puzzle_parameters": {
                "quantity": quantity,
                "themes": themes,
                "min_rating": min_rating,
                "max_rating": max_rating,
                "think_time_ms": think_time_ms
            },
            "results": {
                "total_puzzles": total_puzzles,
                "solved_puzzles": solved_puzzles,
                "failed_puzzles": total_puzzles - solved_puzzles,
                "success_rate": success_rate,
                "average_time_per_puzzle": avg_time,
                "total_time": result.time_taken
            },
            "detailed_results": result.detailed_results
        }
        
        # Save verification results
        verification_filename = f"stockfish_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        verification_path = dashboard_data_dir / verification_filename
        
        with open(verification_path, 'w', encoding='utf-8') as f:
            json.dump(stockfish_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Verification results saved to: {verification_path}")
        
        # Analysis and verdict
        print(f"\n{'='*80}")
        print("🔍 FRAMEWORK VERIFICATION ANALYSIS")
        print(f"{'='*80}")
        
        if success_rate >= 80:
            print("✅ FRAMEWORK VERIFIED: Stockfish achieved excellent results (≥80%)")
            print("   → Puzzle challenger is working correctly")
            print("   → V7P3R and SlowMate results are accurate")
        elif success_rate >= 50:
            print("⚠️  FRAMEWORK QUESTIONABLE: Stockfish achieved moderate results (50-79%)")
            print("   → Some puzzle validation issues may exist")
            print("   → Manual review recommended")
        else:
            print("❌ FRAMEWORK ISSUE: Stockfish achieved poor results (<50%)")
            print("   → Serious issues with puzzle validation or engine interface")
            print("   → Framework needs debugging")
        
        # Compare with our engines
        print(f"\n📊 COMPARISON WITH TESTED ENGINES:")
        print(f"   • Stockfish: {success_rate:.1f}% success rate")
        print(f"   • SlowMate v3.0: 6.0% success rate")
        print(f"   • V7P3R v5.1: 0.0% success rate")
        print(f"   • Performance Gap: Stockfish is {success_rate/6.0:.1f}x better than SlowMate")
        
        # Specific insights
        if success_rate < 90:
            print(f"\n💡 PUZZLE ANALYSIS:")
            failed_puzzles = [r for r in result.detailed_results if not r['solved']]
            if failed_puzzles:
                print(f"   • {len(failed_puzzles)} puzzles failed even for Stockfish")
                print(f"   • These may be extremely difficult or have validation issues")
                
                # Show a few examples
                print(f"   • Sample failed puzzles:")
                for i, puzzle in enumerate(failed_puzzles[:3]):
                    print(f"     - {puzzle['puzzle_id']} (Rating: {puzzle['puzzle_rating']}, Themes: {puzzle['puzzle_themes']})")
        
        print(f"\n🎯 CONCLUSION:")
        if success_rate >= 80:
            print("   The puzzle challenger framework is working correctly!")
            print("   V7P3R and SlowMate simply need tactical improvement.")
        else:
            print("   Framework verification suggests potential issues.")
            print("   Consider debugging puzzle validation or engine interface.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
