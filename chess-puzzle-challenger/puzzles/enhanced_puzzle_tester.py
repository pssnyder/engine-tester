#!/usr/bin/env python3
"""
Enhanced Puzzle Testing Framework for Cece Engine
Implements advanced sequence testing and evaluation analysis
"""

import csv
import random
import json
import subprocess
import time
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import chess

@dataclass
class PuzzleMoveResult:
    """Result for a single move in a puzzle sequence."""
    move_number: int
    expected_move: str
    engine_move: str
    position_fen: str
    correct: bool
    evaluation_score: Optional[int] = None
    search_depth: Optional[int] = None
    time_taken: float = 0.0

@dataclass
class PuzzleSequenceResult:
    """Result for testing an entire puzzle sequence."""
    puzzle_id: str
    rating: int
    themes: List[str]
    starting_fen: str
    solution_moves: List[str]
    move_results: List[PuzzleMoveResult]
    fully_solved: bool
    moves_solved: int
    total_moves: int
    total_time: float
    notes: str = ""
    
    def success_rate(self) -> float:
        """Calculate percentage of moves solved correctly."""
        return (self.moves_solved / self.total_moves * 100) if self.total_moves > 0 else 0.0

@dataclass
class Puzzle:
    """Container for puzzle data."""
    puzzle_id: str
    fen: str
    moves: List[str]  # Solution moves
    rating: int
    themes: List[str]
    opening_tags: str
    
    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'Puzzle':
        """Create puzzle from CSV row."""
        return cls(
            puzzle_id=row[0],
            fen=row[1], 
            moves=row[2].split(),
            rating=int(row[3]) if row[3].isdigit() else 0,
            themes=row[7].split(),
            opening_tags=row[9] if len(row) > 9 else ""
        )

class EnhancedPuzzleTester:
    """Advanced puzzle tester with sequence analysis and evaluation debugging."""
    
    def __init__(self, engine_path: str, csv_path: str):
        self.engine_path = engine_path
        self.csv_path = csv_path
        self.solved_puzzles_file = "solved_puzzles.json"
        self.results_file = "puzzle_sequence_results.json"
        self.analytics_file = "puzzle_analytics.json"
        
        # Load previously solved puzzles and results
        self.solved_puzzles = self._load_solved_puzzles()
        self.results = self._load_results()
        
    def _load_solved_puzzles(self) -> set:
        """Load set of previously solved puzzle IDs."""
        if os.path.exists(self.solved_puzzles_file):
            with open(self.solved_puzzles_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_solved_puzzles(self):
        """Save solved puzzle IDs."""
        with open(self.solved_puzzles_file, 'w') as f:
            json.dump(list(self.solved_puzzles), f)
    
    def _load_results(self) -> List[PuzzleSequenceResult]:
        """Load previous test results."""
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                return [self._dict_to_result(item) for item in data]
        return []
    
    def _dict_to_result(self, data: Dict) -> PuzzleSequenceResult:
        """Convert dictionary back to PuzzleSequenceResult."""
        move_results = [PuzzleMoveResult(**mr) for mr in data['move_results']]
        return PuzzleSequenceResult(
            puzzle_id=data['puzzle_id'],
            rating=data['rating'],
            themes=data['themes'],
            starting_fen=data['starting_fen'],
            solution_moves=data['solution_moves'],
            move_results=move_results,
            fully_solved=data['fully_solved'],
            moves_solved=data['moves_solved'],
            total_moves=data['total_moves'],
            total_time=data['total_time'],
            notes=data.get('notes', '')
        )
    
    def _save_results(self):
        """Save test results."""
        with open(self.results_file, 'w') as f:
            json.dump([asdict(result) for result in self.results], f, indent=2)
    
    def get_random_puzzles(self, count: int, 
                          rating_min: int = 1200, rating_max: int = 1800,
                          themes_filter: Optional[List[str]] = None) -> List[Puzzle]:
        """Get random puzzles matching criteria, excluding already solved ones."""
        puzzles = []
        seen_ids = set()
        
        print(f"🔍 Searching for {count} puzzles (rating {rating_min}-{rating_max})")
        if themes_filter:
            print(f"   Themes: {', '.join(themes_filter)}")
        
        # Read CSV and collect matching puzzles
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row_num, row in enumerate(reader):
                if len(row) < 8:
                    continue
                    
                puzzle_id = row[0]
                if puzzle_id in self.solved_puzzles or puzzle_id in seen_ids:
                    continue
                    
                # Check rating
                try:
                    rating = int(row[3])
                    if not (rating_min <= rating <= rating_max):
                        continue
                except (ValueError, IndexError):
                    continue
                
                # Check themes filter
                if themes_filter:
                    puzzle_themes = row[7].split()
                    if not any(theme in puzzle_themes for theme in themes_filter):
                        continue
                
                puzzle = Puzzle.from_csv_row(row)
                puzzles.append(puzzle)
                seen_ids.add(puzzle_id)
                
                # Stop if we have enough candidates
                if len(puzzles) >= count * 5:  # Get 5x more for random selection
                    break
                    
                # Progress indicator
                if row_num % 100000 == 0 and row_num > 0:
                    print(f"   Scanned {row_num:,} puzzles, found {len(puzzles)} matches")
        
        print(f"✅ Found {len(puzzles)} matching puzzles")
        # Return random sample
        selected = random.sample(puzzles, min(count, len(puzzles)))
        print(f"📋 Selected {len(selected)} puzzles for testing")
        return selected
    
    def test_engine_move(self, fen: str, time_limit: float = 5.0) -> Tuple[Optional[str], float, Optional[int]]:
        """Test engine on a single position and return best move, time, and evaluation."""
        try:
            # Start engine process
            engine = subprocess.Popen(
                self.engine_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            start_time = time.time()
            
            # Send UCI commands with proper sequencing
            commands = [
                "uci",
                "isready",
                f"position fen {fen}",
                f"go movetime {int(time_limit * 1000)}"  # Convert to milliseconds
            ]
            
            # Send commands and collect output
            all_output = []
            engine_move = None
            evaluation_score = None
            
            for cmd in commands[:3]:  # Send first 3 commands
                if engine.stdin:
                    engine.stdin.write(f"{cmd}\n")
                    engine.stdin.flush()
                
                if cmd == "uci":
                    # Wait for uciok
                    while True:
                        if engine.stdout:
                            line = engine.stdout.readline()
                            if line:
                                line = line.strip()
                                all_output.append(line)
                                if line == "uciok":
                                    break
                elif cmd == "isready":
                    # Wait for readyok
                    while True:
                        if engine.stdout:
                            line = engine.stdout.readline()
                            if line:
                                line = line.strip()
                                all_output.append(line)
                                if line == "readyok":
                                    break
                elif cmd.startswith("position"):
                    # Brief pause for position setting
                    time.sleep(0.1)
                    # Read any immediate response
                    if engine.stdout:
                        try:
                            line = engine.stdout.readline()
                            if line:
                                all_output.append(line.strip())
                        except:
                            pass
            
            # Now send the go command
            if engine.stdin:
                engine.stdin.write(f"{commands[3]}\n")
                engine.stdin.flush()
            
            # Wait for bestmove with timeout
            search_start = time.time()
            while time.time() - search_start < time_limit + 2:
                if engine.stdout:
                    line = engine.stdout.readline()
                    if line:
                        line = line.strip()
                        all_output.append(line)
                        
                        # Extract evaluation score if present
                        if "Evaluation:" in line:
                            try:
                                eval_part = line.split("Evaluation:")[1].strip()
                                evaluation_score = int(eval_part.split()[0])
                            except:
                                pass
                        
                        if line.startswith("bestmove"):
                            parts = line.split()
                            if len(parts) > 1 and parts[1] != "0000":
                                engine_move = parts[1]
                            break
                else:
                    time.sleep(0.01)
            
            # Clean up
            if engine.stdin:
                engine.stdin.write("quit\n")
                engine.stdin.flush()
            engine.wait(timeout=2)
            
            elapsed = time.time() - start_time
            return engine_move, elapsed, evaluation_score
            
        except Exception as e:
            print(f"   ❌ Engine error: {e}")
            return None, 0.0, None
    
    def test_puzzle_sequence(self, puzzle: Puzzle, time_limit: float = 5.0) -> PuzzleSequenceResult:
        """Test engine on complete puzzle sequence with correct move alternation."""
        print(f"\n🧩 Testing Puzzle {puzzle.puzzle_id}")
        print(f"   Rating: {puzzle.rating}")
        print(f"   Themes: {' '.join(puzzle.themes)}")
        print(f"   Solution: {' '.join(puzzle.moves)}")
        
        move_results = []
        current_board = chess.Board(puzzle.fen)
        moves_solved = 0
        total_time = 0.0
        
        # Determine who is to move first from the FEN
        side_to_move = current_board.turn
        print(f"   Initial position: {'White' if side_to_move else 'Black'} to move")
        
        # Process moves in pairs: [engine_move, opponent_response, engine_move, opponent_response, ...]
        engine_moves_count = 0
        
        for move_num, expected_move in enumerate(puzzle.moves, 1):
            # Determine if this move should be played by the engine or opponent
            is_engine_move = (move_num % 2 == 1)  # Odd-numbered moves are engine moves
            
            if is_engine_move:
                engine_moves_count += 1
                print(f"\n   Engine Move {engine_moves_count}: Testing position {current_board.fen()}")
                print(f"   Expected: {expected_move}")
                
                # Test engine on current position
                engine_move, move_time, evaluation = self.test_engine_move(
                    current_board.fen(), time_limit
                )
                total_time += move_time
                
                correct = engine_move == expected_move
                if correct:
                    moves_solved += 1
                    print(f"   ✅ Correct! Engine played: {engine_move}")
                else:
                    print(f"   ❌ Wrong! Engine played: {engine_move}, expected: {expected_move}")
                    if evaluation is not None:
                        print(f"      Engine evaluation: {evaluation}")
                
                # Record result for engine moves only
                move_result = PuzzleMoveResult(
                    move_number=engine_moves_count,
                    expected_move=expected_move,
                    engine_move=engine_move or "timeout",
                    position_fen=current_board.fen(),
                    correct=correct,
                    evaluation_score=evaluation,
                    time_taken=move_time
                )
                move_results.append(move_result)
                
                # Apply the expected move to continue sequence
                try:
                    move = chess.Move.from_uci(expected_move)
                    current_board.push(move)
                except:
                    print(f"   ⚠️  Invalid move in puzzle: {expected_move}")
                    break
                    
                # If engine got it wrong, we might want to stop the sequence
                if not correct:
                    print(f"   🛑 Engine failed - stopping sequence evaluation")
                    # Still apply the correct move to continue analysis if desired
                    # (this allows us to see how the engine would handle subsequent positions)
                    
            else:
                # This is an opponent move - just apply it
                print(f"   Opponent plays: {expected_move}")
                try:
                    move = chess.Move.from_uci(expected_move)
                    current_board.push(move)
                except:
                    print(f"   ⚠️  Invalid opponent move: {expected_move}")
                    break
        
        # Calculate total engine moves (only odd-numbered moves in sequence)
        total_engine_moves = engine_moves_count
        fully_solved = moves_solved == total_engine_moves
        success_rate = (moves_solved / total_engine_moves * 100) if total_engine_moves > 0 else 0
        
        result = PuzzleSequenceResult(
            puzzle_id=puzzle.puzzle_id,
            rating=puzzle.rating,
            themes=puzzle.themes,
            starting_fen=puzzle.fen,
            solution_moves=puzzle.moves,
            move_results=move_results,
            fully_solved=fully_solved,
            moves_solved=moves_solved,
            total_moves=total_engine_moves,  # Only count engine moves
            total_time=total_time,
            notes=f"Engine moves: {moves_solved}/{total_engine_moves}, Success rate: {success_rate:.1f}%"
        )
        
        if fully_solved:
            print(f"   🎉 FULLY SOLVED! ({moves_solved}/{total_engine_moves} engine moves)")
            self.solved_puzzles.add(puzzle.puzzle_id)
        else:
            print(f"   📊 Partially solved: {moves_solved}/{total_engine_moves} engine moves ({success_rate:.1f}%)")
        
        return result
    
    def run_test_session(self, count: int = 10, **kwargs):
        """Run a comprehensive test session."""
        print(f"🚀 Enhanced Puzzle Test Session")
        print(f"Testing {count} puzzles with sequence analysis")
        print("=" * 60)
        
        # Get puzzles
        puzzles = self.get_random_puzzles(count, **kwargs)
        if not puzzles:
            print("❌ No puzzles found matching criteria")
            return
        
        session_results = []
        session_start = time.time()
        
        for i, puzzle in enumerate(puzzles, 1):
            print(f"\n[{i}/{len(puzzles)}] ", end="")
            result = self.test_puzzle_sequence(puzzle)
            session_results.append(result)
            self.results.append(result)
        
        # Save progress
        self._save_solved_puzzles()
        self._save_results()
        
        # Generate session analytics
        self._generate_session_analytics(session_results)
        
        session_time = time.time() - session_start
        print(f"\n🎯 Session Complete ({session_time:.1f}s)")
        print("=" * 60)
    
    def _generate_session_analytics(self, session_results: List[PuzzleSequenceResult]):
        """Generate detailed analytics for the session."""
        total_puzzles = len(session_results)
        fully_solved = sum(1 for r in session_results if r.fully_solved)
        total_moves = sum(r.total_moves for r in session_results)
        moves_solved = sum(r.moves_solved for r in session_results)
        
        print(f"\n📊 Session Analytics:")
        print(f"   Puzzles fully solved: {fully_solved}/{total_puzzles} ({fully_solved/total_puzzles*100:.1f}%)")
        print(f"   Individual moves solved: {moves_solved}/{total_moves} ({moves_solved/total_moves*100:.1f}%)")
        
        # Theme analysis
        theme_stats = {}
        rating_stats = {}
        
        for result in session_results:
            # Theme analysis
            for theme in result.themes:
                if theme not in theme_stats:
                    theme_stats[theme] = {'total': 0, 'solved': 0, 'moves_solved': 0, 'total_moves': 0}
                theme_stats[theme]['total'] += 1
                theme_stats[theme]['total_moves'] += result.total_moves
                theme_stats[theme]['moves_solved'] += result.moves_solved
                if result.fully_solved:
                    theme_stats[theme]['solved'] += 1
            
            # Rating analysis
            rating_range = f"{(result.rating // 100) * 100}-{(result.rating // 100) * 100 + 99}"
            if rating_range not in rating_stats:
                rating_stats[rating_range] = {'total': 0, 'solved': 0}
            rating_stats[rating_range]['total'] += 1
            if result.fully_solved:
                rating_stats[rating_range]['solved'] += 1
        
        print(f"\n🎭 Theme Performance:")
        for theme, stats in sorted(theme_stats.items()):
            if stats['total'] >= 2:  # Only show themes with 2+ puzzles
                puzzle_rate = stats['solved'] / stats['total'] * 100
                move_rate = stats['moves_solved'] / stats['total_moves'] * 100
                print(f"   {theme:15}: {stats['solved']:2}/{stats['total']:2} puzzles ({puzzle_rate:5.1f}%), "
                      f"{stats['moves_solved']:3}/{stats['total_moves']:3} moves ({move_rate:5.1f}%)")
        
        print(f"\n🎯 Rating Performance:")
        for rating_range, stats in sorted(rating_stats.items()):
            rate = stats['solved'] / stats['total'] * 100
            print(f"   {rating_range}: {stats['solved']}/{stats['total']} ({rate:.1f}%)")
        
        # Save analytics
        analytics_data = {
            'session_timestamp': time.time(),
            'total_puzzles': total_puzzles,
            'fully_solved': fully_solved,
            'total_moves': total_moves,
            'moves_solved': moves_solved,
            'theme_stats': theme_stats,
            'rating_stats': rating_stats,
            'puzzle_details': [asdict(r) for r in session_results]
        }
        
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics_data, f, indent=2)
        
        print(f"\n💾 Analytics saved to: {self.analytics_file}")
    
    def reset_solved_puzzles(self):
        """Reset the solved puzzles tracker."""
        self.solved_puzzles.clear()
        if os.path.exists(self.solved_puzzles_file):
            os.remove(self.solved_puzzles_file)
        print("✅ Solved puzzles tracker reset")

def main():
    """Main test runner with your specified configuration."""
    # Configuration
    engine_path = "../dist/Cece_v1.0.exe"
    csv_path = "lichess_db_puzzle.csv"
    
    if not os.path.exists(engine_path):
        print(f"❌ Engine not found: {engine_path}")
        return
    
    if not os.path.exists(csv_path):
        print(f"❌ Puzzle CSV not found: {csv_path}")
        return
    
    tester = EnhancedPuzzleTester(engine_path, csv_path)
    
    # Test configuration based on your requirements
    test_themes = [
        "mate",           # Mating patterns
        "advantage",      # Advantage evaluation  
        "endgame",        # Pawn positioning/endgames
        "exchange",       # Exchange evaluation
        "sacrifice"       # Exchange-related themes
    ]
    
    print("🎯 Configured for evaluation tuning:")
    print("   - Mating patterns")
    print("   - Pawn positioning/endgames") 
    print("   - Advantage evaluation")
    print("   - Exchange evaluation")
    print("   - Time limit: 5 seconds per move")
    
    # Run test session
    tester.run_test_session(
        count=8,  # Start with 8 puzzles
        rating_min=1200,
        rating_max=1700,
        themes_filter=test_themes
    )

if __name__ == "__main__":
    main()
