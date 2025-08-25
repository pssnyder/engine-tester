#!/usr/bin/env python3
"""
V7P3R Quick Gauntlet vs Established Engines
Test V7P3R v7.0 against known UCI engines to establish baseline rating
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def run_v7p3r_quick_gauntlet():
    """Run V7P3R v7.0 against available established UCI engines"""
    
    print("🏟️ V7P3R v7.0 Quick Gauntlet vs Established Engines")
    print("=" * 70)
    
    # Engine paths
    base_dir = Path(__file__).parent
    engines_dir = base_dir / "engines"
    downloaded_engines_dir = base_dir / "downloaded_engines"
    
    v7p3r_path = engines_dir / "V7P3R" / "V7P3R_v7.0.exe"
    
    # Available opponent engines with approximate ratings
    available_engines = [
        {
            'name': 'SlowMate_v3.0',
            'path': engines_dir / "SlowMate" / "SlowMate_v3.0.exe",
            'estimated_rating': 1800,  # Based on our tournaments
            'description': 'Educational engine'
        },
        {
            'name': 'Stockfish_17.1',
            'path': downloaded_engines_dir / "stockfish" / "stockfish-windows-x86-64-avx2.exe",
            'estimated_rating': 3500,  # World's strongest
            'description': 'World champion engine'
        },
        # Add other engines as available
    ]
    
    # Verify engines exist
    if not v7p3r_path.exists():
        print(f"❌ V7P3R engine not found: {v7p3r_path}")
        return False
    
    print(f"✓ V7P3R Engine: {v7p3r_path}")
    
    active_opponents = []
    for engine in available_engines:
        if engine['path'].exists():
            active_opponents.append(engine)
            print(f"✓ {engine['name']}: {engine['path']} (Est. {engine['estimated_rating']} ELO)")
        else:
            print(f"❌ {engine['name']}: Not found at {engine['path']}")
    
    if not active_opponents:
        print("❌ No opponent engines available!")
        return False
    
    print(f"\n🎯 Quick Gauntlet Configuration:")
    print(f"   Test Engine: V7P3R v7.0")
    print(f"   Opponents: {len(active_opponents)}")
    print(f"   Games per Opponent: 4 (2 as White, 2 as Black)")
    print(f"   Time Control: 3+2 (3 min + 2 sec increment)")
    print(f"   Total Games: {len(active_opponents) * 4}")
    
    # Run using our existing battle framework
    print(f"\n⚔️ Starting Quick Gauntlet...")
    print("-" * 50)
    
    total_results = {
        'wins': 0, 'losses': 0, 'draws': 0, 'errors': 0,
        'white_record': {'wins': 0, 'losses': 0, 'draws': 0},
        'black_record': {'wins': 0, 'losses': 0, 'draws': 0},
        'opponent_results': {}
    }
    
    start_time = time.time()
    
    for i, opponent in enumerate(active_opponents, 1):
        print(f"\n[{i}/{len(active_opponents)}] vs {opponent['name']} (Est. {opponent['estimated_rating']} ELO)")
        print(f"{'='*50}")
        
        opponent_results = {'wins': 0, 'losses': 0, 'draws': 0, 'errors': 0}
        
        # Run 4 games: 2 as White, 2 as Black
        for game_num in range(4):
            v7p3r_as_white = (game_num < 2)  # First 2 games as White
            
            if v7p3r_as_white:
                white_engine = str(v7p3r_path)
                black_engine = str(opponent['path'])
                color_info = "V7P3R(W) vs"
            else:
                white_engine = str(opponent['path'])
                black_engine = str(v7p3r_path)
                color_info = "V7P3R(B) vs"
            
            print(f"\n   Game {game_num + 1}: {color_info} {opponent['name']}")
            
            try:
                # Use our existing battle framework via Python subprocess
                battle_cmd = [
                    'python', 
                    str(base_dir / 'automated_battle_framework' / 'simple_test.py'),
                    '--white', white_engine,
                    '--black', black_engine,
                    '--time', '180',  # 3 minutes
                    '--increment', '2'  # 2 seconds
                ]
                
                result = subprocess.run(battle_cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    # Parse result from output (simplified)
                    output = result.stdout
                    
                    if "White wins" in output or "1-0" in output:
                        game_result = '1-0'
                    elif "Black wins" in output or "0-1" in output:
                        game_result = '0-1'
                    else:
                        game_result = '1/2-1/2'  # Draw
                    
                    # Determine V7P3R's result
                    if v7p3r_as_white:
                        if game_result == '1-0':
                            v7p3r_result = 'win'
                            total_results['white_record']['wins'] += 1
                        elif game_result == '0-1':
                            v7p3r_result = 'loss'
                            total_results['white_record']['losses'] += 1
                        else:
                            v7p3r_result = 'draw'
                            total_results['white_record']['draws'] += 1
                    else:
                        if game_result == '0-1':
                            v7p3r_result = 'win'
                            total_results['black_record']['wins'] += 1
                        elif game_result == '1-0':
                            v7p3r_result = 'loss'
                            total_results['black_record']['losses'] += 1
                        else:
                            v7p3r_result = 'draw'
                            total_results['black_record']['draws'] += 1
                    
                    # Update totals
                    opponent_results[v7p3r_result + 's'] += 1
                    total_results[v7p3r_result + 's'] += 1
                    
                    # Status
                    symbol = "✓" if v7p3r_result == 'win' else "✗" if v7p3r_result == 'loss' else "="
                    print(f"     {symbol} {v7p3r_result.upper()} ({game_result})")
                    
                else:
                    # Error
                    opponent_results['errors'] += 1
                    total_results['errors'] += 1
                    print(f"     ❌ ERROR: Battle failed")
                    
            except subprocess.TimeoutExpired:
                opponent_results['errors'] += 1
                total_results['errors'] += 1
                print(f"     ⏰ TIMEOUT: Game took too long")
            except Exception as e:
                opponent_results['errors'] += 1
                total_results['errors'] += 1
                print(f"     ❌ EXCEPTION: {e}")
        
        # Store opponent results
        total_results['opponent_results'][opponent['name']] = opponent_results
        
        # Print opponent summary
        opp_total = opponent_results['wins'] + opponent_results['losses'] + opponent_results['draws']
        if opp_total > 0:
            win_rate = opponent_results['wins'] / opp_total * 100
            score = opponent_results['wins'] + opponent_results['draws'] * 0.5
            print(f"\n   vs {opponent['name']}: {score:.1f}/{opp_total} ({win_rate:.1f}% win rate)")
    
    # Final Summary
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 70)
    print("🏆 V7P3R v7.0 QUICK GAUNTLET RESULTS")
    print("=" * 70)
    
    # Overall stats
    total_completed = total_results['wins'] + total_results['losses'] + total_results['draws']
    if total_completed > 0:
        win_rate = total_results['wins'] / total_completed * 100
        score = total_results['wins'] + total_results['draws'] * 0.5
        score_percentage = score / total_completed * 100
        
        print(f"\n📊 Overall Performance:")
        print(f"   Record: {total_results['wins']}-{total_results['losses']}-{total_results['draws']}")
        print(f"   Score: {score:.1f}/{total_completed} ({score_percentage:.1f}%)")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Errors: {total_results['errors']}")
    
    # Color analysis
    white_stats = total_results['white_record']
    black_stats = total_results['black_record']
    
    white_total = white_stats['wins'] + white_stats['losses'] + white_stats['draws']
    black_total = black_stats['wins'] + black_stats['losses'] + black_stats['draws']
    
    print(f"\n🎨 Performance by Color:")
    if white_total > 0:
        white_score = white_stats['wins'] + white_stats['draws'] * 0.5
        white_percentage = white_score / white_total * 100
        print(f"   As White: {white_score:.1f}/{white_total} ({white_percentage:.1f}%)")
    
    if black_total > 0:
        black_score = black_stats['wins'] + black_stats['draws'] * 0.5
        black_percentage = black_score / black_total * 100
        print(f"   As Black: {black_score:.1f}/{black_total} ({black_percentage:.1f}%)")
    
    # Rating estimation (very rough)
    if total_completed > 0:
        print(f"\n📈 Estimated Rating Analysis:")
        for opponent_name, opp_results in total_results['opponent_results'].items():
            opponent_info = next(e for e in active_opponents if e['name'] == opponent_name)
            opp_total = opp_results['wins'] + opp_results['losses'] + opp_results['draws']
            
            if opp_total > 0:
                opp_score = opp_results['wins'] + opp_results['draws'] * 0.5
                score_percentage = opp_score / opp_total
                
                # Very rough ELO estimation based on score percentage
                if score_percentage > 0.5:
                    rating_diff = 400 * (score_percentage - 0.5)  # Simplified formula
                    estimated_v7p3r_rating = opponent_info['estimated_rating'] + rating_diff
                elif score_percentage < 0.5:
                    rating_diff = 400 * (0.5 - score_percentage)
                    estimated_v7p3r_rating = opponent_info['estimated_rating'] - rating_diff
                else:
                    estimated_v7p3r_rating = opponent_info['estimated_rating']
                
                print(f"   vs {opponent_name} ({opponent_info['estimated_rating']} ELO): {score_percentage:.1%} → V7P3R ~{estimated_v7p3r_rating:.0f} ELO")
    
    print(f"\n⏱️ Total Time: {total_time:.1f} seconds")
    
    # Performance verdict
    if total_completed > 0:
        if score_percentage >= 75:
            print("\n🎉 EXCEPTIONAL! V7P3R shows very strong performance!")
        elif score_percentage >= 60:
            print("\n🏆 EXCELLENT! V7P3R demonstrates good strength!")
        elif score_percentage >= 40:
            print("\n👍 SOLID! V7P3R shows competitive play!")
        else:
            print("\n📈 Developing! V7P3R has room to grow!")
    
    return True

if __name__ == "__main__":
    success = run_v7p3r_quick_gauntlet()
    if success:
        print("\n✅ Quick gauntlet completed!")
    else:
        print("\n❌ Quick gauntlet failed!")
        sys.exit(1)
