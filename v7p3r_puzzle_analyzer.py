#!/usr/bin/env python3
"""
V7P3R Puzzle Analyzer

Simple but effective puzzle testing system that:
1. Pulls positions from puzzle database
2. Gives V7P3R generous time to analyze
3. Compares V7P3R's choice against Stockfish's top 5 moves
4. Scores performance and tracks puzzle themes

Scoring: 5pts (1st), 4pts (2nd), 3pts (3rd), 2pts (4th), 1pt (5th), 0pts (not in top 5)
"""

import subprocess
import time
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Union
import chess
import chess.engine

# Add the chess-puzzle-challenger src to path for database access
sys.path.append(os.path.join(os.path.dirname(__file__), 'chess-puzzle-challenger', 'src'))
try:
    from database import PuzzleDatabase, Puzzle
except ImportError:
    print("Error: Could not import puzzle database. Make sure chess-puzzle-challenger is available.")
    sys.exit(1)


class V7P3RPuzzleAnalyzer:
    """Analyzes V7P3R performance against puzzle database using Stockfish comparison"""
    
    def __init__(self, 
                 v7p3r_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R\V7P3R_v7.0.exe",
                 stockfish_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe",
                 puzzle_db_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\chess-puzzle-challenger\puzzles.db"):
        
        self.v7p3r_path = v7p3r_path
        self.stockfish_path = stockfish_path
        self.puzzle_db_path = puzzle_db_path
        self.results = []
        
        # Verify engines exist
        if not os.path.exists(v7p3r_path):
            raise FileNotFoundError(f"V7P3R engine not found: {v7p3r_path}")
        if not os.path.exists(stockfish_path):
            raise FileNotFoundError(f"Stockfish engine not found: {stockfish_path}")
        if not os.path.exists(puzzle_db_path):
            raise FileNotFoundError(f"Puzzle database not found: {puzzle_db_path}")
    
    def get_v7p3r_move(self, fen: str, time_seconds: float = 10.0) -> Optional[str]:
        """Get V7P3R's best move for a position with generous time"""
        try:
            process = subprocess.Popen(
                self.v7p3r_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # UCI commands
            commands = [
                "uci",
                "isready",
                f"position fen {fen}",
                f"go movetime {int(time_seconds * 1000)}"  # Convert to milliseconds
            ]
            
            for cmd in commands:
                if process.stdin:
                    process.stdin.write(f"{cmd}\n")
                    process.stdin.flush()
                if cmd == "uci" or cmd == "isready":
                    time.sleep(0.2)  # Brief pause for initialization
            
            # Read output until bestmove
            best_move = None
            output_lines = []
            start_time = time.time()
            timeout = time_seconds + 3  # Add 3 second buffer
            
            while time.time() - start_time < timeout:
                if not process.stdout:
                    break
                
                # Use poll to check if process is still running
                if process.poll() is not None:
                    break
                    
                try:
                    line = process.stdout.readline()
                    if not line:
                        time.sleep(0.1)  # Brief pause if no output
                        continue
                        
                    line = line.strip()
                    output_lines.append(line)
                    
                    if line.startswith("bestmove"):
                        parts = line.split()
                        if len(parts) > 1:
                            best_move = parts[1]
                        break
                except:
                    break
            
            # Ensure process is terminated
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                    process.wait(timeout=1)
                except:
                    pass
            
            return best_move
            
        except Exception as e:
            print(f"Error getting V7P3R move: {e}")
            return None
    
    def get_stockfish_top_moves(self, fen: str, num_moves: int = 5, time_seconds: float = 2.0) -> List[Tuple[str, int]]:
        """Get Stockfish's top N moves with scores (move, centipawn_score)"""
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                board = chess.Board(fen)
                
                # Use analyse with multipv parameter instead of configure
                result = engine.analyse(
                    board, 
                    chess.engine.Limit(time=time_seconds),
                    multipv=num_moves
                )
                
                moves_with_scores = []
                for analysis in result:
                    if 'pv' in analysis and analysis['pv']:
                        move = analysis['pv'][0]
                        score = analysis.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                        
                        # Convert score to centipawns from white's perspective
                        if score.is_mate():
                            # Convert mate scores to large centipawn values
                            mate_in = score.white().mate()
                            if mate_in is not None:
                                cp_score = 10000 - abs(mate_in) * 100 if mate_in > 0 else -10000 + abs(mate_in) * 100
                            else:
                                cp_score = 0
                        else:
                            cp_score = score.white().score()
                        
                        moves_with_scores.append((str(move), cp_score))
                
                return moves_with_scores
                
        except Exception as e:
            print(f"Error getting Stockfish moves: {e}")
            return []
    
    def score_v7p3r_move(self, v7p3r_move: str, stockfish_moves: List[Tuple[str, int]]) -> Tuple[int, int]:
        """
        Score V7P3R's move based on Stockfish ranking
        Returns: (score, rank) where rank is 1-5 or 0 if not in top 5
        """
        if not v7p3r_move or not stockfish_moves:
            return 0, 0
        
        for rank, (sf_move, _) in enumerate(stockfish_moves, 1):
            if v7p3r_move == sf_move:
                score = 6 - rank  # 5pts for 1st, 4pts for 2nd, ..., 1pt for 5th
                return score, rank
        
        return 0, 0  # Not in top 5
    
    def analyze_puzzle(self, puzzle: Puzzle, v7p3r_time: float = 10.0) -> Optional[Dict]:
        """Analyze a single puzzle"""
        print(f"Analyzing puzzle {puzzle.id} (Rating: {puzzle.rating})")
        print(f"Themes: {puzzle.themes}")
        print(f"Position: {puzzle.fen}")
        
        # Get V7P3R's move
        print(f"Giving V7P3R {v7p3r_time} seconds to think...")
        start_analysis = time.time()
        v7p3r_move = self.get_v7p3r_move(puzzle.fen, v7p3r_time)
        analysis_time = time.time() - start_analysis
        
        if not v7p3r_move:
            print(f"❌ V7P3R failed to return a move (took {analysis_time:.1f}s)")
            return None
        
        print(f"V7P3R chose: {v7p3r_move} (took {analysis_time:.1f}s)")
        
        # Get Stockfish's top 5 moves
        print("Getting Stockfish's top 5 moves...")
        stockfish_moves = self.get_stockfish_top_moves(puzzle.fen, 5, 2.0)
        
        if not stockfish_moves:
            print("❌ Stockfish failed to analyze position")
            return None
        
        print("Stockfish's top 5 moves:")
        for i, (move, score) in enumerate(stockfish_moves, 1):
            print(f"  {i}. {move} (score: {score:+d})")
        
        # Score V7P3R's performance
        score, rank = self.score_v7p3r_move(v7p3r_move, stockfish_moves)
        
        if rank > 0:
            print(f"✅ V7P3R's move ranked #{rank} - Score: {score}/5")
        else:
            print(f"❌ V7P3R's move not in top 5 - Score: 0/5")
        
        # Expected move from puzzle (for reference)
        expected_moves = puzzle.moves.split() if puzzle.moves else []
        expected_move = expected_moves[0] if expected_moves else "unknown"
        print(f"Expected move: {expected_move}")
        
        result = {
            'puzzle_id': puzzle.id,
            'fen': puzzle.fen,
            'rating': puzzle.rating,
            'themes': puzzle.themes.split() if puzzle.themes else [],
            'v7p3r_move': v7p3r_move,
            'v7p3r_score': score,
            'v7p3r_rank': rank,
            'stockfish_top_moves': stockfish_moves,
            'expected_move': expected_move,
            'v7p3r_time_seconds': v7p3r_time,
            'timestamp': datetime.now().isoformat()
        }
        
        print("-" * 60)
        return result
    
    def run_analysis(self, 
                     num_puzzles: int = 100,
                     rating_min: int = 1200,
                     rating_max: int = 2000,
                     v7p3r_time: float = 10.0,
                     themes_filter: Optional[List[str]] = None) -> List[Dict]:
        """Run analysis on multiple puzzles"""
        
        print(f"V7P3R Puzzle Analysis - {num_puzzles} puzzles")
        print(f"Rating range: {rating_min}-{rating_max}")
        print(f"V7P3R thinking time: {v7p3r_time} seconds")
        if themes_filter:
            print(f"Theme filter: {themes_filter}")
        print("=" * 60)
        
        # Get puzzles from database
        db = PuzzleDatabase(self.puzzle_db_path)
        puzzles = db.query_puzzles(
            themes=themes_filter,
            min_rating=rating_min,
            max_rating=rating_max,
            quantity=num_puzzles
        )
        
        if not puzzles:
            print("No puzzles found matching criteria!")
            return []
        
        print(f"Found {len(puzzles)} puzzles to analyze")
        print("-" * 60)
        
        # Analyze each puzzle
        results = []
        for i, puzzle in enumerate(puzzles, 1):
            print(f"Puzzle {i}/{len(puzzles)}")
            result = self.analyze_puzzle(puzzle, v7p3r_time)
            if result:
                results.append(result)
                self.results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """Generate analysis report"""
        if not results:
            return {}
        
        total_puzzles = len(results)
        total_score = sum(r['v7p3r_score'] for r in results)
        max_possible_score = total_puzzles * 5
        
        # Score distribution
        score_dist = {i: 0 for i in range(6)}
        for result in results:
            score_dist[result['v7p3r_score']] += 1
        
        # Rank distribution
        rank_dist = {i: 0 for i in range(6)}  # 0 = not in top 5, 1-5 = ranks
        for result in results:
            rank_dist[result['v7p3r_rank']] += 1
        
        # Theme analysis
        theme_performance = {}
        for result in results:
            for theme in result['themes']:
                if theme not in theme_performance:
                    theme_performance[theme] = {'total': 0, 'score_sum': 0}
                theme_performance[theme]['total'] += 1
                theme_performance[theme]['score_sum'] += result['v7p3r_score']
        
        # Calculate theme averages
        for theme in theme_performance:
            theme_data = theme_performance[theme]
            theme_data['average_score'] = theme_data['score_sum'] / theme_data['total']
            theme_data['percentage'] = (theme_data['score_sum'] / (theme_data['total'] * 5)) * 100
        
        # Top 5 hit rate
        top5_hits = sum(1 for r in results if r['v7p3r_rank'] > 0)
        top5_rate = (top5_hits / total_puzzles) * 100
        
        report = {
            'total_puzzles': total_puzzles,
            'total_score': total_score,
            'max_possible_score': max_possible_score,
            'average_score': total_score / total_puzzles,
            'percentage_score': (total_score / max_possible_score) * 100,
            'top5_hits': top5_hits,
            'top5_hit_rate': top5_rate,
            'score_distribution': score_dist,
            'rank_distribution': rank_dist,
            'theme_performance': theme_performance,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted analysis report"""
        print("\n" + "=" * 80)
        print("V7P3R PUZZLE ANALYSIS REPORT")
        print("=" * 80)
        
        print(f"Puzzles Analyzed: {report['total_puzzles']}")
        print(f"Total Score: {report['total_score']}/{report['max_possible_score']}")
        print(f"Average Score: {report['average_score']:.2f}/5.0")
        print(f"Percentage Score: {report['percentage_score']:.1f}%")
        print(f"Top-5 Hit Rate: {report['top5_hits']}/{report['total_puzzles']} ({report['top5_hit_rate']:.1f}%)")
        
        print("\nScore Distribution:")
        for score in range(5, -1, -1):
            count = report['score_distribution'][score]
            percentage = (count / report['total_puzzles']) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {score} pts: {count:3d} ({percentage:4.1f}%) {bar}")
        
        print("\nRank Distribution:")
        rank_labels = {0: "Not in top 5", 1: "1st (best)", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}
        for rank in range(0, 6):
            count = report['rank_distribution'][rank]
            percentage = (count / report['total_puzzles']) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {rank_labels[rank]:12s}: {count:3d} ({percentage:4.1f}%) {bar}")
        
        print("\nTheme Performance (Top 10):")
        theme_items = list(report['theme_performance'].items())
        theme_items.sort(key=lambda x: x[1]['average_score'], reverse=True)
        
        for theme, data in theme_items[:10]:
            avg_score = data['average_score']
            percentage = data['percentage']
            count = data['total']
            print(f"  {theme:20s}: {avg_score:.2f}/5.0 ({percentage:4.1f}%) [{count:2d} puzzles]")
    
    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"v7p3r_puzzle_analysis_{timestamp}.json"
        
        data = {
            'analysis_results': self.results,
            'report': self.generate_report(self.results),
            'metadata': {
                'v7p3r_path': self.v7p3r_path,
                'stockfish_path': self.stockfish_path,
                'puzzle_db_path': self.puzzle_db_path,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to: {filename}")


def main():
    """Main execution function"""
    try:
        analyzer = V7P3RPuzzleAnalyzer()
        
        # Run analysis on 100 puzzles with generous time for V7P3R
        results = analyzer.run_analysis(
            num_puzzles=100,
            rating_min=1200,
            rating_max=2000,
            v7p3r_time=20.0,  # Give V7P3R 20 seconds per puzzle to avoid timeouts
            themes_filter=None  # No theme filter for initial broad analysis
        )
        
        if results:
            # Generate and print report
            report = analyzer.generate_report(results)
            analyzer.print_report(report)
            
            # Save results
            analyzer.save_results()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
