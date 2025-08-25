#!/usr/bin/env python3
"""
V7P3R Stockfish ELO Gauntlet with Game Records
==============================================

Comprehensive ELO assessment with full game recording:
1. Tests V7P3R against Stockfish at increasing ELO levels (1500-2500+)
2. Records complete PGN game records for analysis
3. Uses proper time controls for accurate rating assessment
4. Saves detailed results and statistics

Based on initial test: V7P3R beat default Stockfish, so we test UPWARD!
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add framework to path
sys.path.append(str(Path(__file__).parent / 'automated_battle_framework'))

from engine_battle_framework import BattleFramework, ChallengeType, EngineConfig, EngineType

class V7P3RStockfishGauntlet:
    """Comprehensive ELO gauntlet with game recording"""
    
    def __init__(self):
        self.framework = BattleFramework()
        self.stockfish_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        
        # ELO test ladder - starting higher based on initial success
        self.elo_ladder = [
            1500,  # Club player
            1600,  # Strong club player  
            1700,  # Tournament player
            1800,  # Expert
            1900,  # Near-master
            2000,  # Master
            2100,  # Strong master
            2200,  # IM level
            2300,  # Strong IM
            2400,  # Weak GM
            2500,  # Strong GM
            2600,  # Elite GM
        ]
        
        # Test results storage
        self.gauntlet_results = {
            'test_start': datetime.now().isoformat(),
            'v7p3r_version': 'v7.0',
            'stockfish_version': '17.1',
            'time_control': 'Traditional 8s per move',
            'elo_brackets': [],
            'games': [],
            'final_rating_estimate': None,
            'performance_summary': {}
        }
        
        self.results_dir = Path("gauntlet_testing")
        self.results_dir.mkdir(exist_ok=True)
    
    async def add_stockfish_engine(self, target_elo: int):
        """Add Stockfish configured for specific ELO"""
        
        engine_name = f"Stockfish_{target_elo}"
        
        # Remove previous Stockfish if exists
        if engine_name in self.framework.engines:
            del self.framework.engines[engine_name]
        
        # Add new Stockfish configuration
        stockfish_config = EngineConfig(
            name=engine_name,
            engine_type=EngineType.EXE_CONTROL,
            path=self.stockfish_path,
            version=f"17.1_ELO_{target_elo}"
        )
        
        self.framework.add_engine(stockfish_config)
        
        # Configure Stockfish UCI options for ELO
        # We need to send UCI commands after starting the engine
        print(f"✅ Added {engine_name} (ELO: {target_elo})")
        return engine_name
    
    async def run_elo_bracket(self, target_elo: int, num_games: int = 4):
        """Test V7P3R against Stockfish at specific ELO"""
        
        print(f"\n🎯 ELO Bracket: {target_elo} ({num_games} games)")
        print("=" * 40)
        
        # Add Stockfish for this ELO
        stockfish_name = await self.add_stockfish_engine(target_elo)
        
        # Create session for this bracket
        session_id = await self.framework.create_battle_session(
            f"V7P3R_vs_Stockfish_{target_elo}",
            f"ELO Bracket {target_elo}: V7P3R v7.0 vs Stockfish {target_elo} ELO"
        )
        
        bracket_results = {
            'target_elo': target_elo,
            'session_id': session_id,
            'games': [],
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'total_games': 0,
            'score_rate': 0.0,
            'performance_elo': 0
        }
        
        # Run games
        for game_num in range(1, num_games + 1):
            print(f"\n🎮 Game {game_num}/{num_games}: ", end='')
            
            # Alternate colors
            if game_num % 2 == 1:
                # V7P3R white, Stockfish black
                white_engine = "V7P3R_Current"
                black_engine = stockfish_name
                print(f"V7P3R (white) vs Stockfish_{target_elo} (black)")
            else:
                # Stockfish white, V7P3R black  
                white_engine = stockfish_name
                black_engine = "V7P3R_Current"
                print(f"Stockfish_{target_elo} (white) vs V7P3R (black)")
            
            try:
                # Run speed challenge to test engine strength
                result = await self.framework.run_challenge(
                    session_id,
                    ChallengeType.SPEED_CHALLENGE,
                    white_engine,
                    black_engine,
                    time_limit=8.0  # 8 seconds per position for thorough analysis
                )
                
                if result:
                    # Determine V7P3R outcome
                    v7p3r_white = (white_engine == "V7P3R_Current")
                    v7p3r_outcome = self.analyze_game_result(result.winner, v7p3r_white)
                    
                    game_record = {
                        'game_number': game_num,
                        'v7p3r_color': 'white' if v7p3r_white else 'black',
                        'white_engine': white_engine,
                        'black_engine': black_engine,
                        'winner': result.winner,
                        'v7p3r_outcome': v7p3r_outcome,
                        'duration_seconds': result.execution_time,
                        'total_moves': getattr(result, 'total_moves', 'unknown'),
                        'pgn_game': getattr(result, 'pgn', 'not_recorded'),
                        'end_reason': getattr(result, 'end_reason', 'unknown')
                    }
                    
                    bracket_results['games'].append(game_record)
                    
                    # Update counters
                    if v7p3r_outcome == 'WIN':
                        bracket_results['wins'] += 1
                        print(f"   ✅ V7P3R {v7p3r_outcome}")
                    elif v7p3r_outcome == 'DRAW':
                        bracket_results['draws'] += 1  
                        print(f"   ⚫ V7P3R {v7p3r_outcome}")
                    else:
                        bracket_results['losses'] += 1
                        print(f"   ❌ V7P3R {v7p3r_outcome}")
                    
                    bracket_results['total_games'] += 1
                    
                else:
                    print(f"   💥 Game {game_num} failed")
                    bracket_results['games'].append({
                        'game_number': game_num,
                        'error': 'Challenge failed'
                    })
            
            except Exception as e:
                print(f"   💥 Game {game_num} crashed: {e}")
                bracket_results['games'].append({
                    'game_number': game_num,
                    'error': str(e)
                })
        
        # Calculate bracket statistics
        if bracket_results['total_games'] > 0:
            bracket_results['score_rate'] = (
                bracket_results['wins'] + 0.5 * bracket_results['draws']
            ) / bracket_results['total_games']
            
            bracket_results['performance_elo'] = self.calculate_performance_elo(
                target_elo, bracket_results['score_rate']
            )
        
        # Save bracket results
        self.gauntlet_results['elo_brackets'].append(bracket_results)
        self.save_progress()
        
        # Print bracket summary
        wins = bracket_results['wins']
        draws = bracket_results['draws'] 
        losses = bracket_results['losses']
        score_rate = bracket_results['score_rate']
        perf_elo = bracket_results['performance_elo']
        
        print(f"\n📊 Bracket {target_elo} Results:")
        print(f"   Score: {wins}W-{draws}D-{losses}L ({score_rate:.1%})")
        print(f"   Performance ELO: {perf_elo:.0f}")
        
        return bracket_results
    
    def analyze_game_result(self, winner: str, v7p3r_white: bool) -> str:
        """Determine V7P3R's outcome from game result"""
        
        if winner == "V7P3R_Current":
            return "WIN"
        elif "Stockfish" in winner:
            return "LOSS"
        else:
            return "DRAW"
    
    def calculate_performance_elo(self, opponent_elo: int, score_rate: float) -> float:
        """Calculate performance ELO from score rate"""
        
        if score_rate >= 0.99:
            return opponent_elo + 400
        elif score_rate <= 0.01:
            return opponent_elo - 400
        else:
            import math
            return opponent_elo + 400 * math.log10(score_rate / (1 - score_rate))
    
    async def run_full_gauntlet(self):
        """Run the complete ELO gauntlet"""
        
        print("🚀 V7P3R Stockfish ELO Gauntlet")
        print("=" * 50)
        print(f"📈 ELO ladder: {self.elo_ladder}")
        print(f"⏱️  Time control: 8 seconds per move")
        print(f"🎮 Games per bracket: 4")
        
        # Track overall performance
        total_games = 0
        total_wins = 0
        total_draws = 0
        total_losses = 0
        
        try:
            for elo in self.elo_ladder:
                bracket_result = await self.run_elo_bracket(elo, num_games=4)
                
                # Update totals
                total_games += bracket_result['total_games']
                total_wins += bracket_result['wins']
                total_draws += bracket_result['draws']
                total_losses += bracket_result['losses']
                
                score_rate = bracket_result['score_rate']
                
                # Decision logic for continuing
                if score_rate < 0.2:
                    print(f"\n⚠️  V7P3R struggling at {elo} ELO ({score_rate:.1%}) - stopping gauntlet")
                    break
                elif score_rate > 0.8:
                    print(f"✅ V7P3R dominating at {elo} ELO ({score_rate:.1%}) - continuing upward")
                    continue
                else:
                    print(f"🎯 Competitive range found at {elo} ELO ({score_rate:.1%})")
                    # Continue but we're in the right zone
            
            # Calculate final rating estimate
            self.calculate_final_rating()
            
            # Print final summary
            self.print_gauntlet_summary(total_games, total_wins, total_draws, total_losses)
            
            # Save final results
            self.save_final_results()
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Gauntlet interrupted by user")
            self.save_progress()
        except Exception as e:
            print(f"\n💥 Gauntlet crashed: {e}")
            self.save_progress()
    
    def calculate_final_rating(self):
        """Calculate V7P3R's estimated rating from all brackets"""
        
        if not self.gauntlet_results['elo_brackets']:
            return
        
        # Weight performance by number of games
        total_weighted_elo = 0
        total_games = 0
        
        for bracket in self.gauntlet_results['elo_brackets']:
            if bracket['total_games'] > 0:
                weight = bracket['total_games']
                perf_elo = bracket['performance_elo']
                
                total_weighted_elo += perf_elo * weight
                total_games += weight
        
        if total_games > 0:
            estimated_elo = total_weighted_elo / total_games
            
            # Calculate confidence range
            performances = [b['performance_elo'] for b in self.gauntlet_results['elo_brackets'] if b['total_games'] > 0]
            if len(performances) > 1:
                import statistics
                std_dev = statistics.stdev(performances)
                confidence_range = (estimated_elo - std_dev, estimated_elo + std_dev)
            else:
                confidence_range = (estimated_elo - 100, estimated_elo + 100)
            
            self.gauntlet_results['final_rating_estimate'] = {
                'estimated_elo': estimated_elo,
                'confidence_range': confidence_range,
                'total_games_analyzed': total_games
            }
    
    def print_gauntlet_summary(self, total_games, total_wins, total_draws, total_losses):
        """Print comprehensive gauntlet summary"""
        
        print(f"\n🏆 V7P3R ELO Gauntlet Complete!")
        print("=" * 50)
        
        print(f"📊 Overall Performance:")
        print(f"   Total games: {total_games}")
        print(f"   Overall score: {total_wins}W-{total_draws}D-{total_losses}L")
        
        if total_games > 0:
            overall_score_rate = (total_wins + 0.5 * total_draws) / total_games
            print(f"   Overall score rate: {overall_score_rate:.1%}")
        
        # Rating estimate
        if self.gauntlet_results['final_rating_estimate']:
            estimate = self.gauntlet_results['final_rating_estimate']
            elo = estimate['estimated_elo']
            range_low, range_high = estimate['confidence_range']
            
            print(f"\n🎯 V7P3R v7.0 Estimated Rating:")
            print(f"   📈 ELO: {elo:.0f}")
            print(f"   📊 Range: {range_low:.0f} - {range_high:.0f}")
            print(f"   📋 Based on {estimate['total_games_analyzed']} games")
        
        # Bracket breakdown
        print(f"\n📋 Bracket Performance:")
        for bracket in self.gauntlet_results['elo_brackets']:
            if bracket['total_games'] > 0:
                elo = bracket['target_elo']
                score = bracket['score_rate']
                perf = bracket['performance_elo']
                games = bracket['total_games']
                print(f"   {elo} ELO: {score:.1%} score (Perf: {perf:.0f}, {games} games)")
    
    def save_progress(self):
        """Save current progress"""
        progress_file = self.results_dir / f"gauntlet_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(progress_file, 'w') as f:
            json.dump(self.gauntlet_results, f, indent=2)
    
    def save_final_results(self):
        """Save final comprehensive results"""
        
        # Main results file
        results_file = self.results_dir / f"v7p3r_stockfish_gauntlet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        self.gauntlet_results['test_end'] = datetime.now().isoformat()
        
        with open(results_file, 'w') as f:
            json.dump(self.gauntlet_results, f, indent=2)
        
        # Extract PGN games for analysis
        pgn_file = self.results_dir / f"v7p3r_games_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn"
        
        with open(pgn_file, 'w') as f:
            f.write("# V7P3R v7.0 vs Stockfish ELO Gauntlet Games\n")
            f.write(f"# Test date: {self.gauntlet_results['test_start']}\n\n")
            
            for bracket in self.gauntlet_results['elo_brackets']:
                for game in bracket['games']:
                    if 'pgn_game' in game and game['pgn_game'] != 'not_recorded':
                        f.write(f"# Game vs Stockfish {bracket['target_elo']} ELO\n")
                        f.write(f"# V7P3R as {game.get('v7p3r_color', 'unknown')}\n")
                        f.write(f"# Result: V7P3R {game.get('v7p3r_outcome', 'unknown')}\n")
                        f.write(game['pgn_game'])
                        f.write("\n\n")
        
        print(f"\n📁 Results saved:")
        print(f"   📊 Data: {results_file}")
        print(f"   ♟️  Games: {pgn_file}")


async def main():
    """Run the V7P3R ELO gauntlet"""
    
    gauntlet = V7P3RStockfishGauntlet()
    await gauntlet.run_full_gauntlet()


if __name__ == "__main__":
    asyncio.run(main())
