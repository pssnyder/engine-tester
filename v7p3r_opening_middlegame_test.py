#!/usr/bin/env python3
"""
V7P3R Opening & Middlegame Focused Analysis

Test V7P3R's recent improvements in:
- Opening positioning and control
- Middlegame attacks and defense
- Strategic planning

Filters puzzles by opening/middlegame themes and gives V7P3R generous time
"""

import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from v7p3r_puzzle_analyzer import V7P3RPuzzleAnalyzer
    
    print("V7P3R Opening & Middlegame Analysis")
    print("=" * 60)
    print("Testing V7P3R's recent improvements with OPTIMAL 30s time allocation:")
    print("- Opening positioning and control")
    print("- Middlegame attacks and defense") 
    print("- Strategic planning")
    print("Expected runtime: ~37.5 minutes (75 puzzles × 30s each)")
    print()
    
    # Create analyzer instance
    analyzer = V7P3RPuzzleAnalyzer()
    
    # Test 1: Opening themes
    print("🚀 TEST 1: OPENING ANALYSIS")
    print("-" * 40)
    opening_themes = ["opening", "development", "castling", "attack", "initiative"]
    
    opening_results = analyzer.run_analysis(
        num_puzzles=25,
        rating_min=1200,
        rating_max=2200,
        v7p3r_time=30.0,  # Optimal time based on testing
        themes_filter=opening_themes
    )
    
    print(f"\n📊 Opening Results: {len(opening_results)} puzzles analyzed")
    if opening_results:
        opening_report = analyzer.generate_report(opening_results)
        print(f"Opening Score: {opening_report['average_score']:.2f}/5.0 ({opening_report['percentage_score']:.1f}%)")
        print(f"Top-5 Hit Rate: {opening_report['top5_hit_rate']:.1f}%")
    
    # Test 2: Middlegame themes
    print("\n⚔️ TEST 2: MIDDLEGAME ANALYSIS")
    print("-" * 40)
    middlegame_themes = ["middlegame", "attack", "tactics", "sacrifice", "advantage", "kingAttack"]
    
    # Reset results for clean middlegame analysis
    analyzer.results = []
    
    middlegame_results = analyzer.run_analysis(
        num_puzzles=25,
        rating_min=1400,
        rating_max=2400,
        v7p3r_time=30.0,  # Optimal time based on testing
        themes_filter=middlegame_themes
    )
    
    print(f"\n📊 Middlegame Results: {len(middlegame_results)} puzzles analyzed")
    if middlegame_results:
        middlegame_report = analyzer.generate_report(middlegame_results)
        print(f"Middlegame Score: {middlegame_report['average_score']:.2f}/5.0 ({middlegame_report['percentage_score']:.1f}%)")
        print(f"Top-5 Hit Rate: {middlegame_report['top5_hit_rate']:.1f}%")
    
    # Test 3: Strategic/Positional themes  
    print("\n🎯 TEST 3: STRATEGIC/POSITIONAL ANALYSIS")
    print("-" * 40)
    strategic_themes = ["advantage", "positional", "attraction", "deflection", "clearance", "interference"]
    
    # Reset results for clean strategic analysis
    analyzer.results = []
    
    strategic_results = analyzer.run_analysis(
        num_puzzles=25,
        rating_min=1500,
        rating_max=2300,
        v7p3r_time=30.0,  # Optimal time based on testing
        themes_filter=strategic_themes
    )
    
    print(f"\n📊 Strategic Results: {len(strategic_results)} puzzles analyzed")
    if strategic_results:
        strategic_report = analyzer.generate_report(strategic_results)
        print(f"Strategic Score: {strategic_report['average_score']:.2f}/5.0 ({strategic_report['percentage_score']:.1f}%)")
        print(f"Top-5 Hit Rate: {strategic_report['top5_hit_rate']:.1f}%")
    
    # Combined analysis
    print("\n" + "=" * 80)
    print("📈 COMBINED OPENING & MIDDLEGAME ANALYSIS")
    print("=" * 80)
    
    all_results = opening_results + middlegame_results + strategic_results
    
    if all_results:
        # Set combined results for final report
        analyzer.results = all_results
        
        final_report = analyzer.generate_report(all_results)
        analyzer.print_report(final_report)
        
        # Detailed breakdown by phase
        print(f"\n🔍 PHASE BREAKDOWN:")
        print(f"Opening Performance:    {opening_report['average_score'] if opening_results else 0:.2f}/5.0 ({len(opening_results)} puzzles)")
        print(f"Middlegame Performance: {middlegame_report['average_score'] if middlegame_results else 0:.2f}/5.0 ({len(middlegame_results)} puzzles)")
        print(f"Strategic Performance:  {strategic_report['average_score'] if strategic_results else 0:.2f}/5.0 ({len(strategic_results)} puzzles)")
        print(f"Overall Performance:    {final_report['average_score']:.2f}/5.0 ({len(all_results)} puzzles)")
        
        # Save combined results
        timestamp = analyzer.results[0]['timestamp'][:10] if analyzer.results else "test"
        filename = f"v7p3r_opening_middlegame_analysis_{timestamp}.json"
        analyzer.save_results(filename)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Performance insights
        print(f"\n🎯 KEY INSIGHTS:")
        if opening_results and middlegame_results:
            opening_avg = opening_report['average_score']
            middlegame_avg = middlegame_report['average_score']
            
            if opening_avg > middlegame_avg:
                print(f"✅ V7P3R shows stronger OPENING play (+{opening_avg - middlegame_avg:.2f} pts vs middlegame)")
            elif middlegame_avg > opening_avg:
                print(f"✅ V7P3R shows stronger MIDDLEGAME play (+{middlegame_avg - opening_avg:.2f} pts vs opening)")
            else:
                print(f"⚖️ V7P3R shows balanced opening/middlegame performance")
        
        if final_report['percentage_score'] > 60:
            print(f"🏆 Strong overall performance! V7P3R finds top-5 moves {final_report['top5_hit_rate']:.0f}% of the time")
        elif final_report['percentage_score'] > 40:
            print(f"📈 Good performance with room for improvement. Focus on themes with low scores.")
        else:
            print(f"🔧 Performance needs work. Consider tactical training or search depth improvements.")
        
        print(f"\n✅ Analysis completed successfully!")
    else:
        print("❌ No results generated")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("1. Make sure V7P3R engine exists and is working")
    print("2. Make sure Stockfish engine exists and is working") 
    print("3. Make sure puzzle database contains opening/middlegame puzzles")
    print("4. Try running check_setup.py first")
