#!/usr/bin/env python3
"""
Batch Version Comparison Script

Runs version comparisons for multiple engines as requested:
- SlowMate v1.0 vs v2.0
- V7P3R v4.1 vs v4.3  
- Cece v2.0 vs v2.3
- C0BR4 v1.0 vs v2.0

This script automates the analysis process and generates comprehensive reports
for each engine comparison.
"""

import asyncio
import os
import json
import datetime
from pathlib import Path
from version_comparison_analyzer import VersionComparisonAnalyzer

class BatchComparisonRunner:
    """Manages multiple version comparisons"""
    
    def __init__(self, stockfish_depth: int = 12, max_games_per_version: int = 15):
        self.stockfish_depth = stockfish_depth
        self.max_games_per_version = max_games_per_version
        self.results = {}
        
    async def run_all_comparisons(self):
        """Run all requested version comparisons"""
        
        # Define comparisons to run - all original requested comparisons now have data
        comparisons = [
            {"engine": "SlowMate", "v1": "1.0", "v2": "2.0"},
            {"engine": "V7P3R", "v1": "4.1", "v2": "4.3"},
            {"engine": "Cece", "v1": "2.0", "v2": "2.3"},
            {"engine": "C0BR4", "v1": "1.0", "v2": "2.0"},
        ]
        
        print(f"🚀 Starting batch comparison analysis...")
        print(f"Configurations:")
        print(f"  - Stockfish depth: {self.stockfish_depth}")
        print(f"  - Max games per version: {self.max_games_per_version}")
        print(f"  - Total comparisons: {len(comparisons)}")
        print("=" * 60)
        
        # Initialize analyzer once
        analyzer = VersionComparisonAnalyzer(stockfish_depth=self.stockfish_depth)
        
        try:
            await analyzer.initialize()
            
            for i, comp in enumerate(comparisons, 1):
                print(f"\n📊 Comparison {i}/{len(comparisons)}: {comp['engine']} v{comp['v1']} vs v{comp['v2']}")
                print("-" * 40)
                
                try:
                    # Run comparison
                    comparison_result = await analyzer.compare_versions(
                        comp["engine"], 
                        comp["v1"], 
                        comp["v2"], 
                        self.max_games_per_version
                    )
                    
                    # Generate report
                    report = analyzer.generate_developer_report(comparison_result)
                    
                    # Save individual report
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"version_comparison_{comp['engine']}_v{comp['v1']}_vs_v{comp['v2']}_{timestamp}.json"
                    output_path = os.path.join(".", filename)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2, default=str)
                    
                    # Store result for summary
                    self.results[f"{comp['engine']}_v{comp['v1']}_vs_v{comp['v2']}"] = {
                        "report_file": output_path,
                        "summary": report["executive_summary"],
                        "status": "completed"
                    }
                    
                    print(f"✅ Analysis complete. Report saved: {filename}")
                    self.print_comparison_summary(comp, report)
                    
                except Exception as e:
                    print(f"❌ Error analyzing {comp['engine']}: {e}")
                    self.results[f"{comp['engine']}_v{comp['v1']}_vs_v{comp['v2']}"] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    continue
        
        finally:
            await analyzer.cleanup()
        
        # Generate master summary
        self.generate_master_summary()
    
    def print_comparison_summary(self, comp: dict, report: dict):
        """Print a brief summary of comparison results"""
        summary = report["executive_summary"]
        
        print(f"📈 Summary for {comp['engine']} v{comp['v1']} → v{comp['v2']}:")
        
        # Overall improvement assessment
        if summary["overall_improvement"]:
            print("  🎯 Overall: IMPROVED")
        else:
            print("  ⚠️  Overall: REGRESSED or UNCHANGED")
        
        # Key metrics
        accuracy_change = summary["accuracy_change"]
        blunder_change = summary["blunder_rate_change"]
        
        print(f"  📊 Accuracy change: {accuracy_change:+.2f}%")
        print(f"  🎲 Blunder rate change: {blunder_change:+.4f}")
        
        # Direct match results
        direct = summary["direct_match_record"]
        total_direct = direct["v1_wins"] + direct["v1_losses"] + direct["v1_draws"]
        if total_direct > 0:
            v2_score = (direct["v2_wins"] + 0.5 * direct["v2_draws"]) / total_direct * 100
            print(f"  🥊 Head-to-head: v{comp['v2']} scored {v2_score:.1f}% ({direct['v2_wins']}-{direct['v2_draws']}-{direct['v2_losses']})")
        
        # Regressions
        regressions = summary["key_regressions"]
        if regressions > 0:
            print(f"  ⚠️  Key regressions identified: {regressions}")
        else:
            print("  ✅ No major regressions detected")
    
    def generate_master_summary(self):
        """Generate a master summary of all comparisons"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f"batch_comparison_summary_{timestamp}.json"
        
        master_report = {
            "analysis_metadata": {
                "batch_analysis_date": datetime.datetime.now().isoformat(),
                "total_comparisons": len(self.results),
                "successful_comparisons": len([r for r in self.results.values() if r.get("status") == "completed"]),
                "failed_comparisons": len([r for r in self.results.values() if r.get("status") == "failed"]),
                "configuration": {
                    "stockfish_depth": self.stockfish_depth,
                    "max_games_per_version": self.max_games_per_version
                }
            },
            "comparison_results": self.results,
            "overall_insights": self.generate_overall_insights()
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(master_report, f, indent=2, default=str)
        
        print(f"\n🎯 BATCH ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Master summary saved: {summary_file}")
        print(f"Successful analyses: {master_report['analysis_metadata']['successful_comparisons']}")
        print(f"Failed analyses: {master_report['analysis_metadata']['failed_comparisons']}")
        
        # Print overall insights
        insights = master_report["overall_insights"]
        print(f"\n🔍 Overall Insights:")
        print(f"  Engines that improved: {len(insights['improved_engines'])}")
        print(f"  Engines with regressions: {len(insights['regressed_engines'])}")
        print(f"  Average accuracy change: {insights['average_accuracy_change']:.2f}%")
        
        if insights['most_improved']:
            print(f"  Most improved: {insights['most_improved']['engine']} (+{insights['most_improved']['improvement']:.2f}%)")
        
        if insights['most_regressed']:
            print(f"  Most regressed: {insights['most_regressed']['engine']} ({insights['most_regressed']['regression']:.2f}%)")
    
    def generate_overall_insights(self) -> dict:
        """Generate insights across all comparisons"""
        successful_results = [r for r in self.results.values() if r.get("status") == "completed"]
        
        if not successful_results:
            return {"error": "No successful comparisons to analyze"}
        
        # Collect metrics
        accuracy_changes = []
        improved_engines = []
        regressed_engines = []
        
        for engine_name, result in self.results.items():
            if result.get("status") != "completed":
                continue
                
            summary = result["summary"]
            accuracy_change = summary["accuracy_change"]
            accuracy_changes.append(accuracy_change)
            
            if summary["overall_improvement"]:
                improved_engines.append({
                    "engine": engine_name,
                    "accuracy_change": accuracy_change
                })
            else:
                regressed_engines.append({
                    "engine": engine_name,
                    "accuracy_change": accuracy_change
                })
        
        # Find most/least improved
        most_improved = max(improved_engines, key=lambda x: x["accuracy_change"]) if improved_engines else None
        most_regressed = min(regressed_engines, key=lambda x: x["accuracy_change"]) if regressed_engines else None
        
        return {
            "improved_engines": improved_engines,
            "regressed_engines": regressed_engines,
            "average_accuracy_change": sum(accuracy_changes) / len(accuracy_changes) if accuracy_changes else 0,
            "most_improved": {
                "engine": most_improved["engine"],
                "improvement": most_improved["accuracy_change"]
            } if most_improved else None,
            "most_regressed": {
                "engine": most_regressed["engine"],
                "regression": most_regressed["accuracy_change"]
            } if most_regressed else None
        }

async def main():
    """Main execution function"""
    print("🔍 Chess Engine Version Comparison Batch Analysis")
    print("=" * 60)
    print("This script will analyze version differences for:")
    print("  • SlowMate v1.0 vs v2.0")
    print("  • V7P3R v4.1 vs v4.3")
    print("  • Cece v2.0 vs v2.3")
    print("  • C0BR4 v1.0 vs v2.0")
    print()
    print("The analysis will:")
    print("  ✓ Compare gameplay performance between versions")
    print("  ✓ Identify blunders and regressions using Stockfish")
    print("  ✓ Generate detailed developer reports")
    print("  ✓ Provide actionable recommendations")
    print()
    
    # Configuration
    depth = 12  # Balanced depth for reasonable analysis time
    max_games = 15  # Sufficient sample size while keeping runtime manageable
    
    print(f"Analysis configuration:")
    print(f"  Stockfish analysis depth: {depth}")
    print(f"  Max games per version: {max_games}")
    print()
    
    response = input("Proceed with analysis? (y/N): ").strip().lower()
    if response != 'y':
        print("Analysis cancelled.")
        return
    
    # Run batch analysis
    runner = BatchComparisonRunner(stockfish_depth=depth, max_games_per_version=max_games)
    await runner.run_all_comparisons()

if __name__ == "__main__":
    asyncio.run(main())
