#!/usr/bin/env python3
"""
Simple Runner for Version Comparison Analysis

This script provides an easy interface to run version comparisons
with sensible defaults and interactive prompts.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def run_simple_comparison():
    """Run a simple version comparison with user input"""
    
    print("🏁 Chess Engine Version Comparison Tool")
    print("=" * 50)
    
    # Available engines based on directory structure
    available_engines = {
        "1": ("SlowMate", "1.0", "2.0"),
        "2": ("V7P3R", "4.1", "4.3"),
        "3": ("Cece", "2.0", "2.3"),
        "4": ("C0BR4", "1.0", "2.0"),
        "5": ("Custom", "", "")
    }
    
    print("Available comparisons:")
    for key, (engine, v1, v2) in available_engines.items():
        if engine == "Custom":
            print(f"  {key}. {engine} - specify your own versions")
        else:
            print(f"  {key}. {engine} v{v1} vs v{v2}")
    
    choice = input("\nSelect comparison (1-5): ").strip()
    
    if choice not in available_engines:
        print("Invalid choice. Exiting.")
        return
    
    engine, v1, v2 = available_engines[choice]
    
    if engine == "Custom":
        engine = input("Enter engine name (e.g., SlowMate): ").strip()
        v1 = input("Enter first version (e.g., 1.0): ").strip()
        v2 = input("Enter second version (e.g., 2.0): ").strip()
    
    # Configuration options
    print(f"\n📊 Analysis Configuration for {engine} v{v1} vs v{v2}")
    
    depth = input("Stockfish analysis depth (default 12): ").strip()
    depth = int(depth) if depth.isdigit() else 12
    
    max_games = input("Max games per version (default 15): ").strip()
    max_games = int(max_games) if max_games.isdigit() else 15
    
    print(f"\n🔄 Starting analysis...")
    print(f"  Engine: {engine}")
    print(f"  Versions: v{v1} vs v{v2}")
    print(f"  Stockfish depth: {depth}")
    print(f"  Max games: {max_games}")
    
    try:
        # Import and run the analyzer
        from version_comparison_analyzer import VersionComparisonAnalyzer
        import datetime
        import json
        
        # Initialize analyzer
        analyzer = VersionComparisonAnalyzer(stockfish_depth=depth)
        await analyzer.initialize()
        
        # Perform comparison
        comparison = await analyzer.compare_versions(engine, v1, v2, max_games)
        
        # Generate report
        report = analyzer.generate_developer_report(comparison)
        
        # Save report
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"version_comparison_{engine}_v{v1}_vs_v{v2}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Display results
        print(f"\n✅ Analysis Complete!")
        print(f"📄 Report saved: {filename}")
        
        summary = report["executive_summary"]
        print(f"\n📈 Results Summary:")
        print(f"  Overall improvement: {'YES' if summary['overall_improvement'] else 'NO'}")
        print(f"  Accuracy change: {summary['accuracy_change']:+.2f}%")
        print(f"  Blunder rate change: {summary['blunder_rate_change']:+.4f}")
        
        # Show direct comparison if available
        direct = summary["direct_match_record"]
        total_direct = direct["v1_wins"] + direct["v1_losses"] + direct["v1_draws"]
        if total_direct > 0:
            v2_score = (direct["v2_wins"] + 0.5 * direct["v2_draws"]) / total_direct * 100
            print(f"  Head-to-head: v{v2} scored {v2_score:.1f}% in {total_direct} games")
        
        # Show recommendations
        recommendations = report["actionable_recommendations"]
        if recommendations:
            print(f"\n⚠️  Top Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. [{rec['priority']}] {rec['issue']}")
                print(f"     → {rec['recommendation']}")
        
        await analyzer.cleanup()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required dependencies are installed:")
        print("  pip install -r ../../requirements.txt")
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        print("Check that:")
        print("  • Stockfish is available in ../../engines/Stockfish/")
        print("  • Game data is available in ../../results/")
        print("  • Engine names match the tournament data")

def main():
    """Main entry point"""
    try:
        asyncio.run(run_simple_comparison())
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main()
