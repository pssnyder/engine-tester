#!/usr/bin/env python3
"""
V7P3R vs SlowMate Puzzle Competition Runner
Runs the tactical skills competition and saves results to dashboard
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
    """Run the V7P3R vs SlowMate puzzle competition"""
    
    # Configuration
    engine_tester_base = puzzle_challenger_dir.parent
    v7p3r_path = engine_tester_base / "engines" / "V7P3R" / "V7P3R_v5.1.exe"
    slowmate_path = engine_tester_base / "engines" / "SlowMate" / "SlowMate_v3.0.exe"
    db_path = puzzle_challenger_dir / "puzzles.db"
    
    # Initialize comparison tool with dashboard output
    dashboard_data_dir = engine_tester_base / "analytics_and_dashboard" / "dashboard" / "data"
    comparer = EnginePuzzleComparison(str(dashboard_data_dir))
    
    # Test parameters - as requested by user
    themes = ["middlegame", "endgame", "mate", "mateIn2", "mateIn3", "pin", "fork", "skewer", "tactics"]
    quantity = 100  # Start with 100 for testing, can increase later
    min_rating = 400
    max_rating = 1200
    think_time_ms = 5000  # 5 seconds thinking time for thorough analysis but avoid timeouts
    
    print("🏁 V7P3R vs SlowMate: The Ultimate Tactical Skills Challenge")
    print("🤖 Human-designed engine vs 🧠 AI-designed engine")
    print(f"📊 Test Parameters:")
    print(f"   • Puzzles: {quantity}")
    print(f"   • Themes: {', '.join(themes)}")
    print(f"   • Rating Range: {min_rating}-{max_rating}")
    print(f"   • Think Time: {think_time_ms}ms per move")
    print(f"   • Results → {dashboard_data_dir}")
    
    # Verify engines exist
    if not v7p3r_path.exists():
        print(f"❌ V7P3R engine not found: {v7p3r_path}")
        return False
    
    if not slowmate_path.exists():
        print(f"❌ SlowMate engine not found: {slowmate_path}")
        return False
    
    if not db_path.exists():
        print(f"❌ Puzzle database not found: {db_path}")
        print("💡 Please run the puzzle import first:")
        print(f"   cd {puzzle_challenger_dir}")
        print(f"   python -m src.main import-puzzles --file lichess_db_puzzle.csv")
        return False
    
    print(f"✅ V7P3R engine found: {v7p3r_path}")
    print(f"✅ SlowMate engine found: {slowmate_path}")
    print(f"✅ Puzzle database found: {db_path}")
    
    try:
        # Run the comparison
        print(f"\n{'='*80}")
        print("🚀 Starting Competition...")
        print(f"{'='*80}")
        
        result = comparer.compare_engines(
            engine_1_path=str(v7p3r_path),
            engine_2_path=str(slowmate_path),
            themes=themes,
            quantity=quantity,
            min_rating=min_rating,
            max_rating=max_rating,
            think_time_ms=think_time_ms,
            db_path=str(db_path)
        )
        
        # Save results to dashboard
        results_file = comparer.save_results(result)
        
        # Generate tactical skills report
        print(f"\n📈 Generating tactical skills analysis...")
        tactical_report = comparer.generate_tactical_skills_report(result)
        
        # Save tactical report
        from datetime import datetime
        import json
        
        report_filename = f"tactical_skills_report_{result.engine_1_name}_vs_{result.engine_2_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = dashboard_data_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(tactical_report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tactical skills report saved to: {report_path}")
        
        # Print final summary
        print(f"\n{'='*80}")
        print("🏆 COMPETITION COMPLETED SUCCESSFULLY!")
        print(f"{'='*80}")
        print(f"📁 Results Location: {dashboard_data_dir}")
        print(f"📄 Main Results: {results_file}")
        print(f"📊 Tactical Report: {report_path}")
        print(f"\n🎯 Next Steps:")
        print(f"   • Review results in the dashboard")
        print(f"   • Compare engine strengths and weaknesses")
        print(f"   • Use insights for engine improvements")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during competition: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
