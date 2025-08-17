"""
Gauntlet Testing Framework
Tests your chess engine against all 627 competition entries from the Tiny Chess Bot Challenge
"""

import json
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import subprocess

@dataclass
class BotInfo:
    """Information about a competition bot"""
    bot_id: int
    name: str
    author: str
    score: int
    tiebreak: int
    rank: int
    file_path: Path

@dataclass
class GauntletResult:
    """Result of a single gauntlet match"""
    bot_id: int
    bot_name: str
    our_engine: str
    result: str  # 'win', 'loss', 'draw', 'error'
    moves: int
    time_taken: float
    error_message: Optional[str] = None

class GauntletTester:
    """Manages gauntlet testing against competition bots"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.source_dir = self.base_dir / "source_repos" / "Tiny-Chess-Bot-Challenge-Results"
        self.bots_dir = self.source_dir / "Bots"
        self.results_dir = self.base_dir / "gauntlet_testing" / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.bots_info: List[BotInfo] = []
        self.load_bot_rankings()
        
    def load_bot_rankings(self):
        """Load bot rankings from tournament results"""
        results_file = self.source_dir / "Swiss" / "Results.txt"
        
        if not results_file.exists():
            print(f"Warning: Results file not found at {results_file}")
            return
            
        self.bots_info = []
        rank = 1
        
        with open(results_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split(' | ')
                if len(parts) >= 4:
                    try:
                        bot_id_str = parts[0].strip()
                        bot_name = parts[1].strip()
                        author = parts[2].strip()
                        score = int(parts[3].strip())
                        tiebreak = int(parts[4].strip()) if len(parts) > 4 else 0
                        
                        # Extract bot ID number
                        bot_id = int(bot_id_str.replace('Bot_', ''))
                        
                        # Find corresponding file
                        bot_file = self.bots_dir / f"Bot_{bot_id}.cs"
                        
                        if bot_file.exists():
                            bot_info = BotInfo(
                                bot_id=bot_id,
                                name=bot_name,
                                author=author,
                                score=score,
                                tiebreak=tiebreak,
                                rank=rank,
                                file_path=bot_file
                            )
                            self.bots_info.append(bot_info)
                            rank += 1
                        else:
                            print(f"Warning: Bot file not found for Bot_{bot_id}")
                            
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse line: {line} - {e}")
                        
        print(f"Loaded {len(self.bots_info)} competition bots")
        
    def get_bot_summary(self) -> Dict[str, Any]:
        """Get summary statistics of loaded bots"""
        if not self.bots_info:
            return {"error": "No bots loaded"}
            
        scores = [bot.score for bot in self.bots_info]
        return {
            "total_bots": len(self.bots_info),
            "score_range": {
                "min": min(scores),
                "max": max(scores),
                "avg": sum(scores) / len(scores)
            },
            "top_10": [
                {"rank": bot.rank, "name": bot.name, "score": bot.score, "author": bot.author}
                for bot in self.bots_info[:10]
            ]
        }
        
    def run_gauntlet(self, our_engine_path: str, max_bots: Optional[int] = None, 
                    start_from_rank: int = 1, time_per_game: float = 60.0) -> List[GauntletResult]:
        """
        Run gauntlet test against competition bots
        
        Args:
            our_engine_path: Path to your engine
            max_bots: Maximum number of bots to test against (None = all)
            start_from_rank: Start from this rank (1 = strongest bot)
            time_per_game: Time limit per game in seconds
        """
        
        if not self.bots_info:
            raise RuntimeError("No bots loaded. Check bot rankings file.")
            
        # Filter bots based on parameters
        bots_to_test = self.bots_info[start_from_rank - 1:]
        if max_bots:
            bots_to_test = bots_to_test[:max_bots]
            
        print(f"Starting gauntlet test against {len(bots_to_test)} bots")
        print(f"Starting from rank {start_from_rank}")
        print(f"Time per game: {time_per_game}s")
        print("="*50)
        
        results = []
        start_time = time.time()
        
        for i, bot in enumerate(bots_to_test, 1):
            print(f"[{i}/{len(bots_to_test)}] Testing against {bot.name} (Rank {bot.rank}, Score {bot.score})")
            
            try:
                result = self._test_against_bot(our_engine_path, bot, time_per_game)
                results.append(result)
                
                # Print result
                status_symbol = "✓" if result.result == "win" else "✗" if result.result == "loss" else "="
                print(f"  {status_symbol} {result.result.upper()} in {result.moves} moves ({result.time_taken:.1f}s)")
                
            except Exception as e:
                error_result = GauntletResult(
                    bot_id=bot.bot_id,
                    bot_name=bot.name,
                    our_engine=our_engine_path,
                    result="error",
                    moves=0,
                    time_taken=0.0,
                    error_message=str(e)
                )
                results.append(error_result)
                print(f"  ✗ ERROR: {e}")
                
            # Save intermediate results every 10 games
            if i % 10 == 0:
                self._save_results(results, f"gauntlet_intermediate_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
        total_time = time.time() - start_time
        print("="*50)
        print(f"Gauntlet complete in {total_time:.1f}s")
        
        # Save final results
        self._save_results(results, f"gauntlet_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self._print_summary(results)
        
        return results
        
    def _test_against_bot(self, our_engine_path: str, bot: BotInfo, time_limit: float) -> GauntletResult:
        """Test our engine against a single competition bot"""
        
        # For now, this is a placeholder implementation
        # TODO: Implement actual chess game logic
        
        start_time = time.time()
        
        # Simulate a game (this needs to be replaced with actual implementation)
        import random
        result = random.choice(['win', 'loss', 'draw'])
        moves = random.randint(20, 80)
        
        time.sleep(0.1)  # Simulate game time
        
        time_taken = time.time() - start_time
        
        return GauntletResult(
            bot_id=bot.bot_id,
            bot_name=bot.name,
            our_engine=our_engine_path,
            result=result,
            moves=moves,
            time_taken=time_taken
        )
        
    def _save_results(self, results: List[GauntletResult], filename_base: str):
        """Save results to JSON and CSV files"""
        
        timestamp = datetime.now().isoformat()
        
        # Save JSON
        json_file = self.results_dir / f"{filename_base}.json"
        results_data = {
            "timestamp": timestamp,
            "total_games": len(results),
            "results": [
                {
                    "bot_id": r.bot_id,
                    "bot_name": r.bot_name,
                    "our_engine": r.our_engine,
                    "result": r.result,
                    "moves": r.moves,
                    "time_taken": r.time_taken,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }
        
        with open(json_file, 'w') as f:
            json.dump(results_data, f, indent=2)
            
        # Save CSV
        csv_file = self.results_dir / f"{filename_base}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['bot_id', 'bot_name', 'our_engine', 'result', 'moves', 'time_taken', 'error_message'])
            
            for r in results:
                writer.writerow([
                    r.bot_id, r.bot_name, r.our_engine, r.result, 
                    r.moves, r.time_taken, r.error_message or ''
                ])
                
        print(f"Results saved to {json_file} and {csv_file}")
        
    def _print_summary(self, results: List[GauntletResult]):
        """Print summary of gauntlet results"""
        
        wins = sum(1 for r in results if r.result == 'win')
        losses = sum(1 for r in results if r.result == 'loss')
        draws = sum(1 for r in results if r.result == 'draw')
        errors = sum(1 for r in results if r.result == 'error')
        total = len(results)
        
        print(f"\nGAUNTLET SUMMARY:")
        print(f"Total games: {total}")
        print(f"Wins: {wins} ({wins/total*100:.1f}%)")
        print(f"Losses: {losses} ({losses/total*100:.1f}%)")
        print(f"Draws: {draws} ({draws/total*100:.1f}%)")
        print(f"Errors: {errors} ({errors/total*100:.1f}%)")
        print(f"Score: {wins + draws/2:.1f} / {total} ({(wins + draws/2)/total*100:.1f}%)")
        
        if wins == total - errors:
            print("\n🎉 PERFECT GAUNTLET! You beat all competition bots! 🎉")
        elif wins > total * 0.9:
            print("\n🏆 EXCELLENT! You dominated the gauntlet!")
        elif wins > total * 0.7:
            print("\n👍 GOOD! Strong performance against the competition!")
        else:
            print("\n📈 Keep improving! There's room for growth.")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run gauntlet test against competition bots")
    parser.add_argument("engine", help="Path to your chess engine")
    parser.add_argument("--max-bots", type=int, help="Maximum number of bots to test against")
    parser.add_argument("--start-rank", type=int, default=1, help="Start from this rank (1=strongest)")
    parser.add_argument("--time-per-game", type=float, default=60.0, help="Time limit per game in seconds")
    parser.add_argument("--summary-only", action="store_true", help="Show bot summary only, don't run tests")
    
    args = parser.parse_args()
    
    tester = GauntletTester()
    
    if args.summary_only:
        summary = tester.get_bot_summary()
        print(json.dumps(summary, indent=2))
        return
        
    results = tester.run_gauntlet(
        our_engine_path=args.engine,
        max_bots=args.max_bots,
        start_from_rank=args.start_rank,
        time_per_game=args.time_per_game
    )

if __name__ == "__main__":
    main()
