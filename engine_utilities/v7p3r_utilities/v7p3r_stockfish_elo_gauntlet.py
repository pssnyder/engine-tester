#!/usr/bin/env python3
"""
Stockfish ELO Gauntlet for V7P3R Rating Assessment
==================================================

Creates a series of Stockfish opponents at different ELO ratings to:
1. Test V7P3R against a ladder of known-strength opponents
2. Find the ELO range where V7P3R wins ~50% of games
3. Calculate V7P3R's approximate rating

Stockfish UCI Options:
- UCI_LimitStrength = true (enables ELO limiting)
- UCI_Elo = 1320-3190 (target ELO rating)
- Skill Level = 0-20 (alternative strength control)
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add framework to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'automated_battle_framework'))
from engine_battle_framework import BattleFramework, ChallengeType

class StockfishELOGauntlet:
    """Manages ELO-based gauntlet testing against Stockfish"""
    
    def __init__(self):
        self.framework = BattleFramework()
        self.stockfish_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        self.v7p3r_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/V7P3R/V7P3R_v7.0.exe"
        
        # ELO test points (start conservative, expand based on results)
        self.test_elos = [
            1320,  # Minimum Stockfish ELO
            1400,  # Beginner+
            1500,  # Casual player
            1600,  # Club player
            1700,  # Strong club player
            1800,  # Expert
            1900,  # Near-master
            2000,  # Master level
            2100,  # Strong master
            2200,  # IM level
        ]
        
        self.results = {
            'test_date': datetime.now().isoformat(),
            'v7p3r_version': 'v7.0',
            'stockfish_version': '17.1',
            'battles': [],
            'estimated_elo': None,
            'confidence_range': None
        }
    
    def create_stockfish_config(self, target_elo: int) -> dict:
        """Create Stockfish configuration for specific ELO"""
        return {
            'path': self.stockfish_path,
            'name': f'Stockfish_{target_elo}_ELO',
            'uci_options': {
                'UCI_LimitStrength': 'true',
                'UCI_Elo': str(target_elo),
                'Threads': '1',  # Keep consistent for fair testing
                'Hash': '32'     # Conservative memory usage
            }
        }
    
    async def test_elo_bracket(self, target_elo: int, num_games: int = 6) -> dict:
        """Test V7P3R against Stockfish at specific ELO"""
        
        print(f"\n🎯 Testing V7P3R vs Stockfish {target_elo} ELO ({num_games} games)")
        
        stockfish_config = self.create_stockfish_config(target_elo)
        
        wins = 0
        draws = 0
        losses = 0
        game_results = []
        
        try:
            # Create battle session
            session_id = await self.framework.create_battle_session(
                f"V7P3R_vs_Stockfish_{target_elo}",
                f"ELO assessment: V7P3R v7.0 vs Stockfish {target_elo} ELO"
            )
            
            for game_num in range(num_games):
                print(f"  Game {game_num + 1}/{num_games}...", end=' ')
                
                try:
                    # Alternate colors (V7P3R plays both white and black)
                    if game_num % 2 == 0:
                        # V7P3R as white
                        result = await self.framework.run_challenge(
                            session_id,
                            ChallengeType.TRADITIONAL_CHALLENGE,
                            "V7P3R_Current",  # Will need to configure this
                            stockfish_config['name'],
                            time_limit=5.0,  # 5 seconds per move
                            max_moves=100
                        )
                        v7p3r_color = 'white'
                    else:
                        # V7P3R as black
                        result = await self.framework.run_challenge(
                            session_id,
                            ChallengeType.TRADITIONAL_CHALLENGE,
                            stockfish_config['name'],
                            "V7P3R_Current",
                            time_limit=5.0,
                            max_moves=100
                        )
                        v7p3r_color = 'black'
                    
                    # Analyze result
                    if result.winner == "V7P3R_Current":
                        wins += 1
                        outcome = "WIN"
                        print("✅ WIN")
                    elif result.winner == stockfish_config['name']:
                        losses += 1
                        outcome = "LOSS"
                        print("❌ LOSS")
                    else:
                        draws += 1
                        outcome = "DRAW"
                        print("⚫ DRAW")
                    
                    game_results.append({
                        'game': game_num + 1,
                        'v7p3r_color': v7p3r_color,
                        'outcome': outcome,
                        'moves': result.total_moves if hasattr(result, 'total_moves') else 'unknown',
                        'duration': result.execution_time
                    })
                    
                except Exception as e:
                    print(f"❌ FAILED ({e})")
                    game_results.append({
                        'game': game_num + 1,
                        'outcome': 'ERROR',
                        'error': str(e)
                    })
            
            # Calculate performance
            total_games = wins + draws + losses
            win_rate = wins / total_games if total_games > 0 else 0
            score_rate = (wins + 0.5 * draws) / total_games if total_games > 0 else 0
            
            bracket_result = {
                'target_elo': target_elo,
                'games_played': total_games,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': win_rate,
                'score_rate': score_rate,
                'performance_elo': self.calculate_performance_elo(target_elo, score_rate),
                'games': game_results
            }
            
            self.results['battles'].append(bracket_result)
            
            print(f"  📊 Results: {wins}W-{draws}D-{losses}L ({score_rate:.1%} score)")
            print(f"  📈 Performance ELO: {bracket_result['performance_elo']:.0f}")
            
            return bracket_result
            
        except Exception as e:
            print(f"💥 ELO bracket failed: {e}")
            return None
    
    def calculate_performance_elo(self, opponent_elo: int, score_rate: float) -> float:
        """Calculate performance ELO based on score against known opponent"""
        
        if score_rate >= 0.99:
            # Avoid log(0) - assume very high performance
            return opponent_elo + 400
        elif score_rate <= 0.01:
            # Avoid log(0) - assume very low performance  
            return opponent_elo - 400
        else:
            # Standard ELO calculation
            import math
            return opponent_elo + 400 * math.log10(score_rate / (1 - score_rate))
    
    async def run_progressive_gauntlet(self):
        """Run progressive ELO gauntlet to find V7P3R's rating"""
        
        print("🚀 V7P3R vs Stockfish ELO Gauntlet")
        print("=" * 50)
        print(f"V7P3R: {self.v7p3r_path}")
        print(f"Stockfish: {self.stockfish_path}")
        print(f"Test ELOs: {self.test_elos}")
        
        # Test each ELO bracket
        for target_elo in self.test_elos:
            bracket_result = await self.test_elo_bracket(target_elo, num_games=6)
            
            if bracket_result:
                score_rate = bracket_result['score_rate']
                
                # If we're getting crushed (< 20%), no need to test higher
                if score_rate < 0.2:
                    print(f"\n⚠️  V7P3R struggling at {target_elo} ELO, stopping upward progression")
                    break
                
                # If we're dominating (> 80%), continue to higher ELOs
                if score_rate > 0.8:
                    print(f"✅ V7P3R strong at {target_elo} ELO, continuing upward")
                    continue
                
                # If we're in the competitive range (20-80%), we found the zone
                if 0.3 <= score_rate <= 0.7:
                    print(f"🎯 Found competitive range around {target_elo} ELO!")
                    break
        
        # Calculate final rating estimate
        self.estimate_final_rating()
        
        # Save results
        results_file = Path("gauntlet_testing") / f"v7p3r_stockfish_elo_gauntlet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_file}")
        
        return self.results
    
    def estimate_final_rating(self):
        """Estimate V7P3R's ELO based on gauntlet results"""
        
        if not self.results['battles']:
            return
        
        # Calculate weighted average performance
        total_games = 0
        performance_sum = 0
        
        for battle in self.results['battles']:
            games = battle['games_played']
            perf_elo = battle['performance_elo']
            
            total_games += games
            performance_sum += perf_elo * games
        
        if total_games > 0:
            estimated_elo = performance_sum / total_games
            
            # Calculate confidence range based on results spread
            performances = [b['performance_elo'] for b in self.results['battles'] if b['games_played'] > 0]
            if len(performances) > 1:
                import statistics
                std_dev = statistics.stdev(performances)
                confidence_range = (estimated_elo - std_dev, estimated_elo + std_dev)
            else:
                confidence_range = (estimated_elo - 50, estimated_elo + 50)
            
            self.results['estimated_elo'] = estimated_elo
            self.results['confidence_range'] = confidence_range
            
            print(f"\n🎉 V7P3R v7.0 Estimated Rating:")
            print(f"   📈 ELO: {estimated_elo:.0f}")
            print(f"   📊 Range: {confidence_range[0]:.0f} - {confidence_range[1]:.0f}")
            

async def main():
    """Run the Stockfish ELO Gauntlet"""
    
    gauntlet = StockfishELOGauntlet()
    
    # Check if files exist
    if not Path(gauntlet.v7p3r_path).exists():
        print(f"❌ V7P3R not found: {gauntlet.v7p3r_path}")
        return
    
    if not Path(gauntlet.stockfish_path).exists():
        print(f"❌ Stockfish not found: {gauntlet.stockfish_path}")
        return
    
    try:
        results = await gauntlet.run_progressive_gauntlet()
        
        if results['estimated_elo']:
            print(f"\n🏆 SUCCESS: V7P3R rating estimated at {results['estimated_elo']:.0f} ELO")
        else:
            print("\n⚠️  Could not determine rating - need more data")
            
    except Exception as e:
        print(f"💥 Gauntlet failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
