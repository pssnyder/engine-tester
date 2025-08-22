"""
Comprehensive test script for Puzzle Challenger.
Tests the system with a collection of puzzles using Stockfish engine.
"""

import os
import sys
import time
import random
import argparse

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import PuzzleDatabase
from src.solver import PuzzleSolver
from src.visualization import create_performance_charts, save_results_to_json

def run_comprehensive_test(stockfish_path, db_path, output_dir, sample_size=100, themes=None):
    """
    Run a comprehensive test with Stockfish on a sample of puzzles.
    
    Args:
        stockfish_path: Path to the stockfish executable
        db_path: Path to the puzzle database
        output_dir: Directory to save reports and visualizations
        sample_size: Number of puzzles to sample
        themes: List of themes to include (if None, all themes are considered)
    """
    print(f"Starting comprehensive test with Stockfish on {sample_size} puzzles")
    
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize database
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        print("Please run 'python -m src.main import-puzzles --file lichess_db_puzzle.csv' first.")
        return
    
    db = PuzzleDatabase(db_path)
    
    # Get available themes if none specified
    if not themes:
        # This is a simplified way to get themes - in a real implementation we'd use a dedicated query
        conn = db.engine.connect()
        from sqlalchemy.sql import text
        result = conn.execute(text("SELECT DISTINCT themes FROM puzzles LIMIT 1000"))
        all_themes = set()
        for row in result:
            themes_str = row[0]
            if themes_str:
                theme_list = themes_str.split()
                all_themes.update(theme_list)
        
        # Sample some common themes
        common_themes = ['mate', 'fork', 'pin', 'sacrifice', 'discovery', 'hanging', 'skewer',
                         'opening', 'middlegame', 'endgame', 'advantage', 'equality', 'crushing']
        themes = [theme for theme in common_themes if theme in all_themes]
        
        if not themes:
            # If none of the common themes were found, use whatever themes we found
            themes = list(all_themes)[:10]  # Use up to 10 themes
    
    print(f"Testing with themes: {', '.join(themes)}")
    
    # Initialize the solver with Stockfish
    solver = PuzzleSolver(stockfish_path)
    
    try:
        # Get puzzles for each theme
        puzzles_per_theme = max(1, sample_size // len(themes))
        all_puzzles = []
        
        for theme in themes:
            print(f"Fetching puzzles with theme: {theme}")
            puzzles = db.query_puzzles(
                themes=[theme],
                quantity=puzzles_per_theme,
                strict_themes=True
            )
            print(f"Found {len(puzzles)} puzzles with theme '{theme}'")
            all_puzzles.extend(puzzles)
        
        # If we don't have enough puzzles, get some random ones
        if len(all_puzzles) < sample_size:
            additional_puzzles = db.query_puzzles(
                quantity=sample_size - len(all_puzzles)
            )
            all_puzzles.extend(additional_puzzles)
        
        # Limit to sample size and shuffle
        if len(all_puzzles) > sample_size:
            all_puzzles = random.sample(all_puzzles, sample_size)
        else:
            random.shuffle(all_puzzles)
        
        print(f"\nSolving {len(all_puzzles)} puzzles with Stockfish...")
        start_time = time.time()
        
        # Solve the puzzles
        results = solver.solve_multiple_puzzles(all_puzzles, think_time_ms=1000, verbose=True)
        
        end_time = time.time()
        print(f"\nTest completed in {end_time - start_time:.2f} seconds")
        
        # Print performance report
        print("\n" + solver.get_performance_report())
        
        # Save results to JSON
        results_file = os.path.join(output_dir, "stockfish_results.json")
        save_results_to_json(results, results_file)
        
        # Generate visualizations
        create_performance_charts(results, output_dir)
        
        print(f"\nTest results, charts, and reports saved to {output_dir}")
        
    finally:
        solver.close()

def main():
    parser = argparse.ArgumentParser(description="Run a comprehensive test of Puzzle Challenger with Stockfish")
    parser.add_argument("--stockfish", type=str, default="src/stockfish.exe",
                        help="Path to Stockfish executable (default: src/stockfish.exe)")
    parser.add_argument("--db", type=str, default="puzzles.db",
                        help="Path to puzzle database (default: puzzles.db)")
    parser.add_argument("--output", type=str, default="reports",
                        help="Directory to save reports and visualizations (default: reports)")
    parser.add_argument("--sample-size", type=int, default=100,
                        help="Number of puzzles to sample (default: 100)")
    parser.add_argument("--themes", type=str, nargs="+",
                        help="Specific themes to test (optional)")
    
    args = parser.parse_args()
    
    run_comprehensive_test(
        args.stockfish,
        args.db,
        args.output,
        args.sample_size,
        args.themes
    )

if __name__ == "__main__":
    main()
