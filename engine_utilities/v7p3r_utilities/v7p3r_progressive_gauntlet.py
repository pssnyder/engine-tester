#!/usr/bin/env python3
"""
V7P3R Progressive Rating Gauntlet
Test V7P3R v7.0 against engines of increasing strength to establish rating baseline
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

def run_v7p3r_progressive_gauntlet():
    """Run V7P3R v7.0 against progressively stronger opponents to estimate rating"""
    
    print("🎯 V7P3R v7.0 Progressive Rating Gauntlet")
    print("=" * 70)
    
    # Define opponents in order of estimated strength
    base_dir = Path(__file__).parent
    engines_dir = base_dir / "engines"
    downloaded_dir = base_dir / "downloaded_engines"
    
    # Progressive opponent ladder with estimated ratings
    opponents = [
        {
            'name': 'Random_Opponent',
            'path': engines_dir / "Opponents" / "Random_Opponent.exe",
            'estimated_elo': 600,
            'description': 'Random move engine - baseline test'
        },
        {
            'name': 'SlowMate_v0.0.0',
            'path': engines_dir / "SlowMate" / "SlowMate_v0.0.0.exe",
            'estimated_elo': 800,
            'description': 'Early SlowMate version'
        },
        {
            'name': 'SlowMate_v1.0',
            'path': engines_dir / "SlowMate" / "Slowmate_v1.0.exe",
            'estimated_elo': 1200,
            'description': 'SlowMate stable release'
        },
        {
            'name': 'V7P3R_v5.0',
            'path': engines_dir / "V7P3R" / "V7P3R_v5.0.exe",
            'estimated_elo': 1400,
            'description': 'V7P3R older version baseline'
        },
        {
            'name': 'SlowMate_v3.0',
            'path': engines_dir / "SlowMate" / "SlowMate_v3.0.exe",
            'estimated_elo': 1800,
            'description': 'Current SlowMate version'
        },
        {
            'name': 'V7P3R_v6.1',
            'path': engines_dir / "V7P3R" / "V7P3R_v6.1.exe",
            'estimated_elo': 2000,
            'description': 'Previous V7P3R version'
        },
        {
            'name': 'C0BR4_v2.1',
            'path': engines_dir / "C0BR4" / "C0BR4_v2.1.exe",
            'estimated_elo': 2200,
            'description': 'Advanced tournament engine'
        },
        {
            'name': 'Stockfish_17.1',
            'path': downloaded_dir / "stockfish" / "stockfish-windows-x86-64-avx2.exe",
            'estimated_elo': 3500,
            'description': 'World champion engine (strength limited)'
        }
    ]
    
    # V7P3R test engine
    v7p3r_path = engines_dir / "V7P3R" / "V7P3R_v7.0.exe"
    
    if not v7p3r_path.exists():
        print(f"❌ V7P3R v7.0 not found: {v7p3r_path}")
        return False
    
    print(f"✓ Test Engine: V7P3R v7.0")
    print(f"📍 Path: {v7p3r_path}")
    
    # Check which opponents are available
    available_opponents = []
    for opponent in opponents:
        if opponent['path'].exists():
            available_opponents.append(opponent)
            print(f"✓ {opponent['name']}: ~{opponent['estimated_elo']} ELO - {opponent['description']}")
        else:
            print(f"❌ {opponent['name']}: Not found")
    
    if not available_opponents:
        print("\n❌ No opponents available for testing!")
        return False
    
    print(f"\n🎯 Gauntlet Configuration:")
    print(f"   Available Opponents: {len(available_opponents)}")
    print(f"   Games per Opponent: 6 (3 as White, 3 as Black)")
    print(f"   Time Control: 5+3 (5 min + 3 sec increment)")
    print(f"   Total Estimated Games: {len(available_opponents) * 6}")
    print(f"   Format: Progressive ladder testing")
    
    # Results tracking
    gauntlet_results = {
        'start_time': datetime.now().isoformat(),
        'v7p3r_version': 'v7.0',
        'opponents_tested': [],
        'overall_stats': {'wins': 0, 'losses': 0, 'draws': 0, 'errors': 0},
        'rating_estimates': [],
        'performance_curve': []
    }
    
    print(f"\n⚔️ Starting Progressive Gauntlet...")
    print("=" * 70)
    
    start_time = time.time()
    
    for i, opponent in enumerate(available_opponents, 1):
        print(f"\n🎮 ROUND {i}/{len(available_opponents)}: V7P3R v7.0 vs {opponent['name']}")
        print(f"   Target Rating: ~{opponent['estimated_elo']} ELO")
        print(f"   Description: {opponent['description']}")
        print("-" * 50)
        
        round_results = {
            'opponent_name': opponent['name'],
            'opponent_elo': opponent['estimated_elo'],
            'games': [],
            'wins': 0, 'losses': 0, 'draws': 0, 'errors': 0,
            'white_performance': {'wins': 0, 'losses': 0, 'draws': 0},
            'black_performance': {'wins': 0, 'losses': 0, 'draws': 0}
        }
        
        # Play 6 games: 3 as White, 3 as Black
        for game_num in range(6):
            v7p3r_as_white = (game_num < 3)
            color_str = "White" if v7p3r_as_white else "Black"
            game_id = f"{i}.{game_num + 1}"
            
            print(f"\n   Game {game_id}: V7P3R as {color_str} vs {opponent['name']}")
            
            try:
                # Use our battle framework via command line
                if v7p3r_as_white:
                    white_engine = str(v7p3r_path)
                    black_engine = str(opponent['path'])
                else:
                    white_engine = str(opponent['path'])
                    black_engine = str(v7p3r_path)
                
                # Run battle using our existing framework
                battle_cmd = [
                    'python',
                    str(base_dir / 'automated_battle_framework' / 'simple_test.py'),
                    '--timeout', '600'  # 10 minute timeout per game
                ]
                
                game_start = time.time()
                
                # Create a simple subprocess call to our battle framework
                # (This is a simplified approach - in production we'd use the API directly)
                result = subprocess.run([
                    'python', '-c', f'''
import sys
sys.path.append(r"{base_dir / 'automated_battle_framework'}")
from engine_battle_framework import EngineBattleFramework

framework = EngineBattleFramework()
result = framework.simple_battle(
    white_engine=r"{white_engine}",
    black_engine=r"{black_engine}",
    time_limit=300,
    increment=3
)
print(f"RESULT:{{result}}")
'''
                ], capture_output=True, text=True, timeout=600)
                
                game_time = time.time() - game_start
                
                if result.returncode == 0:
                    # Parse result (simplified)
                    output = result.stdout
                    
                    # Extract game result
                    if "1-0" in output or "White wins" in output:
                        game_result = "1-0"
                    elif "0-1" in output or "Black wins" in output:
                        game_result = "0-1"
                    elif "1/2-1/2" in output or "Draw" in output:
                        game_result = "1/2-1/2"
                    else:
                        game_result = "ERROR"
                    
                    # Determine V7P3R's result
                    if game_result == "ERROR":
                        v7p3r_result = "error"
                        round_results['errors'] += 1
                        gauntlet_results['overall_stats']['errors'] += 1
                    elif v7p3r_as_white:
                        if game_result == "1-0":
                            v7p3r_result = "win"
                            round_results['wins'] += 1
                            round_results['white_performance']['wins'] += 1
                            gauntlet_results['overall_stats']['wins'] += 1
                        elif game_result == "0-1":
                            v7p3r_result = "loss"
                            round_results['losses'] += 1
                            round_results['white_performance']['losses'] += 1
                            gauntlet_results['overall_stats']['losses'] += 1
                        else:
                            v7p3r_result = "draw"
                            round_results['draws'] += 1
                            round_results['white_performance']['draws'] += 1
                            gauntlet_results['overall_stats']['draws'] += 1
                    else:  # V7P3R as Black
                        if game_result == "0-1":
                            v7p3r_result = "win"
                            round_results['wins'] += 1
                            round_results['black_performance']['wins'] += 1
                            gauntlet_results['overall_stats']['wins'] += 1
                        elif game_result == "1-0":
                            v7p3r_result = "loss"
                            round_results['losses'] += 1
                            round_results['black_performance']['losses'] += 1
                            gauntlet_results['overall_stats']['losses'] += 1
                        else:
                            v7p3r_result = "draw"
                            round_results['draws'] += 1
                            round_results['black_performance']['draws'] += 1
                            gauntlet_results['overall_stats']['draws'] += 1
                    
                    # Record game
                    round_results['games'].append({
                        'game_number': game_num + 1,
                        'v7p3r_color': color_str.lower(),
                        'result': v7p3r_result,
                        'game_result': game_result,
                        'duration': game_time
                    })
                    
                    # Status display
                    symbol = "✓" if v7p3r_result == "win" else "✗" if v7p3r_result == "loss" else "=" if v7p3r_result == "draw" else "❌"
                    print(f"      {symbol} {v7p3r_result.upper()} ({game_result}) in {game_time:.1f}s")
                    
                else:
                    print(f"      ❌ ERROR: Battle failed ({result.returncode})")
                    round_results['errors'] += 1
                    gauntlet_results['overall_stats']['errors'] += 1
                    
            except subprocess.TimeoutExpired:
                print(f"      ⏰ TIMEOUT: Game exceeded time limit")
                round_results['errors'] += 1
                gauntlet_results['overall_stats']['errors'] += 1
            except Exception as e:
                print(f"      ❌ EXCEPTION: {e}")
                round_results['errors'] += 1
                gauntlet_results['overall_stats']['errors'] += 1
        
        # Round summary
        total_games = round_results['wins'] + round_results['losses'] + round_results['draws']
        if total_games > 0:
            score = round_results['wins'] + round_results['draws'] * 0.5
            score_percentage = score / total_games * 100
            
            print(f"\n   📊 Round Summary vs {opponent['name']} (~{opponent['estimated_elo']} ELO):")
            print(f"      Record: {round_results['wins']}-{round_results['losses']}-{round_results['draws']}")
            print(f"      Score: {score:.1f}/{total_games} ({score_percentage:.1f}%)")
            
            # Rough rating estimate based on performance
            if score_percentage > 50:
                rating_estimate = opponent['estimated_elo'] + (score_percentage - 50) * 8  # Rough formula
            else:
                rating_estimate = opponent['estimated_elo'] - (50 - score_percentage) * 8
            
            print(f"      Estimated V7P3R Rating: ~{rating_estimate:.0f} ELO")
            
            gauntlet_results['rating_estimates'].append({
                'opponent': opponent['name'],
                'opponent_elo': opponent['estimated_elo'],
                'score_percentage': score_percentage,
                'estimated_v7p3r_elo': rating_estimate
            })
        
        gauntlet_results['opponents_tested'].append(round_results)
        
        # Performance curve tracking
        cumulative_games = gauntlet_results['overall_stats']['wins'] + gauntlet_results['overall_stats']['losses'] + gauntlet_results['overall_stats']['draws']
        if cumulative_games > 0:
            cumulative_score = gauntlet_results['overall_stats']['wins'] + gauntlet_results['overall_stats']['draws'] * 0.5
            cumulative_percentage = cumulative_score / cumulative_games * 100
            
            gauntlet_results['performance_curve'].append({
                'after_opponent': opponent['name'],
                'cumulative_games': cumulative_games,
                'cumulative_score_percentage': cumulative_percentage
            })
    
    # Final analysis
    end_time = time.time()
    total_time = end_time - start_time
    gauntlet_results['end_time'] = datetime.now().isoformat()
    gauntlet_results['total_duration'] = total_time
    
    print("\n" + "=" * 70)
    print("🏆 V7P3R v7.0 PROGRESSIVE GAUNTLET RESULTS")
    print("=" * 70)
    
    # Overall statistics
    overall = gauntlet_results['overall_stats']
    total_completed = overall['wins'] + overall['losses'] + overall['draws']
    
    if total_completed > 0:
        overall_score = overall['wins'] + overall['draws'] * 0.5
        overall_percentage = overall_score / total_completed * 100
        
        print(f"\n📊 Overall Performance:")
        print(f"   Total Games: {total_completed} (+ {overall['errors']} errors)")
        print(f"   Record: {overall['wins']}-{overall['losses']}-{overall['draws']}")
        print(f"   Overall Score: {overall_score:.1f}/{total_completed} ({overall_percentage:.1f}%)")
    
    # Rating estimates analysis
    if gauntlet_results['rating_estimates']:
        print(f"\n📈 Rating Estimation Analysis:")
        estimates = gauntlet_results['rating_estimates']
        
        for est in estimates:
            print(f"   vs {est['opponent']} ({est['opponent_elo']} ELO): {est['score_percentage']:.1f}% → ~{est['estimated_v7p3r_elo']:.0f} ELO")
        
        # Average estimate
        avg_estimate = sum(est['estimated_v7p3r_elo'] for est in estimates) / len(estimates)
        print(f"\n   🎯 Average Estimated Rating: ~{avg_estimate:.0f} ELO")
        
        # Rating range
        min_estimate = min(est['estimated_v7p3r_elo'] for est in estimates)
        max_estimate = max(est['estimated_v7p3r_elo'] for est in estimates)
        print(f"   📊 Rating Range: {min_estimate:.0f} - {max_estimate:.0f} ELO")
    
    # Performance assessment
    print(f"\n🎖️ Performance Assessment:")
    if avg_estimate >= 2500:
        print("   🏆 MASTER LEVEL: V7P3R shows master-level strength!")
    elif avg_estimate >= 2000:
        print("   🥇 EXPERT LEVEL: V7P3R demonstrates expert-level play!")
    elif avg_estimate >= 1500:
        print("   🥈 ADVANCED LEVEL: V7P3R shows strong intermediate play!")
    elif avg_estimate >= 1000:
        print("   🥉 INTERMEDIATE LEVEL: V7P3R demonstrates solid fundamentals!")
    else:
        print("   📚 DEVELOPING: V7P3R is building foundational strength!")
    
    print(f"\n⏱️ Total Test Duration: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    
    # Save results
    results_dir = base_dir / "gauntlet_testing" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"v7p3r_progressive_gauntlet_{timestamp}.json"
    
    import json
    with open(results_file, 'w') as f:
        json.dump(gauntlet_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return True

if __name__ == "__main__":
    success = run_v7p3r_progressive_gauntlet()
    if success:
        print("\n✅ Progressive gauntlet completed successfully!")
    else:
        print("\n❌ Progressive gauntlet failed!")
        sys.exit(1)
