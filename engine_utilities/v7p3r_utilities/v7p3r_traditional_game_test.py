#!/usr/bin/env python3
"""
V7P3R Traditional Game Test
==========================

Test V7P3R in a traditional game format instead of speed challenges.
Speed challenges might not be the right metric for chess strength.
"""

import asyncio
import sys
from pathlib import Path

# Add framework to path
sys.path.append(str(Path(__file__).parent / 'automated_battle_framework'))

from engine_battle_framework import BattleFramework, ChallengeType, EngineConfig, EngineType

async def test_traditional_game():
    """Test V7P3R vs SlowMate in traditional game format"""
    
    print("♟️  V7P3R Traditional Game Test")
    print("=" * 35)
    
    framework = BattleFramework()
    
    # Create session
    session_id = await framework.create_battle_session(
        "V7P3R_Traditional_Test",
        "V7P3R vs SlowMate traditional game"
    )
    
    print(f"🎮 Running traditional game test...")
    print("   V7P3R vs SlowMate (traditional game)")
    print("   Time control: 30 seconds per move")
    print("   Max moves: 50")
    
    try:
        result = await framework.run_challenge(
            session_id,
            ChallengeType.TRADITIONAL_GAME,
            "V7P3R_Current",
            "SlowMate_Current",
            time_control=30.0,  # 30 seconds per move
            max_moves=50        # Reasonable game length
        )
        
        if result:
            print(f"\n📊 Game Results:")
            print(f"   Winner: {result.winner}")
            print(f"   Game duration: {result.execution_time:.1f}s")
            print(f"   Status: {result.status.value}")
            
            # Examine game details
            if hasattr(result, 'result_details') and result.result_details:
                details = result.result_details
                print(f"\n🔍 Game Analysis:")
                
                if 'move_count' in details:
                    moves = details['move_count']
                    print(f"   Total moves: {moves}")
                
                if 'game_pgn' in details:
                    pgn = details['game_pgn']
                    print(f"   PGN available: {len(pgn) > 0}")
                    if pgn and len(pgn) < 500:  # Only print if reasonably short
                        print(f"   PGN: {pgn}")
                
                if 'end_reason' in details:
                    end_reason = details['end_reason']
                    print(f"   End reason: {end_reason}")
            
            # Performance analysis
            if result.winner == "V7P3R_Current":
                print(f"\n✅ V7P3R won the traditional game!")
                print(f"🎉 This suggests V7P3R is stronger in actual games vs speed tests")
            elif result.winner == "SlowMate_Current":
                print(f"\n❌ SlowMate won the traditional game")
                print(f"📉 V7P3R may need performance improvements")
            else:
                print(f"\n⚫ Game ended in draw")
                print(f"🤝 Engines are evenly matched")
        
        else:
            print("❌ Traditional game test failed")
    
    except Exception as e:
        print(f"💥 Traditional game test crashed: {e}")
        import traceback
        traceback.print_exc()


async def test_multiple_games():
    """Test multiple traditional games for better assessment"""
    
    print(f"\n🎯 Multiple Traditional Games Test")
    print("=" * 40)
    
    framework = BattleFramework()
    
    wins = 0
    draws = 0
    losses = 0
    num_games = 3
    
    for game_num in range(1, num_games + 1):
        print(f"\n🎮 Game {game_num}/{num_games}:")
        
        # Create session
        session_id = await framework.create_battle_session(
            f"V7P3R_Game_{game_num}",
            f"V7P3R vs SlowMate Game {game_num}"
        )
        
        try:
            # Alternate colors
            if game_num % 2 == 1:
                white_engine = "V7P3R_Current"
                black_engine = "SlowMate_Current"
                print(f"   V7P3R (white) vs SlowMate (black)")
            else:
                white_engine = "SlowMate_Current"
                black_engine = "V7P3R_Current"
                print(f"   SlowMate (white) vs V7P3R (black)")
            
            result = await framework.run_challenge(
                session_id,
                ChallengeType.TRADITIONAL_GAME,
                white_engine,
                black_engine,
                time_control=15.0,  # 15 seconds per move
                max_moves=40        # Shorter games
            )
            
            if result:
                # Determine V7P3R result
                if result.winner == "V7P3R_Current":
                    wins += 1
                    print(f"   ✅ V7P3R wins")
                elif result.winner == "SlowMate_Current":
                    losses += 1
                    print(f"   ❌ SlowMate wins")
                else:
                    draws += 1
                    print(f"   ⚫ Draw")
                
                # Brief game info
                duration = result.execution_time
                details = getattr(result, 'result_details', {})
                moves = details.get('move_count', 'unknown')
                print(f"   Duration: {duration:.1f}s, Moves: {moves}")
            
            else:
                print(f"   💥 Game {game_num} failed")
        
        except Exception as e:
            print(f"   💥 Game {game_num} crashed: {e}")
    
    # Summary
    total_games = wins + draws + losses
    if total_games > 0:
        score_rate = (wins + 0.5 * draws) / total_games
        
        print(f"\n📊 Traditional Games Summary:")
        print(f"   Games played: {total_games}")
        print(f"   V7P3R score: {wins}W-{draws}D-{losses}L ({score_rate:.1%})")
        
        if score_rate > 0.6:
            print(f"   ✅ V7P3R shows strength in traditional games")
            print(f"   💡 Speed challenges may not reflect true chess strength")
        elif score_rate > 0.4:
            print(f"   ⚖️  V7P3R competitive in traditional games")
        else:
            print(f"   ❌ V7P3R struggles even in traditional games")


async def main():
    """Run traditional game tests"""
    
    try:
        # Single detailed game first
        await test_traditional_game()
        
        # Multiple games for statistical sample
        await test_multiple_games()
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
    except Exception as e:
        print(f"\n💥 Tests crashed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
