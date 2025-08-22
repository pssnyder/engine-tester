#!/usr/bin/env python3
"""
Puzzle Testing Framework for Cece Engine
Tests engine performance on tactical puzzles from Lichess database
"""

import csv
import random
import json
import subprocess
import time
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

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

@dataclass 
class PuzzleResult:
    """Container for puzzle test result."""
    puzzle_id: str
    solved: bool
    engine_move: str
    expected_move: str
    time_taken: float
    search_depth: int
    themes: List[str]
    rating: int
    notes: str = ""

class PuzzleTester:
    """Tests engine performance on tactical puzzles."""
    
    def __init__(self, engine_path: str, csv_path: str):
        self.engine_path = engine_path
        self.csv_path = csv_path
        self.solved_puzzles_file = "solved_puzzles.json"
        self.results_file = "puzzle_results.json"
        
        # Load previously solved puzzles
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
    
    def _load_results(self) -> List[PuzzleResult]:
        """Load previous test results."""
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                return [PuzzleResult(**item) for item in data]
        return []
    
    def _save_results(self):
        """Save test results."""
        with open(self.results_file, 'w') as f:
            json.dump([result.__dict__ for result in self.results], f, indent=2)
    
    def get_random_puzzles(self, count: int, 
                          rating_min: int = 1000, rating_max: int = 2000,
                          themes_filter: Optional[List[str]] = None) -> List[Puzzle]:
        """Get random puzzles matching criteria, excluding already solved ones."""
        puzzles = []
        seen_ids = set()
        
        # Read CSV and collect matching puzzles
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
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
                if len(puzzles) >= count * 10:  # Get 10x more for random selection
                    break
        
        # Return random sample
        return random.sample(puzzles, min(count, len(puzzles)))
    
    def test_puzzle(self, puzzle: Puzzle, time_limit: float = 3.0) -> PuzzleResult:
        """Test engine on a single puzzle."""
        print(f"Testing puzzle {puzzle.puzzle_id} (Rating: {puzzle.rating})")
        print(f"Themes: {' '.join(puzzle.themes)}")
        print(f"Position: {puzzle.fen}")
        print(f"Expected move: {puzzle.moves[0]}")
        
        try:
            # Start engine
            engine = subprocess.Popen(
                self.engine_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            start_time = time.time()
            
            # Send UCI commands
            commands = [
                "uci",
                "isready",
                f"position fen {puzzle.fen}",
                f"go movetime {int(time_limit * 1000)}"  # Convert to milliseconds
            ]
            
            for cmd in commands:
                if engine.stdin:
                    engine.stdin.write(f"{cmd}\n")
                    engine.stdin.flush()
                if cmd == "uci":
                    time.sleep(0.5)  # Wait for UCI response
            
            # Read output until we get bestmove
            engine_move = None
            output_lines = []
            
            while True:
                if not engine.stdout:
                    break
                line = engine.stdout.readline()
                if not line:
                    break
                line = line.strip()
                output_lines.append(line)
                
                if line.startswith("bestmove"):
                    engine_move = line.split()[1] if len(line.split()) > 1 else "0000"
                    break
                    
                # Timeout check
                if time.time() - start_time > time_limit + 2:
                    break
            
            # Clean up
            if engine.stdin:
                engine.stdin.write("quit\n")
                engine.stdin.flush()
            engine.wait(timeout=2)
            
            elapsed = time.time() - start_time
            
            # Check if solved
            solved = engine_move == puzzle.moves[0]
            
            result = PuzzleResult(
                puzzle_id=puzzle.puzzle_id,
                solved=solved,
                engine_move=engine_move or "timeout",
                expected_move=puzzle.moves[0],
                time_taken=elapsed,
                search_depth=0,  # TODO: extract from engine output
                themes=puzzle.themes,
                rating=puzzle.rating,
                notes=f"Output lines: {len(output_lines)}"
            )
            
            print(f"Result: {'✅ SOLVED' if solved else '❌ FAILED'}")
            print(f"Engine move: {engine_move}")
            print(f"Time: {elapsed:.2f}s")
            print("-" * 50)
            
            return result
            
        except Exception as e:
            return PuzzleResult(
                puzzle_id=puzzle.puzzle_id,
                solved=False,
                engine_move="error",
                expected_move=puzzle.moves[0],
                time_taken=0,
                search_depth=0,
                themes=puzzle.themes,
                rating=puzzle.rating,
                notes=f"Error: {str(e)}"
            )
    
    def run_test_session(self, count: int = 10, **kwargs):
        """Run a test session on random puzzles."""
        print(f"🧩 Starting puzzle test session ({count} puzzles)")
        print("=" * 60)
        
        puzzles = self.get_random_puzzles(count, **kwargs)
        print(f"Selected {len(puzzles)} puzzles for testing")
        
        session_results = []
        solved_count = 0
        
        for i, puzzle in enumerate(puzzles, 1):
            print(f"\\n[{i}/{len(puzzles)}] ", end="")
            result = self.test_puzzle(puzzle)
            session_results.append(result)
            self.results.append(result)
            
            if result.solved:
                solved_count += 1
                self.solved_puzzles.add(puzzle.puzzle_id)
        
        # Save progress
        self._save_solved_puzzles()
        self._save_results()
        
        # Print session summary
        print(f"\\n🎯 Session Summary:")
        print(f"Puzzles solved: {solved_count}/{len(puzzles)} ({solved_count/len(puzzles)*100:.1f}%)")
        
        # Theme analysis
        theme_stats = {}
        for result in session_results:
            for theme in result.themes:
                if theme not in theme_stats:
                    theme_stats[theme] = {'total': 0, 'solved': 0}
                theme_stats[theme]['total'] += 1
                if result.solved:
                    theme_stats[theme]['solved'] += 1
        
        print("\\n📊 Theme Performance:")
        for theme, stats in sorted(theme_stats.items()):
            if stats['total'] >= 2:  # Only show themes with 2+ puzzles
                rate = stats['solved'] / stats['total'] * 100
                print(f"  {theme}: {stats['solved']}/{stats['total']} ({rate:.1f}%)")
    
    def reset_solved_puzzles(self):
        """Reset the solved puzzles tracker."""
        self.solved_puzzles.clear()
        if os.path.exists(self.solved_puzzles_file):
            os.remove(self.solved_puzzles_file)
        print("✅ Solved puzzles tracker reset")

def main():
    """Main test runner."""
    # Configuration
    engine_path = "../dist/Cece_v1.0.exe"
    csv_path = "lichess_db_puzzle.csv"
    
    if not os.path.exists(engine_path):
        print(f"❌ Engine not found: {engine_path}")
        return
    
    if not os.path.exists(csv_path):
        print(f"❌ Puzzle CSV not found: {csv_path}")
        return
    
    tester = PuzzleTester(engine_path, csv_path)
    
    # Run test session
    tester.run_test_session(
        count=5,  # Start with 5 puzzles
        rating_min=1200,
        rating_max=1600,
        themes_filter=["advantage", "mate"]  # Focus on basic themes
    )

if __name__ == "__main__":
    main()
