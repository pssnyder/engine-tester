#!/usr/bin/env python3
"""
V7P3R vs Weakest Stockfish Test
===============================

Safe, simple test to validate:
1. Can we actually make Stockfish weak enough for V7P3R to compete?
2. How does V7P3R perform with adequate thinking time?
3. Robust error handling to prevent test failures

Strategy:
- Test only the WEAKEST possible Stockfish settings
- Give V7P3R plenty of time (5+ seconds per move)
- Add comprehensive error handling and recovery
- Save progress after each game to prevent data loss
"""

import chess
import chess.engine
import chess.pgn
import json
import time
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafeELOTest:
    """Safe, robust ELO testing with comprehensive error handling"""
    
    def __init__(self):
        self.stockfish_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        self.v7p3r_path = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines/V7P3R/V7P3R_v7.0.exe"
        
        # Conservative time settings - give V7P3R plenty of time
        self.v7p3r_time = 8.0  # 8 seconds per move for V7P3R
        self.stockfish_time = 2.0  # 2 seconds for Stockfish (it's fast)
        
        # Results tracking
        self.results_file = f"v7p3r_vs_weakest_stockfish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.session_data = {
            'test_start': datetime.now().isoformat(),
            'engines': {
                'v7p3r': self.v7p3r_path,
                'stockfish': self.stockfish_path
            },
            'time_control': {
                'v7p3r_seconds': self.v7p3r_time,
                'stockfish_seconds': self.stockfish_time
            },
            'games': [],
            'summary': {}
        }
    
    def validate_engines(self):
        """Validate that both engines are available and working"""
        
        logger.info("🔍 Validating engines...")
        
        # Check file existence
        if not Path(self.v7p3r_path).exists():
            logger.error(f"❌ V7P3R not found: {self.v7p3r_path}")
            return False
        
        if not Path(self.stockfish_path).exists():
            logger.error(f"❌ Stockfish not found: {self.stockfish_path}")
            return False
        
        # Test basic UCI communication
        try:
            logger.info("Testing V7P3R UCI...")
            with chess.engine.SimpleEngine.popen_uci(self.v7p3r_path, timeout=30) as engine:
                logger.info(f"✅ V7P3R: {engine.id.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ V7P3R UCI failed: {e}")
            return False
        
        try:
            logger.info("Testing Stockfish UCI...")
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path, timeout=30) as engine:
                logger.info(f"✅ Stockfish: {engine.id.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ Stockfish UCI failed: {e}")
            return False
        
        logger.info("✅ Both engines validated!")
        return True
    
    def find_weakest_stockfish_settings(self):
        """Find the absolute weakest Stockfish configuration possible"""
        
        logger.info("🔍 Finding weakest Stockfish settings...")
        
        # Test different weakness configurations
        weakness_configs = [
            {"UCI_LimitStrength": True, "UCI_Elo": 1320, "Skill Level": 0},  # Min ELO + Min Skill
            {"Skill Level": 0},  # Just minimum skill level
            {"UCI_LimitStrength": True, "UCI_Elo": 1320},  # Just minimum ELO
        ]
        
        best_config = None
        
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path, timeout=30) as engine:
                
                # Test a simple position to see which config gives weakest play
                test_board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
                
                for i, config in enumerate(weakness_configs):
                    try:
                        logger.info(f"Testing config {i+1}: {config}")
                        
                        # Apply configuration
                        engine.configure(config)
                        
                        # Get move and evaluation
                        info = engine.analyse(test_board, chess.engine.Limit(time=1.0))
                        
                        # Check if analysis succeeded
                        if "pv" in info and len(info["pv"]) > 0:
                            move = info["pv"][0]
                            score = info.get("score", chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                            logger.info(f"   Move: {move}, Score: {score}")
                            
                            # For now, use the first working config
                            if best_config is None:
                                best_config = config
                                logger.info(f"✅ Selected config: {config}")
                        
                    except Exception as e:
                        logger.warning(f"Config {i+1} failed: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"❌ Could not test Stockfish configurations: {e}")
            return None
        
        if best_config is None:
            logger.warning("⚠️  Using fallback minimal config")
            best_config = {"Skill Level": 0}  # Simplest fallback
        
        logger.info(f"🎯 Final weakest config: {best_config}")
        return best_config
    
    def run_single_game(self, game_num: int, v7p3r_white: bool, stockfish_config: dict):
        """Run a single game with comprehensive error handling"""
        
        color_str = "white" if v7p3r_white else "black"
        logger.info(f"🎮 Game {game_num}: V7P3R ({color_str}) vs Weakest Stockfish")
        
        board = chess.Board()
        moves = []
        game_result = {
            'game_number': game_num,
            'v7p3r_color': color_str,
            'start_time': datetime.now().isoformat(),
            'moves': [],
            'result': None,
            'v7p3r_outcome': None,
            'error': None,
            'duration_minutes': 0
        }
        
        start_time = time.time()
        
        try:
            # Open engines with timeouts
            with chess.engine.SimpleEngine.popen_uci(self.v7p3r_path, timeout=30) as v7p3r, \
                 chess.engine.SimpleEngine.popen_uci(self.stockfish_path, timeout=30) as stockfish:
                
                # Configure Stockfish to be weak
                logger.info(f"Configuring Stockfish: {stockfish_config}")
                stockfish.configure(stockfish_config)
                
                move_count = 0
                max_moves = 80  # Reasonable game length limit
                
                while not board.is_game_over() and move_count < max_moves:
                    move_count += 1
                    
                    # Determine which engine's turn
                    if (board.turn == chess.WHITE and v7p3r_white) or \
                       (board.turn == chess.BLACK and not v7p3r_white):
                        # V7P3R's turn - give it time to think
                        engine = v7p3r
                        engine_name = "V7P3R"
                        think_time = self.v7p3r_time
                    else:
                        # Stockfish's turn
                        engine = stockfish
                        engine_name = "Stockfish_Weak"
                        think_time = self.stockfish_time
                    
                    logger.info(f"   Move {move_count}: {engine_name} thinking ({think_time}s)...")
                    
                    try:
                        # Get move with timeout protection
                        move_start = time.time()
                        result = engine.play(board, chess.engine.Limit(time=think_time), info=chess.engine.INFO_BASIC)
                        move_duration = time.time() - move_start
                        
                        if result.move is None:
                            logger.error(f"Engine {engine_name} returned no move!")
                            game_result['error'] = f"No move from {engine_name}"
                            break
                        
                        move = result.move
                        
                        # Validate move
                        if move not in board.legal_moves:
                            logger.error(f"Illegal move {move} from {engine_name}!")
                            game_result['error'] = f"Illegal move {move} from {engine_name}"
                            break
                        
                        # Make move
                        board.push(move)
                        
                        move_info = {
                            'number': move_count,
                            'engine': engine_name,
                            'move': str(move),
                            'time_taken': round(move_duration, 2),
                            'fen_after': board.fen()
                        }
                        game_result['moves'].append(move_info)
                        
                        logger.info(f"   {engine_name}: {move} ({move_duration:.1f}s)")
                        
                    except chess.engine.EngineTerminatedError:
                        logger.error(f"Engine {engine_name} terminated unexpectedly!")
                        game_result['error'] = f"Engine {engine_name} terminated"
                        break
                    except Exception as e:
                        logger.error(f"Move error from {engine_name}: {e}")
                        game_result['error'] = f"Move error from {engine_name}: {e}"
                        break
                
                # Game finished - determine result
                if game_result['error'] is None:
                    board_result = board.result()
                    game_result['result'] = board_result
                    game_result['total_moves'] = move_count
                    
                    # Determine V7P3R outcome
                    if board_result == "1-0":
                        game_result['v7p3r_outcome'] = "WIN" if v7p3r_white else "LOSS"
                    elif board_result == "0-1":
                        game_result['v7p3r_outcome'] = "WIN" if not v7p3r_white else "LOSS"
                    else:
                        game_result['v7p3r_outcome'] = "DRAW"
                    
                    logger.info(f"   🏁 Game {game_num} finished: {board_result} - V7P3R {game_result['v7p3r_outcome']}")
        
        except Exception as e:
            logger.error(f"💥 Game {game_num} crashed: {e}")
            game_result['error'] = str(e)
        
        finally:
            # Record duration
            game_result['duration_minutes'] = round((time.time() - start_time) / 60, 2)
            game_result['end_time'] = datetime.now().isoformat()
            
            # Save game immediately to prevent data loss
            self.session_data['games'].append(game_result)
            self.save_progress()
        
        return game_result
    
    def save_progress(self):
        """Save current progress to prevent data loss"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def run_tournament(self, num_games: int = 6):
        """Run a tournament between V7P3R and weakest Stockfish"""
        
        logger.info(f"🚀 Starting V7P3R vs Weakest Stockfish Tournament ({num_games} games)")
        
        # Validate engines first
        if not self.validate_engines():
            logger.error("❌ Engine validation failed - aborting tournament")
            return None
        
        # Find weakest Stockfish settings
        stockfish_config = self.find_weakest_stockfish_settings()
        if stockfish_config is None:
            logger.error("❌ Could not configure weak Stockfish - aborting tournament")
            return None
        
        self.session_data['stockfish_config'] = stockfish_config
        
        # Run games
        wins = 0
        draws = 0
        losses = 0
        errors = 0
        
        for game_num in range(1, num_games + 1):
            # Alternate colors
            v7p3r_white = (game_num % 2 == 1)
            
            logger.info(f"\n📍 Starting game {game_num}/{num_games}")
            
            game_result = self.run_single_game(game_num, v7p3r_white, stockfish_config)
            
            if game_result['error'] is not None:
                errors += 1
                logger.warning(f"⚠️  Game {game_num} had errors")
            else:
                outcome = game_result['v7p3r_outcome']
                if outcome == 'WIN':
                    wins += 1
                elif outcome == 'DRAW':
                    draws += 1
                else:
                    losses += 1
            
            # Show running tally
            completed_games = wins + draws + losses
            if completed_games > 0:
                score_rate = (wins + 0.5 * draws) / completed_games
                logger.info(f"📊 Current tally: {wins}W-{draws}D-{losses}L ({score_rate:.1%}) + {errors} errors")
        
        # Final summary
        total_valid_games = wins + draws + losses
        if total_valid_games > 0:
            win_rate = wins / total_valid_games
            score_rate = (wins + 0.5 * draws) / total_valid_games
            
            summary = {
                'total_games_attempted': num_games,
                'valid_games': total_valid_games,
                'errors': errors,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': win_rate,
                'score_rate': score_rate,
                'test_conclusion': self.analyze_results(score_rate)
            }
            
            self.session_data['summary'] = summary
            self.session_data['test_end'] = datetime.now().isoformat()
            self.save_progress()
            
            logger.info(f"\n🏆 Tournament Complete!")
            logger.info(f"📊 Final Results: {wins}W-{draws}D-{losses}L")
            logger.info(f"📈 Score Rate: {score_rate:.1%}")
            logger.info(f"🎯 Conclusion: {summary['test_conclusion']}")
            logger.info(f"📁 Results saved: {self.results_file}")
            
            return summary
        else:
            logger.error("❌ No valid games completed!")
            return None
    
    def analyze_results(self, score_rate: float) -> str:
        """Analyze results and provide next steps"""
        
        if score_rate >= 0.8:
            return "V7P3R dominates weakest Stockfish - ready for stronger opponents"
        elif score_rate >= 0.6:
            return "V7P3R competitive vs weakest Stockfish - can test slightly stronger"
        elif score_rate >= 0.4:
            return "V7P3R struggles but competitive - good baseline found"
        else:
            return "V7P3R loses to weakest Stockfish - need even weaker opponent"


def main():
    """Run the safe ELO test"""
    
    print("🚀 V7P3R vs Weakest Stockfish - Safe Tournament")
    print("=" * 50)
    
    tester = SafeELOTest()
    
    try:
        results = tester.run_tournament(num_games=6)
        
        if results:
            print(f"\n✅ Test completed successfully!")
            print(f"📈 V7P3R scored {results['score_rate']:.1%} against weakest Stockfish")
            print(f"🎯 {results['test_conclusion']}")
        else:
            print(f"\n❌ Test failed to complete")
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
        print(f"📁 Partial results saved in: {tester.results_file}")
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        print(f"📁 Check logs and partial results in: {tester.results_file}")


if __name__ == "__main__":
    main()
