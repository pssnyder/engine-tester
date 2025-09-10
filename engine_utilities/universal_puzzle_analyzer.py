#!/usr/bin/env python3
"""
Universal Chess Engine Puzzle Analyzer

Advanced puzzle testing system that works with any UCI-compatible chess engine:
1. Pulls positions from puzzle database
2. Analyzes complete puzzle sequences, not just first position
3. Plays through entire solution chains with the test engine
4. Compares each move against Stockfish's top 5 moves
5. Calculates weighted accuracy scores (later moves weighted higher)
6. Estimates engine's puzzle rating based on perfect/high-accuracy performance
7. Tracks performance degradation through sequence depth
8. Provides comprehensive theme-based analysis

Enhanced Features:
- Universal UCI engine support: V7P3R, C0BR4, SlowMate, or any UCI engine
- Sequence analysis: Plays opponent moves and challenges engine on each position
- Weighted scoring: Later positions in sequences count for more
- Rating estimation: Analyzes puzzle ratings where engine excels
- Position depth analysis: Shows how performance changes with sequence depth
- Comprehensive reporting: Theme performance, accuracy distributions, insights
- Dynamic engine info: Automatically detects engine name and version via UCI

Scoring: 5pts (1st), 4pts (2nd), 3pts (3rd), 2pts (4th), 1pt (5th), 0pts (not in top 5)
Sequence Accuracy: Weighted exponentially (1, 1.5, 2.25, 3.375, etc.)
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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'chess-puzzle-challenger', 'src'))
try:
    from database import PuzzleDatabase, Puzzle
except ImportError:
    print("Error: Could not import puzzle database. Make sure chess-puzzle-challenger is available.")
    sys.exit(1)


class UniversalPuzzleAnalyzer:
    """Analyzes any UCI chess engine's performance against puzzle database using Stockfish comparison"""
    
    def __init__(self, 
                 engine_path: str,
                 stockfish_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe",
                 puzzle_db_path: str = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\chess-puzzle-challenger\puzzles.db"):
        
        self.engine_path = engine_path
        self.stockfish_path = stockfish_path
        self.puzzle_db_path = puzzle_db_path
        self.results = []
        
        # Verify engines exist
        if not os.path.exists(engine_path):
            raise FileNotFoundError(f"Test engine not found: {engine_path}")
        if not os.path.exists(stockfish_path):
            raise FileNotFoundError(f"Stockfish engine not found: {stockfish_path}")
        if not os.path.exists(puzzle_db_path):
            raise FileNotFoundError(f"Puzzle database not found: {puzzle_db_path}")
        
        # Get engine information via UCI
        self.engine_info = self.get_engine_info()
        self.engine_name = self.engine_info.get('name', os.path.basename(engine_path))
        print(f"Initialized Universal Puzzle Analyzer for: {self.engine_name}")
    
    def get_engine_info(self) -> Dict[str, str]:
        """Get engine information via UCI protocol"""
        try:
            process = subprocess.Popen(
                self.engine_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            engine_info = {}
            
            # Send UCI command
            if process.stdin:
                process.stdin.write("uci\n")
                process.stdin.flush()
            
            # Read UCI response
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                if not process.stdout:
                    break
                    
                if process.poll() is not None:
                    break
                
                try:
                    line = process.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    line = line.strip()
                    
                    if line.startswith("id name"):
                        engine_info['name'] = line[8:].strip()
                    elif line.startswith("id author"):
                        engine_info['author'] = line[9:].strip()
                    elif line == "uciok":
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
            
            return engine_info
            
        except Exception as e:
            print(f"Warning: Could not get engine info via UCI: {e}")
            return {'name': os.path.basename(self.engine_path)}
    
    def get_engine_move(self, fen: str, time_seconds: float = 10.0) -> Optional[str]:
        """Get the test engine's best move for a position with generous time"""
        try:
            process = subprocess.Popen(
                self.engine_path,
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
            print(f"Error getting {self.engine_name} move: {e}")
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
    
    def score_engine_move(self, engine_move: str, stockfish_moves: List[Tuple[str, int]]) -> Tuple[int, int]:
        """
        Score engine's move based on Stockfish ranking
        Returns: (score, rank) where rank is 1-5 or 0 if not in top 5
        """
        if not engine_move or not stockfish_moves:
            return 0, 0
        
        for rank, (sf_move, _) in enumerate(stockfish_moves, 1):
            if engine_move == sf_move:
                score = 6 - rank  # 5pts for 1st, 4pts for 2nd, ..., 1pt for 5th
                return score, rank
        
        return 0, 0  # Not in top 5
    
    def calculate_weighted_sequence_score(self, sequence_results: List[bool]) -> float:
        """
        Calculate weighted accuracy score for puzzle sequence
        Later moves in the sequence are weighted more heavily
        Returns: weighted accuracy percentage (0-100)
        """
        if not sequence_results:
            return 0.0
        
        total_weight = 0.0
        weighted_correct = 0.0
        
        for i, is_correct in enumerate(sequence_results):
            # Exponential weighting: later moves are more important
            # Weight increases exponentially: 1, 1.5, 2.25, 3.375, etc.
            weight = 1.5 ** i
            total_weight += weight
            
            if is_correct:
                weighted_correct += weight
        
        return (weighted_correct / total_weight) * 100 if total_weight > 0 else 0.0
    
    def parse_puzzle_sequence(self, puzzle: Puzzle) -> List[str]:
        """Parse puzzle moves into sequence of individual moves"""
        if not puzzle.moves:
            return []
        return puzzle.moves.split()
    
    def analyze_puzzle_sequence(self, puzzle: Puzzle, engine_time: float = 10.0) -> Optional[Dict]:
        """
        Analyze complete puzzle sequence, playing through all moves
        Returns detailed analysis of engine's performance on each position
        """
        print(f"Analyzing puzzle {puzzle.id} (Rating: {puzzle.rating})")
        print(f"Themes: {puzzle.themes}")
        print(f"Original FEN: {puzzle.fen}")
        
        sequence = self.parse_puzzle_sequence(puzzle)
        if len(sequence) < 2:
            print(f"❌ Insufficient moves in sequence: {len(sequence)}")
            return None
        
        print(f"Solution sequence ({len(sequence)} moves): {' '.join(sequence)}")
        
        # Initialize tracking variables
        board = chess.Board(puzzle.fen)
        sequence_results = []
        position_analyses = []
        engine_found_all = True
        
        # Process each position in the sequence
        for move_index in range(0, len(sequence), 2):
            position_num = (move_index // 2) + 1
            
            # Check if we have both opponent move and expected response
            if move_index >= len(sequence):
                break
                
            opponent_move_text = sequence[move_index]
            expected_move_text = sequence[move_index + 1] if move_index + 1 < len(sequence) else None
            
            if not expected_move_text:
                print(f"Position {position_num}: No expected response for opponent move {opponent_move_text}")
                break
            
            print(f"\n--- Position {position_num} ---")
            current_fen = board.fen()
            turn_info = f"{'White' if board.turn else 'Black'} to move"
            print(f"Current position: {turn_info}")
            
            # Apply opponent's move
            try:
                # Try UCI first, then SAN
                try:
                    opponent_move = chess.Move.from_uci(opponent_move_text)
                    if opponent_move not in board.legal_moves:
                        raise ValueError("Move not legal")
                except:
                    opponent_move = board.parse_san(opponent_move_text)
                
                board.push(opponent_move)
                challenge_fen = board.fen()
                print(f"After opponent plays {opponent_move_text}: {challenge_fen}")
                
            except Exception as e:
                print(f"❌ Cannot apply opponent move {opponent_move_text}: {e}")
                break
            
            # Parse expected move
            try:
                try:
                    expected_move = chess.Move.from_uci(expected_move_text)
                    if expected_move not in board.legal_moves:
                        raise ValueError("Move not legal")
                    expected_move_uci = str(expected_move)
                except:
                    expected_move = board.parse_san(expected_move_text)
                    expected_move_uci = str(expected_move)
                
                print(f"Expected response: {expected_move_uci}")
                
            except Exception as e:
                print(f"❌ Cannot parse expected move {expected_move_text}: {e}")
                break
            
            # Get engine's move for this position
            print(f"Challenging {self.engine_name} with {engine_time}s...")
            start_time = time.time()
            engine_move = self.get_engine_move(challenge_fen, engine_time)
            analysis_time = time.time() - start_time
            
            if not engine_move:
                print(f"❌ {self.engine_name} failed to return move (took {analysis_time:.1f}s)")
                sequence_results.append(False)
                engine_found_all = False
                # Continue to next position anyway
                try:
                    board.push(expected_move)
                except:
                    break
                continue
            
            print(f"{self.engine_name} chose: {engine_move} (took {analysis_time:.1f}s)")
            
            # Get Stockfish analysis for this position
            stockfish_moves = self.get_stockfish_top_moves(challenge_fen, 5, 2.0)
            if stockfish_moves:
                print("Stockfish's top 5:")
                for i, (move, score) in enumerate(stockfish_moves, 1):
                    indicator = "🎯" if move == expected_move_uci else "  "
                    engine_indicator = "👑" if move == engine_move else "  "
                    print(f"  {i}. {move} (score: {score:+d}) {indicator}{engine_indicator}")
            
            # Score engine's move
            score, rank = self.score_engine_move(engine_move, stockfish_moves)
            found_solution = engine_move == expected_move_uci
            sequence_results.append(found_solution)
            
            if found_solution:
                print(f"✅ {self.engine_name} found the correct move! (Stockfish rank: #{rank if rank > 0 else 'not in top 5'})")
            else:
                print(f"❌ {self.engine_name} missed the correct move (chose rank #{rank if rank > 0 else 'not in top 5'})")
                engine_found_all = False
            
            # Store position analysis
            position_analysis = {
                'position_number': position_num,
                'challenge_fen': challenge_fen,
                'opponent_move': opponent_move_text,
                'expected_move': expected_move_uci,
                'engine_move': engine_move,
                'engine_found_solution': found_solution,
                'engine_stockfish_score': score,
                'engine_stockfish_rank': rank,
                'stockfish_top_moves': stockfish_moves,
                'analysis_time': analysis_time,
                'turn_info': f"{'White' if not board.turn else 'Black'} to move after opponent's {opponent_move_text}"
            }
            position_analyses.append(position_analysis)
            
            # Apply the expected move to continue sequence
            try:
                board.push(expected_move)
            except Exception as e:
                print(f"❌ Cannot continue sequence after {expected_move_text}: {e}")
                break
        
        # Calculate sequence metrics
        if not sequence_results:
            print("❌ No positions were successfully analyzed")
            return None
        
        sequence_accuracy = (sum(sequence_results) / len(sequence_results)) * 100
        weighted_accuracy = self.calculate_weighted_sequence_score(sequence_results)
        
        print(f"\n🎯 SEQUENCE SUMMARY:")
        print(f"Positions analyzed: {len(sequence_results)}")
        print(f"Correct solutions: {sum(sequence_results)}/{len(sequence_results)}")
        print(f"Linear accuracy: {sequence_accuracy:.1f}%")
        print(f"Weighted accuracy: {weighted_accuracy:.1f}%")
        print(f"Perfect sequence: {'Yes' if engine_found_all else 'No'}")
        
        # Compile comprehensive result
        result = {
            'puzzle_id': puzzle.id,
            'original_fen': puzzle.fen,
            'rating': puzzle.rating,
            'themes': puzzle.themes.split() if puzzle.themes else [],
            'solution_sequence': sequence,
            'positions_analyzed': len(sequence_results),
            'sequence_results': sequence_results,
            'sequence_accuracy_linear': sequence_accuracy,
            'sequence_accuracy_weighted': weighted_accuracy,
            'perfect_sequence': engine_found_all,
            'position_analyses': position_analyses,
            'engine_time_seconds': engine_time,
            'timestamp': datetime.now().isoformat()
        }
        
        print("-" * 60)
        return result
    
    def analyze_puzzle(self, puzzle: Puzzle, engine_time: float = 10.0) -> Optional[Dict]:
        """Analyze a puzzle using the enhanced sequence-based approach"""
        return self.analyze_puzzle_sequence(puzzle, engine_time)
    
    def extract_puzzle_ids_from_results(self, results_file: str) -> List[str]:
        """Extract puzzle IDs from a previous analysis results file"""
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            puzzle_ids = []
            
            # Try to extract from analysis_results
            if 'analysis_results' in data:
                puzzle_ids = [result['puzzle_id'] for result in data['analysis_results'] if 'puzzle_id' in result]
            # Fallback: try direct list of results
            elif isinstance(data, list):
                puzzle_ids = [result['puzzle_id'] for result in data if 'puzzle_id' in result]
            
            print(f"Extracted {len(puzzle_ids)} puzzle IDs from {results_file}")
            return puzzle_ids
            
        except Exception as e:
            print(f"Error extracting puzzle IDs from {results_file}: {e}")
            return []
    
    def run_analysis(self, 
                     num_puzzles: int = 100,
                     rating_min: int = 1200,
                     rating_max: int = 2000,
                     engine_time: float = 10.0,
                     themes_filter: Optional[List[str]] = None,
                     force_puzzle_ids: Optional[List[str]] = None,
                     comparison_file: Optional[str] = None) -> List[Dict]:
        """Run analysis on multiple puzzles with optional puzzle ID forcing for comparison"""
        
        # Handle comparison file input
        if comparison_file and not force_puzzle_ids:
            force_puzzle_ids = self.extract_puzzle_ids_from_results(comparison_file)
            if not force_puzzle_ids:
                print(f"Warning: Could not extract puzzle IDs from {comparison_file}, proceeding with normal analysis")
        
        if force_puzzle_ids:
            print(f"{self.engine_name} Universal Puzzle Analysis - {len(force_puzzle_ids)} forced puzzles")
            print(f"Engine: {self.engine_name}")
            print(f"Puzzle forcing mode: Using specific puzzle IDs")
            print(f"Engine thinking time: {engine_time} seconds")
            if comparison_file:
                print(f"Comparison file: {comparison_file}")
        else:
            print(f"{self.engine_name} Universal Puzzle Analysis - {num_puzzles} puzzles")
            print(f"Engine: {self.engine_name}")
            print(f"Rating range: {rating_min}-{rating_max}")
            print(f"Engine thinking time: {engine_time} seconds")
            if themes_filter:
                print(f"Theme filter: {themes_filter}")
        print("=" * 60)
        
        # Get puzzles from database
        db = PuzzleDatabase(self.puzzle_db_path)
        
        if force_puzzle_ids:
            # Get specific puzzles by ID
            puzzles = []
            for puzzle_id in force_puzzle_ids:
                puzzle = db.get_puzzle_by_id(puzzle_id)
                if puzzle:
                    puzzles.append(puzzle)
                else:
                    print(f"Warning: Puzzle ID {puzzle_id} not found in database")
        else:
            # Normal puzzle query
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
            result = self.analyze_puzzle(puzzle, engine_time)
            if result:
                results.append(result)
                self.results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """Generate enhanced analysis report with sequence-based metrics"""
        if not results:
            return {}
        
        total_puzzles = len(results)
        
        # Legacy single-position metrics (for backward compatibility)
        total_positions = sum(r.get('positions_analyzed', 1) for r in results)
        
        # Sequence-based metrics
        linear_accuracies = [r.get('sequence_accuracy_linear', 0) for r in results if 'sequence_accuracy_linear' in r]
        weighted_accuracies = [r.get('sequence_accuracy_weighted', 0) for r in results if 'sequence_accuracy_weighted' in r]
        perfect_sequences = sum(1 for r in results if r.get('perfect_sequence', False))
        
        avg_linear_accuracy = sum(linear_accuracies) / len(linear_accuracies) if linear_accuracies else 0
        avg_weighted_accuracy = sum(weighted_accuracies) / len(weighted_accuracies) if weighted_accuracies else 0
        perfect_sequence_rate = (perfect_sequences / total_puzzles) * 100
        
        # Rating analysis for estimation
        perfect_puzzle_ratings = [r['rating'] for r in results if r.get('perfect_sequence', False)]
        high_accuracy_ratings = [r['rating'] for r in results if r.get('sequence_accuracy_weighted', 0) >= 80]
        
        # Calculate estimated rating range where engine performs well
        estimated_rating_range = {
            'perfect_sequences': {
                'count': len(perfect_puzzle_ratings),
                'min_rating': min(perfect_puzzle_ratings) if perfect_puzzle_ratings else 0,
                'max_rating': max(perfect_puzzle_ratings) if perfect_puzzle_ratings else 0,
                'avg_rating': sum(perfect_puzzle_ratings) / len(perfect_puzzle_ratings) if perfect_puzzle_ratings else 0
            },
            'high_accuracy': {
                'count': len(high_accuracy_ratings),
                'min_rating': min(high_accuracy_ratings) if high_accuracy_ratings else 0,
                'max_rating': max(high_accuracy_ratings) if high_accuracy_ratings else 0,
                'avg_rating': sum(high_accuracy_ratings) / len(high_accuracy_ratings) if high_accuracy_ratings else 0
            }
        }
        
        # Position-by-position performance analysis
        position_performance = {}
        for result in results:
            if 'position_analyses' in result:
                for pos_analysis in result['position_analyses']:
                    pos_num = pos_analysis['position_number']
                    if pos_num not in position_performance:
                        position_performance[pos_num] = {'total': 0, 'correct': 0, 'stockfish_scores': []}
                    
                    position_performance[pos_num]['total'] += 1
                    if pos_analysis['engine_found_solution']:
                        position_performance[pos_num]['correct'] += 1
                    position_performance[pos_num]['stockfish_scores'].append(pos_analysis['engine_stockfish_score'])
        
        # Calculate position accuracy rates
        for pos_num in position_performance:
            data = position_performance[pos_num]
            data['accuracy_rate'] = (data['correct'] / data['total']) * 100
            data['avg_stockfish_score'] = sum(data['stockfish_scores']) / len(data['stockfish_scores'])
        
        # Theme analysis with sequence metrics
        theme_performance = {}
        for result in results:
            for theme in result.get('themes', []):
                if theme not in theme_performance:
                    theme_performance[theme] = {
                        'total': 0, 
                        'perfect_sequences': 0,
                        'linear_accuracy_sum': 0,
                        'weighted_accuracy_sum': 0,
                        'ratings': []
                    }
                
                theme_data = theme_performance[theme]
                theme_data['total'] += 1
                theme_data['linear_accuracy_sum'] += result.get('sequence_accuracy_linear', 0)
                theme_data['weighted_accuracy_sum'] += result.get('sequence_accuracy_weighted', 0)
                theme_data['ratings'].append(result['rating'])
                
                if result.get('perfect_sequence', False):
                    theme_data['perfect_sequences'] += 1
        
        # Calculate theme averages
        for theme in theme_performance:
            data = theme_performance[theme]
            data['avg_linear_accuracy'] = data['linear_accuracy_sum'] / data['total']
            data['avg_weighted_accuracy'] = data['weighted_accuracy_sum'] / data['total']
            data['perfect_sequence_rate'] = (data['perfect_sequences'] / data['total']) * 100
            data['avg_rating'] = sum(data['ratings']) / len(data['ratings'])
        
        # Accuracy distribution
        accuracy_buckets = {'0-20%': 0, '20-40%': 0, '40-60%': 0, '60-80%': 0, '80-100%': 0}
        for accuracy in weighted_accuracies:
            if accuracy < 20:
                accuracy_buckets['0-20%'] += 1
            elif accuracy < 40:
                accuracy_buckets['20-40%'] += 1
            elif accuracy < 60:
                accuracy_buckets['40-60%'] += 1
            elif accuracy < 80:
                accuracy_buckets['60-80%'] += 1
            else:
                accuracy_buckets['80-100%'] += 1
        
        report = {
            'engine_name': self.engine_name,
            'engine_info': self.engine_info,
            'total_puzzles': total_puzzles,
            'total_positions_analyzed': total_positions,
            'sequence_metrics': {
                'avg_linear_accuracy': avg_linear_accuracy,
                'avg_weighted_accuracy': avg_weighted_accuracy,
                'perfect_sequences': perfect_sequences,
                'perfect_sequence_rate': perfect_sequence_rate
            },
            'estimated_rating_analysis': estimated_rating_range,
            'position_performance': position_performance,
            'theme_performance': theme_performance,
            'accuracy_distribution': accuracy_buckets,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print enhanced analysis report with sequence-based metrics"""
        engine_name = report.get('engine_name', 'Unknown Engine')
        
        print("\n" + "=" * 80)
        print(f"{engine_name.upper()} ENHANCED PUZZLE ANALYSIS REPORT")
        print("=" * 80)
        
        print(f"Engine: {engine_name}")
        if 'engine_info' in report and 'author' in report['engine_info']:
            print(f"Author: {report['engine_info']['author']}")
        
        print(f"Puzzles Analyzed: {report['total_puzzles']}")
        print(f"Total Positions: {report['total_positions_analyzed']}")
        
        # Sequence Performance Metrics
        seq_metrics = report['sequence_metrics']
        print(f"\n🎯 SEQUENCE PERFORMANCE:")
        print(f"Average Linear Accuracy: {seq_metrics['avg_linear_accuracy']:.1f}%")
        print(f"Average Weighted Accuracy: {seq_metrics['avg_weighted_accuracy']:.1f}%")
        print(f"Perfect Sequences: {seq_metrics['perfect_sequences']}/{report['total_puzzles']} ({seq_metrics['perfect_sequence_rate']:.1f}%)")
        
        # Rating Analysis for Engine Estimation
        rating_analysis = report['estimated_rating_analysis']
        print(f"\n📊 ESTIMATED {engine_name.upper()} RATING ANALYSIS:")
        
        perfect_data = rating_analysis['perfect_sequences']
        if perfect_data['count'] > 0:
            print(f"Perfect Sequences ({perfect_data['count']} puzzles):")
            print(f"  Rating Range: {perfect_data['min_rating']}-{perfect_data['max_rating']}")
            print(f"  Average Rating: {perfect_data['avg_rating']:.0f}")
        
        high_acc_data = rating_analysis['high_accuracy']
        if high_acc_data['count'] > 0:
            print(f"High Accuracy ≥80% ({high_acc_data['count']} puzzles):")
            print(f"  Rating Range: {high_acc_data['min_rating']}-{high_acc_data['max_rating']}")
            print(f"  Average Rating: {high_acc_data['avg_rating']:.0f}")
        
        # Engine Estimated Rating Range
        if perfect_data['count'] > 0 and high_acc_data['count'] > 0:
            estimated_min = min(perfect_data['min_rating'], high_acc_data['min_rating'])
            estimated_max = max(perfect_data['max_rating'], high_acc_data['max_rating'])
            estimated_avg = (perfect_data['avg_rating'] + high_acc_data['avg_rating']) / 2
            print(f"\n🎲 ESTIMATED {engine_name.upper()} RATING: {estimated_min}-{estimated_max} (avg: {estimated_avg:.0f})")
        
        # Accuracy Distribution
        print(f"\nAccuracy Distribution:")
        for bucket, count in report['accuracy_distribution'].items():
            percentage = (count / report['total_puzzles']) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {bucket:8s}: {count:3d} ({percentage:4.1f}%) {bar}")
        
        # Position-by-Position Performance
        if report['position_performance']:
            print(f"\n📍 POSITION PERFORMANCE (Sequence Depth Analysis):")
            for pos_num in sorted(report['position_performance'].keys()):
                data = report['position_performance'][pos_num]
                print(f"  Position {pos_num}: {data['correct']}/{data['total']} ({data['accuracy_rate']:.1f}%) - Avg SF Score: {data['avg_stockfish_score']:.1f}")
        
        # Theme Performance (Top 15)
        print(f"\n🎨 THEME PERFORMANCE (Top 15 by Weighted Accuracy):")
        theme_items = list(report['theme_performance'].items())
        theme_items.sort(key=lambda x: x[1]['avg_weighted_accuracy'], reverse=True)
        
        for theme, data in theme_items[:15]:
            perfect_rate = data['perfect_sequence_rate']
            weighted_acc = data['avg_weighted_accuracy']
            count = data['total']
            avg_rating = data['avg_rating']
            print(f"  {theme:20s}: {weighted_acc:4.1f}% weighted ({perfect_rate:4.1f}% perfect) [{count:2d} puzzles, avg {avg_rating:.0f}]")
        
        # Performance Insights
        print(f"\n💡 PERFORMANCE INSIGHTS:")
        
        # Calculate performance degradation through sequence
        if report['position_performance']:
            pos_data = report['position_performance']
            if 1 in pos_data and len(pos_data) > 1:
                first_pos_acc = pos_data[1]['accuracy_rate']
                later_pos_accs = [pos_data[i]['accuracy_rate'] for i in pos_data if i > 1]
                if later_pos_accs:
                    avg_later_acc = sum(later_pos_accs) / len(later_pos_accs)
                    degradation = first_pos_acc - avg_later_acc
                    print(f"  Sequence Degradation: {degradation:+.1f}% (first pos: {first_pos_acc:.1f}%, later avg: {avg_later_acc:.1f}%)")
        
        # Theme strengths and weaknesses
        if theme_items:
            strongest_theme = theme_items[0]
            weakest_theme = theme_items[-1]
            print(f"  Strongest Theme: {strongest_theme[0]} ({strongest_theme[1]['avg_weighted_accuracy']:.1f}%)")
            print(f"  Weakest Theme: {weakest_theme[0]} ({weakest_theme[1]['avg_weighted_accuracy']:.1f}%)")
        
        print("=" * 80)
    
    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            engine_safe_name = self.engine_name.replace(' ', '_').replace('.', '_')
            filename = f"{engine_safe_name}_enhanced_sequence_analysis_{timestamp}.json"
        
        data = {
            'analysis_results': self.results,
            'report': self.generate_report(self.results),
            'metadata': {
                'engine_path': self.engine_path,
                'engine_name': self.engine_name,
                'engine_info': self.engine_info,
                'stockfish_path': self.stockfish_path,
                'puzzle_db_path': self.puzzle_db_path,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to: {filename}")


def main():
    """Main execution function with engine selection and comparison support"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Universal Chess Engine Puzzle Analyzer with Comparison Support')
    parser.add_argument('--engine', required=True, help='Path to the UCI chess engine to test')
    parser.add_argument('--puzzles', type=int, default=50, help='Number of puzzles to analyze (default: 50)')
    parser.add_argument('--time', type=float, default=15.0, help='Time per position in seconds (default: 15.0)')
    parser.add_argument('--min-rating', type=int, default=1200, help='Minimum puzzle rating (default: 1200)')
    parser.add_argument('--max-rating', type=int, default=2200, help='Maximum puzzle rating (default: 2200)')
    parser.add_argument('--themes', nargs='*', help='Filter by puzzle themes (optional)')
    parser.add_argument('--comparison-file', type=str, help='JSON file from previous analysis to use same puzzle IDs for comparison')
    parser.add_argument('--force-puzzle-ids', nargs='*', help='Specific puzzle IDs to analyze (optional)')
    
    args = parser.parse_args()
    
    try:
        analyzer = UniversalPuzzleAnalyzer(engine_path=args.engine)
        
        # Run enhanced sequence analysis with comparison support
        results = analyzer.run_analysis(
            num_puzzles=args.puzzles,
            rating_min=args.min_rating,
            rating_max=args.max_rating,
            engine_time=args.time,
            themes_filter=args.themes,
            force_puzzle_ids=args.force_puzzle_ids,
            comparison_file=args.comparison_file
        )
        
        if results:
            # Generate and print enhanced report
            report = analyzer.generate_report(results)
            analyzer.print_report(report)
            
            # Save results with timestamp
            analyzer.save_results()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
