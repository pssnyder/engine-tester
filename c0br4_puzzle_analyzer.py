#!/usr/bin/env python3
"""
C0BR4 Puzzle Analyzer

Specialized puzzle testing system for C0BR4 engine that focuses on:
1. Rule compliance and legal move validation (crucial for bitboard system)
2. Tactical pattern recognition 
3. Castling rights and special moves validation
4. Endgame technique testing
5. Performance comparison against Stockfish

Scoring: 5pts (1st), 4pts (2nd), 3pts (3rd), 2pts (4th), 1pt (5th), 0pts (not in top 5)
Special focus on detecting illegal moves and rule infractions.
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


class C0BR4PuzzleAnalyzer:
    """Analyzes C0BR4 performance with focus on rule compliance and bitboard validation"""
    
    def __init__(self, 
                 c0br4_path: str = r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\C0BR4\C0BR4_v2.3.exe",
                 stockfish_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe",
                 puzzle_db_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\chess-puzzle-challenger\puzzles.db"):
        
        self.c0br4_path = c0br4_path
        self.stockfish_path = stockfish_path
        self.puzzle_db_path = puzzle_db_path
        self.results = []
        self.illegal_moves_detected = []
        self.rule_infractions = []
        
        # Verify engines exist
        if not os.path.exists(c0br4_path):
            raise FileNotFoundError(f"C0BR4 engine not found: {c0br4_path}")
        if not os.path.exists(stockfish_path):
            raise FileNotFoundError(f"Stockfish engine not found: {stockfish_path}")
        if not os.path.exists(puzzle_db_path):
            raise FileNotFoundError(f"Puzzle database not found: {puzzle_db_path}")
    
    def validate_move_legality(self, fen: str, move: str) -> Tuple[bool, str]:
        """Validate that a move is legal in the given position"""
        try:
            board = chess.Board(fen)
            try:
                # Try UCI notation first
                chess_move = chess.Move.from_uci(move)
                if chess_move in board.legal_moves:
                    return True, "Legal move"
                else:
                    return False, "Move not in legal moves list"
            except:
                try:
                    # Try SAN notation
                    chess_move = board.parse_san(move)
                    return True, "Legal move (SAN)"
                except:
                    return False, "Invalid move format"
        except Exception as e:
            return False, f"Error validating move: {e}"
    
    def get_c0br4_move(self, fen: str, time_seconds: float = 10.0) -> Tuple[Optional[str], List[str], bool]:
        """
        Get C0BR4's best move for a position with legality validation
        Returns: (move, output_lines, had_errors)
        """
        try:
            process = subprocess.Popen(
                self.c0br4_path,
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
            had_errors = False
            
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
                    
                    # Check for error indicators
                    if any(error_word in line.lower() for error_word in ['error', 'illegal', 'invalid', 'exception']):
                        had_errors = True
                    
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
            
            # Validate the move if we got one
            if best_move:
                is_legal, validation_msg = self.validate_move_legality(fen, best_move)
                if not is_legal:
                    self.illegal_moves_detected.append({
                        'fen': fen,
                        'move': best_move,
                        'reason': validation_msg,
                        'timestamp': datetime.now().isoformat()
                    })
                    had_errors = True
                    print(f"🚨 ILLEGAL MOVE DETECTED: {best_move} in position {fen}")
                    print(f"   Reason: {validation_msg}")
            
            return best_move, output_lines, had_errors
            
        except Exception as e:
            print(f"Error getting C0BR4 move: {e}")
            return None, [], True
    
    def get_stockfish_top_moves(self, fen: str, num_moves: int = 5, time_seconds: float = 2.0) -> List[Tuple[str, int]]:
        """Get Stockfish's top N moves with scores (move, centipawn_score)"""
        try:
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                board = chess.Board(fen)
                
                # Use analyse with multipv parameter
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
    
    def get_puzzle_challenge_position(self, puzzle: Puzzle) -> Tuple[str, str, bool, str]:
        """
        Get the actual challenge position and expected move for puzzle solving
        Returns: (challenge_fen, expected_move, is_valid, context_info)
        """
        try:
            # Start with the puzzle FEN (pre-challenge position)
            board = chess.Board(puzzle.fen)
            expected_moves = puzzle.moves.split() if puzzle.moves else []
            
            if len(expected_moves) < 2:
                return puzzle.fen, "unknown", False, "Insufficient moves in solution"
            
            # Play the first move (opponent's setup move)
            opponent_move_text = expected_moves[0]
            try:
                # Try UCI first
                opponent_move = chess.Move.from_uci(opponent_move_text)
                if opponent_move not in board.legal_moves:
                    raise ValueError("Move not legal")
            except:
                try:
                    # Try SAN notation
                    opponent_move = board.parse_san(opponent_move_text)
                except:
                    return puzzle.fen, "unknown", False, f"Cannot parse opponent move: {opponent_move_text}"
            
            # Apply the opponent's move to get challenge position
            board.push(opponent_move)
            challenge_fen = board.fen()
            
            # The second move is what the engine should find
            expected_move_text = expected_moves[1]
            try:
                # Try UCI first
                expected_move = chess.Move.from_uci(expected_move_text)
                if expected_move not in board.legal_moves:
                    raise ValueError("Move not legal")
                expected_move_uci = str(expected_move)
            except:
                try:
                    # Try SAN notation
                    expected_move = board.parse_san(expected_move_text)
                    expected_move_uci = str(expected_move)
                except:
                    return challenge_fen, expected_move_text, False, f"Cannot parse expected move: {expected_move_text}"
            
            turn_info = f"{'White' if board.turn else 'Black'} to move (after opponent played {opponent_move_text})"
            
            return challenge_fen, expected_move_uci, True, turn_info
            
        except Exception as e:
            return puzzle.fen, "unknown", False, f"Error processing puzzle: {e}"

    def score_c0br4_move(self, c0br4_move: str, stockfish_moves: List[Tuple[str, int]]) -> Tuple[int, int]:
        """
        Score C0BR4's move based on Stockfish ranking
        Returns: (score, rank) where rank is 1-5 or 0 if not in top 5
        """
        if not c0br4_move or not stockfish_moves:
            return 0, 0
        
        for rank, (sf_move, _) in enumerate(stockfish_moves, 1):
            if c0br4_move == sf_move:
                score = 6 - rank  # 5pts for 1st, 4pts for 2nd, ..., 1pt for 5th
                return score, rank
        
        return 0, 0  # Not in top 5
    
    def analyze_puzzle(self, puzzle: Puzzle, c0br4_time: float = 10.0) -> Optional[Dict]:
        """Analyze a single puzzle with focus on rule compliance"""
        print(f"Analyzing puzzle {puzzle.id} (Rating: {puzzle.rating})")
        print(f"Themes: {puzzle.themes}")
        print(f"Original FEN: {puzzle.fen}")
        print(f"Solution sequence: {puzzle.moves}")
        
        # Get the actual challenge position and expected move
        challenge_fen, expected_move, is_valid, context_info = self.get_puzzle_challenge_position(puzzle)
        
        if not is_valid:
            print(f"❌ Cannot process puzzle: {context_info}")
            return None
        
        print(f"Challenge FEN: {challenge_fen}")
        print(f"Expected move: {expected_move} ({context_info})")
        
        # Get C0BR4's move on the challenge position with validation
        print(f"Giving C0BR4 {c0br4_time} seconds to solve the challenge...")
        start_analysis = time.time()
        c0br4_move, engine_output, had_errors = self.get_c0br4_move(challenge_fen, c0br4_time)
        analysis_time = time.time() - start_analysis
        
        if not c0br4_move:
            print(f"❌ C0BR4 failed to return a move (took {analysis_time:.1f}s)")
            if had_errors:
                print(f"🚨 Engine reported errors during analysis")
            return None
        
        # Validate move legality
        is_legal, validation_msg = self.validate_move_legality(challenge_fen, c0br4_move)
        if not is_legal:
            print(f"🚨 ILLEGAL MOVE: {c0br4_move} - {validation_msg}")
            self.rule_infractions.append({
                'puzzle_id': puzzle.id,
                'fen': challenge_fen,
                'illegal_move': c0br4_move,
                'reason': validation_msg,
                'timestamp': datetime.now().isoformat()
            })
        
        print(f"C0BR4 chose: {c0br4_move} (took {analysis_time:.1f}s) {'✅ Legal' if is_legal else '🚨 ILLEGAL'}")
        
        # Get Stockfish's top 5 moves on the challenge position
        print("Getting Stockfish's top 5 moves for the challenge position...")
        stockfish_moves = self.get_stockfish_top_moves(challenge_fen, 5, 2.0)
        
        if not stockfish_moves:
            print("❌ Stockfish failed to analyze challenge position")
            return None
        
        print("Stockfish's top 5 moves:")
        for i, (move, score) in enumerate(stockfish_moves, 1):
            indicator = "🎯" if move == expected_move else "  "
            print(f"  {i}. {move} (score: {score:+d}) {indicator}")
        
        # Score C0BR4's performance (0 points if illegal move)
        if is_legal:
            score, rank = self.score_c0br4_move(c0br4_move, stockfish_moves)
        else:
            score, rank = 0, 0  # Illegal moves get 0 points
        
        if rank > 0:
            print(f"✅ C0BR4's move ranked #{rank} - Score: {score}/5")
        else:
            reason = "illegal move" if not is_legal else "not in top 5"
            print(f"❌ C0BR4's move {reason} - Score: 0/5")
        
        # Check if C0BR4 found the expected tactical move
        found_solution = c0br4_move == expected_move and is_legal
        if found_solution:
            print(f"🎯 C0BR4 found the puzzle solution!")
        else:
            print(f"❌ C0BR4 missed the puzzle solution")
        
        # Check if expected move is in Stockfish's top moves
        expected_in_top5 = any(expected_move == sf_move for sf_move, _ in stockfish_moves)
        if expected_in_top5:
            expected_rank = next(i for i, (sf_move, _) in enumerate(stockfish_moves, 1) if sf_move == expected_move)
            print(f"✅ Expected move ranks #{expected_rank} in Stockfish's analysis")
        else:
            print(f"⚠️  Expected move not in Stockfish's top 5 (unusual puzzle)")
        
        result = {
            'puzzle_id': puzzle.id,
            'original_fen': puzzle.fen,
            'challenge_fen': challenge_fen,
            'rating': puzzle.rating,
            'themes': puzzle.themes.split() if puzzle.themes else [],
            'solution_sequence': puzzle.moves,
            'c0br4_move': c0br4_move,
            'c0br4_move_legal': is_legal,
            'c0br4_move_validation_msg': validation_msg,
            'c0br4_score': score,
            'c0br4_rank': rank,
            'c0br4_found_solution': found_solution,
            'c0br4_had_errors': had_errors,
            'stockfish_top_moves': stockfish_moves,
            'expected_move': expected_move,
            'expected_in_stockfish_top5': expected_in_top5,
            'context_info': context_info,
            'c0br4_time_seconds': c0br4_time,
            'analysis_time_actual': analysis_time,
            'engine_output': engine_output,
            'timestamp': datetime.now().isoformat()
        }
        
        print("-" * 60)
        return result
    
    def run_analysis(self, 
                     num_puzzles: int = 50,
                     rating_min: int = 1200,
                     rating_max: int = 1800,
                     c0br4_time: float = 8.0,
                     themes_filter: Optional[List[str]] = None) -> List[Dict]:
        """Run analysis on multiple puzzles with C0BR4-specific focus"""
        
        print(f"C0BR4 Puzzle Analysis - {num_puzzles} puzzles")
        print(f"Rating range: {rating_min}-{rating_max}")
        print(f"C0BR4 thinking time: {c0br4_time} seconds")
        print(f"Focus: Rule compliance, bitboard validation, tactical awareness")
        if themes_filter:
            print(f"Theme filter: {themes_filter}")
        print("=" * 60)
        
        # Get puzzles from database - focus on tactical themes for C0BR4
        if not themes_filter:
            # Default themes that test rule compliance and tactics
            themes_filter = ['castling', 'pin', 'fork', 'skewer', 'discovery', 'endgame']
        
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
            result = self.analyze_puzzle(puzzle, c0br4_time)
            if result:
                results.append(result)
                self.results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """Generate C0BR4-specific analysis report"""
        if not results:
            return {}
        
        total_puzzles = len(results)
        total_score = sum(r['c0br4_score'] for r in results)
        max_possible_score = total_puzzles * 5
        
        # Legal move analysis
        legal_moves = sum(1 for r in results if r['c0br4_move_legal'])
        illegal_moves = total_puzzles - legal_moves
        legal_move_rate = (legal_moves / total_puzzles) * 100
        
        # Score distribution
        score_dist = {i: 0 for i in range(6)}
        for result in results:
            score_dist[result['c0br4_score']] += 1
        
        # Rank distribution
        rank_dist = {i: 0 for i in range(6)}  # 0 = not in top 5, 1-5 = ranks
        for result in results:
            rank_dist[result['c0br4_rank']] += 1
        
        # Theme analysis
        theme_performance = {}
        for result in results:
            for theme in result['themes']:
                if theme not in theme_performance:
                    theme_performance[theme] = {'total': 0, 'score_sum': 0, 'legal_moves': 0}
                theme_performance[theme]['total'] += 1
                theme_performance[theme]['score_sum'] += result['c0br4_score']
                if result['c0br4_move_legal']:
                    theme_performance[theme]['legal_moves'] += 1
        
        # Calculate theme averages
        for theme in theme_performance:
            theme_data = theme_performance[theme]
            theme_data['average_score'] = theme_data['score_sum'] / theme_data['total']
            theme_data['percentage'] = (theme_data['score_sum'] / (theme_data['total'] * 5)) * 100
            theme_data['legal_rate'] = (theme_data['legal_moves'] / theme_data['total']) * 100
        
        # Top 5 hit rate (only for legal moves)
        top5_hits = sum(1 for r in results if r['c0br4_rank'] > 0 and r['c0br4_move_legal'])
        top5_rate = (top5_hits / total_puzzles) * 100
        
        # Solution finding rate
        solutions_found = sum(1 for r in results if r['c0br4_found_solution'])
        solution_rate = (solutions_found / total_puzzles) * 100
        
        report = {
            'total_puzzles': total_puzzles,
            'total_score': total_score,
            'max_possible_score': max_possible_score,
            'average_score': total_score / total_puzzles,
            'percentage_score': (total_score / max_possible_score) * 100,
            'legal_moves': legal_moves,
            'illegal_moves': illegal_moves,
            'legal_move_rate': legal_move_rate,
            'top5_hits': top5_hits,
            'top5_hit_rate': top5_rate,
            'solutions_found': solutions_found,
            'solution_rate': solution_rate,
            'score_distribution': score_dist,
            'rank_distribution': rank_dist,
            'theme_performance': theme_performance,
            'rule_infractions': len(self.rule_infractions),
            'illegal_moves_detected': len(self.illegal_moves_detected),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted C0BR4 analysis report"""
        print("\n" + "=" * 80)
        print("C0BR4 PUZZLE ANALYSIS REPORT")
        print("=" * 80)
        
        print(f"Puzzles Analyzed: {report['total_puzzles']}")
        print(f"Total Score: {report['total_score']}/{report['max_possible_score']}")
        print(f"Average Score: {report['average_score']:.2f}/5.0")
        print(f"Percentage Score: {report['percentage_score']:.1f}%")
        
        # Rule compliance section
        print("\n🔒 RULE COMPLIANCE ANALYSIS:")
        print(f"Legal Moves: {report['legal_moves']}/{report['total_puzzles']} ({report['legal_move_rate']:.1f}%)")
        print(f"Illegal Moves: {report['illegal_moves']} ({100-report['legal_move_rate']:.1f}%)")
        print(f"Rule Infractions Detected: {report['rule_infractions']}")
        
        if report['illegal_moves'] > 0:
            print("🚨 WARNING: Illegal moves detected! Bitboard validation may need improvement.")
        else:
            print("✅ No illegal moves detected - bitboard validation working correctly!")
        
        print(f"\nTop-5 Hit Rate: {report['top5_hits']}/{report['total_puzzles']} ({report['top5_hit_rate']:.1f}%)")
        print(f"Solution Finding Rate: {report['solutions_found']}/{report['total_puzzles']} ({report['solution_rate']:.1f}%)")
        
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
        
        print("\nTheme Performance:")
        theme_items = list(report['theme_performance'].items())
        theme_items.sort(key=lambda x: x[1]['average_score'], reverse=True)
        
        for theme, data in theme_items:
            avg_score = data['average_score']
            percentage = data['percentage']
            legal_rate = data['legal_rate']
            count = data['total']
            print(f"  {theme:15s}: {avg_score:.2f}/5.0 ({percentage:4.1f}%) Legal: {legal_rate:4.1f}% [{count:2d} puzzles]")
    
    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"c0br4_puzzle_analysis_{timestamp}.json"
        
        data = {
            'analysis_results': self.results,
            'report': self.generate_report(self.results),
            'rule_infractions': self.rule_infractions,
            'illegal_moves_detected': self.illegal_moves_detected,
            'metadata': {
                'c0br4_path': self.c0br4_path,
                'stockfish_path': self.stockfish_path,
                'puzzle_db_path': self.puzzle_db_path,
                'timestamp': datetime.now().isoformat(),
                'focus': 'Rule compliance and bitboard validation'
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to: {filename}")


def main():
    """Main execution function"""
    try:
        analyzer = C0BR4PuzzleAnalyzer()
        
        # Run analysis focusing on rule compliance and tactical awareness
        results = analyzer.run_analysis(
            num_puzzles=50,
            rating_min=1200,
            rating_max=1600,
            c0br4_time=8.0,  # Give C0BR4 8 seconds per puzzle
            themes_filter=['castling', 'pin', 'fork', 'skewer', 'discovery', 'endgame', 'mate']
        )
        
        if results:
            # Generate and print report
            report = analyzer.generate_report(results)
            analyzer.print_report(report)
            
            # Save results
            analyzer.save_results()
            
            # Print rule infraction summary if any
            if analyzer.rule_infractions:
                print("\n🚨 RULE INFRACTIONS DETECTED:")
                for infraction in analyzer.rule_infractions:
                    print(f"  Puzzle {infraction['puzzle_id']}: {infraction['illegal_move']} - {infraction['reason']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
