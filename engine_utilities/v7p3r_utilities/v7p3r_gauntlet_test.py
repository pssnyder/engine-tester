#!/usr/bin/env python3
"""
V7P3R Gauntlet Testing Suite
Test V7P3R v7.0 against competition bots to validate tournament performance
"""

import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our existing battle framework components
from automated_battle_framework.engine_battle_framework import EngineBattleFramework
from automated_battle_framework.enhanced_battle_framework import SessionManager

def run_v7p3r_gauntlet_test():
    """Run a focused gauntlet test with V7P3R v7.0 against top competition bots"""
    
    print("🏟️ V7P3R v7.0 Gauntlet Challenge")
    print("=" * 60)
    
    # V7P3R engine path
    engines_dir = Path(__file__).parent.parent / "engines"
    v7p3r_path = engines_dir / "V7P3R" / "V7P3R_v7.0.exe"
    
    # Available opponent engines for gauntlet
    opponents = [
        engines_dir / "SlowMate" / "SlowMate_v3.0.exe",
        engines_dir / "C0BR4" / "C0BR4_v2.1.exe",
        engines_dir / "V7P3R" / "V7P3R_v6.1.exe",  # Test against older version
        engines_dir / "V7P3R" / "V7P3R_v6.0.exe",  # Multiple versions for progression
    ]
    
    # Verify engines exist
    missing_engines = []
    if not v7p3r_path.exists():
        missing_engines.append(str(v7p3r_path))
    
    available_opponents = []
    for opponent in opponents:
        if opponent.exists():
            available_opponents.append(opponent)
        else:
            missing_engines.append(str(opponent))
    
    if missing_engines:
        print("❌ Missing engines:")
        for engine in missing_engines:
            print(f"   {engine}")
        
    if not available_opponents:
        print("❌ No opponent engines available!")
        return False
    
    print(f"✓ V7P3R Engine: {v7p3r_path}")
    print(f"✓ Available Opponents: {len(available_opponents)}")
    for opponent in available_opponents:
        print(f"   - {opponent.stem}")
    
    # Configure gauntlet parameters
    gauntlet_config = {
        'rounds_per_opponent': 4,  # 2 as White, 2 as Black
        'time_control': '5+3',     # 5 minutes + 3 second increment
        'max_moves': 200,          # Reasonable game length limit
        'adjudication_threshold': 500,  # Centipawn advantage for adjudication
        'save_pgn': True,
        'verbose': True
    }
    
    print(f"\n🎯 Gauntlet Configuration:")
    print(f"   Rounds per Opponent: {gauntlet_config['rounds_per_opponent']}")
    print(f"   Time Control: {gauntlet_config['time_control']}")
    print(f"   Max Moves: {gauntlet_config['max_moves']}")
    print(f"   Total Games: {len(available_opponents) * gauntlet_config['rounds_per_opponent']}")
    
    # Initialize battle framework
    print(f"\n⚔️ Initializing Battle Framework...")
    
    try:
        # Use our existing battle framework
        session_manager = SessionManager()
        framework = EngineBattleFramework()
        
        # Create gauntlet session
        session_id = session_manager.create_session(
            session_type='gauntlet',
            description=f"V7P3R v7.0 Gauntlet vs {len(available_opponents)} opponents"
        )
        
        print(f"✓ Session Created: {session_id}")
        
        # Run gauntlet matches
        print(f"\n🏁 Starting Gauntlet Matches...")
        print("-" * 60)
        
        total_results = {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'errors': 0,
            'total_games': 0,
            'white_record': {'wins': 0, 'losses': 0, 'draws': 0},
            'black_record': {'wins': 0, 'losses': 0, 'draws': 0},
            'opponent_results': {}
        }
        
        start_time = time.time()
        
        for i, opponent_path in enumerate(available_opponents, 1):
            opponent_name = opponent_path.stem
            print(f"\n[{i}/{len(available_opponents)}] Fighting {opponent_name}")
            print(f"{'='*40}")
            
            opponent_results = {
                'wins': 0, 'losses': 0, 'draws': 0, 'errors': 0,
                'white': {'wins': 0, 'losses': 0, 'draws': 0},
                'black': {'wins': 0, 'losses': 0, 'draws': 0}
            }
            
            # Run multiple rounds against this opponent
            for round_num in range(gauntlet_config['rounds_per_opponent']):
                # Alternate colors - odd rounds as White, even as Black
                v7p3r_as_white = (round_num % 2 == 0)
                
                if v7p3r_as_white:
                    white_engine = str(v7p3r_path)
                    black_engine = str(opponent_path)
                    color_info = "V7P3R(W) vs"
                else:
                    white_engine = str(opponent_path)
                    black_engine = str(v7p3r_path)
                    color_info = "V7P3R(B) vs"
                
                print(f"\n   Round {round_num + 1}: {color_info} {opponent_name}")
                
                try:
                    # Create battle configuration
                    battle_config = {
                        'challenge_type': 'traditional',
                        'time_limit': 300,      # 5 minutes base
                        'increment': 3,         # 3 second increment
                        'max_moves': gauntlet_config['max_moves'],
                        'adjudication_threshold': gauntlet_config['adjudication_threshold']
                    }
                    
                    # Run the battle
                    battle_result = framework.run_battle(
                        white_engine_path=white_engine,
                        black_engine_path=black_engine,
                        config=battle_config,
                        session_id=session_id
                    )
                    
                    # Process result
                    if battle_result['status'] == 'completed':
                        game_result = battle_result['result']
                        
                        # Determine V7P3R's result
                        if v7p3r_as_white:
                            if game_result == '1-0':  # White wins
                                v7p3r_result = 'win'
                                opponent_results['white']['wins'] += 1
                            elif game_result == '0-1':  # Black wins
                                v7p3r_result = 'loss'
                                opponent_results['white']['losses'] += 1
                            else:  # Draw
                                v7p3r_result = 'draw'
                                opponent_results['white']['draws'] += 1
                        else:  # V7P3R as Black
                            if game_result == '0-1':  # Black wins
                                v7p3r_result = 'win'
                                opponent_results['black']['wins'] += 1
                            elif game_result == '1-0':  # White wins
                                v7p3r_result = 'loss'
                                opponent_results['black']['losses'] += 1
                            else:  # Draw
                                v7p3r_result = 'draw'
                                opponent_results['black']['draws'] += 1
                        
                        # Update counters
                        opponent_results[v7p3r_result + 's'] += 1
                        total_results[v7p3r_result + 's'] += 1
                        
                        # Update color-specific totals
                        color_key = 'white_record' if v7p3r_as_white else 'black_record'
                        total_results[color_key][v7p3r_result + 's'] += 1
                        
                        # Status symbol
                        symbol = "✓" if v7p3r_result == 'win' else "✗" if v7p3r_result == 'loss' else "="
                        print(f"     {symbol} {v7p3r_result.upper()} ({battle_result.get('moves', 0)} moves)")
                        
                    else:
                        # Error occurred
                        opponent_results['errors'] += 1
                        total_results['errors'] += 1
                        print(f"     ❌ ERROR: {battle_result.get('error', 'Unknown error')}")
                    
                    total_results['total_games'] += 1
                    
                except Exception as e:
                    print(f"     ❌ EXCEPTION: {e}")
                    opponent_results['errors'] += 1
                    total_results['errors'] += 1
                    total_results['total_games'] += 1
            
            # Store opponent results
            total_results['opponent_results'][opponent_name] = opponent_results
            
            # Print opponent summary
            opp_total = opponent_results['wins'] + opponent_results['losses'] + opponent_results['draws']
            if opp_total > 0:
                win_rate = opponent_results['wins'] / opp_total * 100
                print(f"\n   vs {opponent_name}: {opponent_results['wins']}-{opponent_results['losses']}-{opponent_results['draws']} ({win_rate:.1f}% win rate)")
        
        # Final summary
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🏆 GAUNTLET RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"\n📊 Overall Performance:")
        total_completed = total_results['wins'] + total_results['losses'] + total_results['draws']
        if total_completed > 0:
            win_rate = total_results['wins'] / total_completed * 100
            score = total_results['wins'] + total_results['draws'] * 0.5
            score_percentage = score / total_completed * 100
            
            print(f"   Games: {total_completed} completed, {total_results['errors']} errors")
            print(f"   Record: {total_results['wins']}-{total_results['losses']}-{total_results['draws']}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Score: {score:.1f}/{total_completed} ({score_percentage:.1f}%)")
        
        # Color-specific analysis
        white_stats = total_results['white_record']
        black_stats = total_results['black_record']
        
        white_total = white_stats['wins'] + white_stats['losses'] + white_stats['draws']
        black_total = black_stats['wins'] + black_stats['losses'] + black_stats['draws']
        
        print(f"\n🎨 Performance by Color:")
        if white_total > 0:
            white_win_rate = white_stats['wins'] / white_total * 100
            print(f"   As White: {white_stats['wins']}-{white_stats['losses']}-{white_stats['draws']} ({white_win_rate:.1f}% win rate)")
        
        if black_total > 0:
            black_win_rate = black_stats['wins'] / black_total * 100
            print(f"   As Black: {black_stats['wins']}-{black_stats['losses']}-{black_stats['draws']} ({black_win_rate:.1f}% win rate)")
        
        # Opponent breakdown
        print(f"\n🤖 Performance vs Each Opponent:")
        for opponent_name, opp_results in total_results['opponent_results'].items():
            opp_total = opp_results['wins'] + opp_results['losses'] + opp_results['draws']
            if opp_total > 0:
                opp_win_rate = opp_results['wins'] / opp_total * 100
                print(f"   vs {opponent_name}: {opp_results['wins']}-{opp_results['losses']}-{opp_results['draws']} ({opp_win_rate:.1f}%)")
        
        print(f"\n⏱️ Total Test Time: {total_time:.1f} seconds")
        print(f"📈 Average Game Time: {total_time/max(total_completed, 1):.1f}s")
        
        # Performance assessment
        if total_completed > 0:
            if win_rate >= 80:
                print("\n🎉 OUTSTANDING! Dominant gauntlet performance!")
            elif win_rate >= 60:
                print("\n🏆 EXCELLENT! Strong gauntlet showing!")
            elif win_rate >= 40:
                print("\n👍 GOOD! Competitive gauntlet performance!")
            else:
                print("\n📈 Room for improvement. Keep working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Gauntlet test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_v7p3r_gauntlet_test()
    if success:
        print("\n✅ Gauntlet test completed!")
    else:
        print("\n❌ Gauntlet test failed!")
        sys.exit(1)
