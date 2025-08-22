"""
Puzzle solver module for Puzzle Challenger.
Handles the logic for solving puzzles and evaluating engine performance.
"""

import chess
import time
from src.engine import UCIEngine
from src.database import PuzzleDatabase

class PuzzleSolver:
    """Class to handle puzzle solving and evaluation."""
    
    def __init__(self, engine_path):
        """Initialize with the path to the chess engine."""
        self.engine = UCIEngine(engine_path)
        self.engine.start()
        self.results = {
            'total': 0,
            'solved': 0,
            'failed': 0,
            'time_taken': 0,
            'by_theme': {},
            'by_rating': {}
        }
    
    def solve_puzzle(self, puzzle, think_time_ms=1000, verbose=True):
        """
        Attempt to solve a puzzle with the engine.
        
        Args:
            puzzle: A Puzzle object from the database
            think_time_ms: Time for the engine to think per move in milliseconds
            verbose: Whether to print detailed output
            
        Returns:
            True if the puzzle was solved correctly, False otherwise
        """
        # Create a chess board with the puzzle position
        board = chess.Board(puzzle.fen)
        
        # Parse the moves string
        moves = puzzle.moves.split()
        expected_moves = []
        
        # Convert the moves to chess.Move objects
        for i in range(0, len(moves), 2):
            if i+1 < len(moves):
                # We need both the opponent's move and our expected response
                opponent_move = chess.Move.from_uci(moves[i])
                expected_move = chess.Move.from_uci(moves[i+1])
                expected_moves.append((opponent_move, expected_move))
        
        if verbose:
            print(f"\nSolving puzzle {puzzle.id} (Rating: {puzzle.rating})")
            print(f"Themes: {puzzle.themes}")
            print(f"Position: {puzzle.fen}")
            print(f"Expected moves: {puzzle.moves}")
            print(board)
        
        # Start timing
        start_time = time.time()
        solved = True
        
        # Play through the puzzle
        for opponent_move, expected_move in expected_moves:
            # Apply the opponent's move
            board.push(opponent_move)
            
            if verbose:
                print(f"\nOpponent plays: {opponent_move.uci()}")
                print(board)
            
            # Get the engine's move
            engine_move_uci = self.engine.get_best_move(board, think_time_ms)
            engine_move = chess.Move.from_uci(engine_move_uci)
            
            if verbose:
                print(f"Engine plays: {engine_move_uci}")
                print(f"Expected: {expected_move.uci()}")
            
            # Check if the engine found the correct move
            if engine_move != expected_move:
                solved = False
                if verbose:
                    print("❌ Incorrect move!")
                break
            else:
                if verbose:
                    print("✓ Correct move!")
            
            # Apply the engine's move to the board
            board.push(engine_move)
        
        # Record the result
        end_time = time.time()
        time_taken = end_time - start_time
        
        self.results['total'] += 1
        if solved:
            self.results['solved'] += 1
        else:
            self.results['failed'] += 1
        
        self.results['time_taken'] += time_taken
        
        # Record by theme
        themes = puzzle.themes.split()
        for theme in themes:
            if theme not in self.results['by_theme']:
                self.results['by_theme'][theme] = {'total': 0, 'solved': 0}
            
            self.results['by_theme'][theme]['total'] += 1
            if solved:
                self.results['by_theme'][theme]['solved'] += 1
        
        # Record by rating range
        rating_range = f"{(puzzle.rating // 200) * 200}-{(puzzle.rating // 200 + 1) * 200}"
        if rating_range not in self.results['by_rating']:
            self.results['by_rating'][rating_range] = {'total': 0, 'solved': 0}
        
        self.results['by_rating'][rating_range]['total'] += 1
        if solved:
            self.results['by_rating'][rating_range]['solved'] += 1
        
        if verbose:
            print(f"\nPuzzle {'solved' if solved else 'failed'} in {time_taken:.2f} seconds")
        
        return solved
    
    def solve_multiple_puzzles(self, puzzles, think_time_ms=1000, verbose=True):
        """
        Solve multiple puzzles and track performance.
        
        Args:
            puzzles: List of Puzzle objects
            think_time_ms: Time for the engine to think per move in milliseconds
            verbose: Whether to print detailed output
            
        Returns:
            Results dictionary with performance statistics
        """
        for i, puzzle in enumerate(puzzles):
            if verbose:
                print(f"\n[{i+1}/{len(puzzles)}] ", end="")
            
            self.solve_puzzle(puzzle, think_time_ms, verbose)
        
        return self.results
    
    def get_performance_report(self):
        """Generate a performance report from the results."""
        total = self.results['total']
        solved = self.results['solved']
        success_rate = (solved / total * 100) if total > 0 else 0
        
        report = [
            f"Performance Report",
            f"=================",
            f"Total puzzles: {total}",
            f"Solved: {solved} ({success_rate:.1f}%)",
            f"Failed: {self.results['failed']}",
            f"Total time: {self.results['time_taken']:.2f} seconds",
            f"Average time per puzzle: {(self.results['time_taken'] / total):.2f} seconds" if total > 0 else "",
            f"\nPerformance by Theme:",
            f"--------------------"
        ]
        
        # Sort themes by success rate
        sorted_themes = sorted(
            self.results['by_theme'].items(),
            key=lambda x: (x[1]['solved'] / x[1]['total']) if x[1]['total'] > 0 else 0,
            reverse=True
        )
        
        for theme, stats in sorted_themes:
            theme_success = (stats['solved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report.append(f"{theme}: {stats['solved']}/{stats['total']} ({theme_success:.1f}%)")
        
        report.extend([
            f"\nPerformance by Rating Range:",
            f"--------------------------"
        ])
        
        # Sort rating ranges
        sorted_ratings = sorted(
            self.results['by_rating'].items(),
            key=lambda x: int(x[0].split('-')[0])
        )
        
        for rating_range, stats in sorted_ratings:
            rating_success = (stats['solved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report.append(f"{rating_range}: {stats['solved']}/{stats['total']} ({rating_success:.1f}%)")
        
        return "\n".join(report)
    
    def close(self):
        """Clean up resources."""
        if self.engine:
            self.engine.stop()
