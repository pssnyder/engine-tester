#!/usr/bin/env python3
"""
Simple V7P3R vs Stockfish ELO Test
==================================

Direct test using python-chess to validate ELO limiting concept.
This bypasses the complex framework and directly tests:
1. Can we limit Stockfish to specific ELO ratings?
2. How does V7P3R perform against different Stockfish strengths?
"""

import chess
import chess.engine
import chess.pgn
import time
import json
from pathlib import Path
from datetime import datetime

class SimpleELOTest:
    """Simple ELO testing using python-chess directly"""
    
    def __init__(self):
        self.stockfish_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        self.v7p3r_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/V7P3R/V7P3R_v7.0.exe"
        
    def test_stockfish_elo_limiting(self):
        """Test if we can successfully limit Stockfish to different ELOs"""
        
        print("🧪 Testing Stockfish ELO Limiting...")
        
        test_elos = [1320, 1500, 1800, 2000]
        
        for target_elo in test_elos:
            print(f"\n🎯 Testing Stockfish at {target_elo} ELO:")
            
            try:
                with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                    # Configure Stockfish for specific ELO
                    engine.configure({
                        "UCI_LimitStrength": True,
                        "UCI_Elo": target_elo,
                        "Threads": 1,
                        "Hash": 32
                    })
                    
                    # Test position: middle game
                    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1")
                    
                    # Get move with time limit
                    info = engine.analyse(board, chess.engine.Limit(time=1.0))
                    best_move = info["pv"][0]
                    score = info.get("score", "unknown")
                    
                    print(f"   ✅ Stockfish {target_elo}: {best_move} (score: {score})")
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        print("✅ Stockfish ELO limiting test complete!")
    
    def run_single_game(self, v7p3r_white: bool = True, stockfish_elo: int = 1500, time_per_move: float = 3.0):
        """Run a single game between V7P3R and Stockfish"""
        
        print(f"\n🎮 Game: V7P3R ({'white' if v7p3r_white else 'black'}) vs Stockfish {stockfish_elo} ELO")
        
        board = chess.Board()
        game = chess.pgn.Game()
        game.headers["Event"] = f"V7P3R vs Stockfish {stockfish_elo} ELO Test"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["White"] = "V7P3R_v7.0" if v7p3r_white else f"Stockfish_{stockfish_elo}"
        game.headers["Black"] = f"Stockfish_{stockfish_elo}" if v7p3r_white else "V7P3R_v7.0"
        
        node = game
        
        try:
            # Open both engines
            with chess.engine.SimpleEngine.popen_uci(self.v7p3r_path) as v7p3r, \
                 chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as stockfish:
                
                # Configure Stockfish
                stockfish.configure({
                    "UCI_LimitStrength": True,
                    "UCI_Elo": stockfish_elo,
                    "Threads": 1,
                    "Hash": 32
                })
                
                move_count = 0
                max_moves = 100
                
                while not board.is_game_over() and move_count < max_moves:
                    move_count += 1
                    
                    # Determine which engine's turn
                    if (board.turn == chess.WHITE and v7p3r_white) or \
                       (board.turn == chess.BLACK and not v7p3r_white):
                        # V7P3R's turn
                        engine = v7p3r
                        engine_name = "V7P3R"
                    else:
                        # Stockfish's turn  
                        engine = stockfish
                        engine_name = f"Stockfish_{stockfish_elo}"
                    
                    print(f"   Move {move_count}: {engine_name} thinking...", end='')
                    
                    try:
                        # Get move
                        result = engine.play(board, chess.engine.Limit(time=time_per_move))
                        move = result.move
                        
                        # Make move
                        board.push(move)
                        node = node.add_variation(move)
                        
                        print(f" {move}")
                        
                    except Exception as e:
                        print(f" ERROR: {e}")
                        break
                
                # Determine result
                result = board.result()
                game.headers["Result"] = result
                
                print(f"   🏁 Game finished: {result}")
                
                if result == "1-0":
                    winner = "White wins"
                elif result == "0-1":
                    winner = "Black wins"
                else:
                    winner = "Draw"
                
                # Determine V7P3R result
                if v7p3r_white:
                    v7p3r_result = "WIN" if result == "1-0" else ("LOSS" if result == "0-1" else "DRAW")
                else:
                    v7p3r_result = "WIN" if result == "0-1" else ("LOSS" if result == "1-0" else "DRAW")
                
                return {
                    'winner': winner,
                    'result': result,
                    'v7p3r_result': v7p3r_result,
                    'moves': move_count,
                    'pgn': str(game),
                    'stockfish_elo': stockfish_elo,
                    'v7p3r_color': 'white' if v7p3r_white else 'black'
                }
                
        except Exception as e:
            print(f"   💥 Game crashed: {e}")
            return None
    
    def run_elo_bracket_test(self, target_elo: int, num_games: int = 4):
        """Test V7P3R against specific Stockfish ELO"""
        
        print(f"\n🎯 Testing V7P3R vs Stockfish {target_elo} ELO ({num_games} games)")
        
        results = []
        wins = 0
        draws = 0
        losses = 0
        
        for game_num in range(num_games):
            # Alternate colors
            v7p3r_white = (game_num % 2 == 0)
            
            game_result = self.run_single_game(
                v7p3r_white=v7p3r_white,
                stockfish_elo=target_elo,
                time_per_move=2.0
            )
            
            if game_result:
                results.append(game_result)
                
                if game_result['v7p3r_result'] == 'WIN':
                    wins += 1
                elif game_result['v7p3r_result'] == 'DRAW':
                    draws += 1
                else:
                    losses += 1
        
        total_games = len(results)
        if total_games > 0:
            win_rate = wins / total_games
            score_rate = (wins + 0.5 * draws) / total_games
            
            print(f"\n📊 Results vs Stockfish {target_elo} ELO:")
            print(f"   Games: {total_games}")
            print(f"   Score: {wins}W-{draws}D-{losses}L")
            print(f"   Win rate: {win_rate:.1%}")
            print(f"   Score rate: {score_rate:.1%}")
            
            return {
                'target_elo': target_elo,
                'total_games': total_games,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': win_rate,
                'score_rate': score_rate,
                'games': results
            }
        
        return None


def main():
    """Run ELO tests"""
    
    tester = SimpleELOTest()
    
    # Check if engines exist
    if not Path(tester.v7p3r_path).exists():
        print(f"❌ V7P3R not found: {tester.v7p3r_path}")
        return
    
    if not Path(tester.stockfish_path).exists():
        print(f"❌ Stockfish not found: {tester.stockfish_path}")
        return
    
    print("🚀 V7P3R vs Stockfish ELO Assessment")
    print("=" * 40)
    
    # First, test if ELO limiting works
    tester.test_stockfish_elo_limiting()
    
    # Then run a quick bracket test
    test_elos = [1400, 1600, 1800]
    
    all_results = []
    
    for elo in test_elos:
        bracket_result = tester.run_elo_bracket_test(elo, num_games=4)
        if bracket_result:
            all_results.append(bracket_result)
    
    # Save results
    if all_results:
        results_file = f"v7p3r_elo_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_file}")
        
        # Quick analysis
        print(f"\n🎯 Quick Assessment:")
        for result in all_results:
            elo = result['target_elo']
            score = result['score_rate']
            print(f"   Stockfish {elo}: {score:.1%} score")


if __name__ == "__main__":
    main()
