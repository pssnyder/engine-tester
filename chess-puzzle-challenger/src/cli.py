"""
Command line interface for Puzzle Challenger.
"""

import click
import os
import chess
import random
import time
import json
from src.database import PuzzleDatabase
from src.solver import PuzzleSolver
from src.visualization import create_performance_charts, save_results_to_json

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Puzzle Challenger - A platform for testing chess engine implementations by solving puzzles."""
    pass

@cli.command()
@click.option('-f', '--file', 'csv_file', required=True, type=click.Path(exists=True),
              help='Path to the Lichess puzzle CSV file.')
@click.option('-d', '--db', 'db_file', default='puzzles.db', show_default=True,
              help='Path to the output database file.')
def import_puzzles(csv_file, db_file):
    """Import puzzles from a CSV file into the database."""
    db = PuzzleDatabase(db_file)
    db.import_from_csv(csv_file)
    click.echo(f"Puzzles successfully imported to {db_file}")

@cli.command()
@click.option('-e', '--engine', required=True, type=click.Path(exists=True),
              help='Path to the UCI chess engine executable.')
@click.option('-p', '--puzzle', 'puzzle_ids', multiple=True,
              help='Specific puzzle ID(s) to solve. Can be used multiple times.')
@click.option('-t', '--themes', multiple=True,
              help='Themes to filter puzzles by. Can be used multiple times.')
@click.option('-d', '--difficulty', 'elo', type=int, default=0,
              help='Maximum puzzle difficulty (ELO rating, 0 = any).')
@click.option('-l', '--limit', 'moves_limit', type=int, default=0,
              help='Maximum number of moves in the puzzle (0 = any).')
@click.option('-q', '--quantity', type=int, default=10,
              help='Number of puzzles to solve.')
@click.option('-s', '--strictness', is_flag=True, 
              help='Use strict theme matching (all themes must match).')
@click.option('--db', default='puzzles.db', show_default=True,
              help='Path to the puzzle database file.')
@click.option('--time', type=int, default=1000, show_default=True,
              help='Time allowed for engine to think per move (in milliseconds).')
@click.option('--verbose/--quiet', default=True,
              help='Show detailed output for each puzzle.')
@click.option('--save-results', type=click.Path(),
              help='Save results to a JSON file at the specified path.')
@click.option('--visualize', is_flag=True,
              help='Generate visualization charts for the results.')
@click.option('--output-dir', default='reports',
              help='Directory to save visualization charts and reports.')
def solve(engine, puzzle_ids, themes, elo, moves_limit, quantity,
         strictness, db, time, verbose, save_results, visualize, output_dir):
    """Solve puzzles using a chess engine."""
    # Check if the database exists
    if not os.path.exists(db):
        click.echo(f"Error: Database file {db} not found. Run import-puzzles first.")
        return
    
    # Initialize the puzzle database
    puzzle_db = PuzzleDatabase(db)
    
    # Initialize the puzzle solver with the specified engine
    solver = PuzzleSolver(engine)
    
    try:
        # Get puzzles
        puzzles = []
        
        if puzzle_ids:
            # Get specific puzzles by ID
            for puzzle_id in puzzle_ids:
                puzzle = puzzle_db.get_puzzle_by_id(puzzle_id)
                if puzzle:
                    puzzles.append(puzzle)
                else:
                    click.echo(f"Warning: Puzzle {puzzle_id} not found")
        else:
            # Get puzzles by criteria
            puzzles = puzzle_db.query_puzzles(
                themes=themes,
                min_rating=0,
                max_rating=elo if elo > 0 else 3500,
                limit_moves=moves_limit,
                quantity=quantity,
                strict_themes=strictness
            )
        
        if not puzzles:
            click.echo("No puzzles found matching the criteria.")
            return
        
        click.echo(f"Solving {len(puzzles)} puzzles...")
        
        # Solve the puzzles
        results = solver.solve_multiple_puzzles(puzzles, time, verbose)
        
        # Print performance report
        click.echo("\n" + solver.get_performance_report())
        
        # Save results to JSON if requested
        if save_results:
            save_results_to_json(results, save_results)
        
        # Generate visualizations if requested
        if visualize:
            os.makedirs(output_dir, exist_ok=True)
            create_performance_charts(results, output_dir)
            click.echo(f"Visualization charts and reports saved to {output_dir}")
        
    finally:
        # Clean up
        solver.close()

@cli.command()
@click.option('--db', default='puzzles.db', show_default=True,
              help='Path to the puzzle database file.')
@click.option('-t', '--themes', is_flag=True,
              help='List all available themes in the database.')
def info(db, themes):
    """Display information about the puzzle database."""
    # Check if the database exists
    if not os.path.exists(db):
        click.echo(f"Error: Database file {db} not found. Run import-puzzles first.")
        return
    
    # Initialize the puzzle database
    puzzle_db = PuzzleDatabase(db)
    
    # Connect directly to get statistics
    conn = puzzle_db.engine.connect()
    
    # Get total number of puzzles
    result = conn.execute("SELECT COUNT(*) FROM puzzles")
    total_puzzles = result.fetchone()[0]
    click.echo(f"Total puzzles: {total_puzzles}")
    
    # Get rating distribution
    result = conn.execute("""
        SELECT 
            (rating / 200) * 200 as range_start,
            ((rating / 200) + 1) * 200 as range_end,
            COUNT(*) as count
        FROM puzzles
        GROUP BY range_start
        ORDER BY range_start
    """)
    
    click.echo("\nRating Distribution:")
    for row in result:
        click.echo(f"{row[0]}-{row[1]}: {row[2]} puzzles")
    
    # List themes if requested
    if themes:
        click.echo("\nAvailable Themes:")
        
        # This query will be slow on a large database
        # In a real implementation, we would need a separate themes table
        result = conn.execute("""
            SELECT DISTINCT themes FROM puzzles
        """)
        
        all_themes = set()
        for row in result:
            themes_str = row[0]
            if themes_str:
                theme_list = themes_str.split()
                all_themes.update(theme_list)
        
        for theme in sorted(all_themes):
            click.echo(theme)

@cli.command()
@click.option('-f', '--fen', required=True,
              help='FEN string representing the position.')
@click.option('-e', '--engine', required=True, type=click.Path(exists=True),
              help='Path to the UCI chess engine executable.')
@click.option('-m', '--moves', multiple=True, required=True,
              help='Expected sequence of moves in UCI format (e.g., e2e4). Can use multiple times for multiple moves.')
@click.option('-t', '--themes', multiple=True,
              help='Themes to tag the puzzle with. Can be used multiple times.')
@click.option('-r', '--rating', type=int, default=1500,
              help='Initial rating for the puzzle.')
@click.option('--db', default='puzzles.db', show_default=True,
              help='Path to the puzzle database file.')
def create(fen, engine, moves, themes, rating, db):
    """Create a new puzzle and add it to the database."""
    # Check if the database exists
    if not os.path.exists(db):
        click.echo(f"Error: Database file {db} not found. Run import-puzzles first.")
        return
    
    # Validate FEN
    try:
        board = chess.Board(fen)
    except ValueError as e:
        click.echo(f"Error: Invalid FEN string - {e}")
        return
    
    # Validate moves
    try:
        test_board = chess.Board(fen)
        for move_uci in moves:
            move = chess.Move.from_uci(move_uci)
            if move not in test_board.legal_moves:
                click.echo(f"Error: Illegal move {move_uci} in position {test_board.fen()}")
                return
            test_board.push(move)
    except ValueError as e:
        click.echo(f"Error: Invalid move format - {e}")
        return
    
    # Generate a unique ID for the puzzle
    puzzle_id = f"custom_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Initialize the puzzle database
    puzzle_db = PuzzleDatabase(db)
    
    # Test the puzzle with the engine
    solver = PuzzleSolver(engine)
    
    try:
        # Create a temporary puzzle object
        from src.database import Puzzle
        temp_puzzle = Puzzle(
            id=puzzle_id,
            fen=fen,
            moves=' '.join(moves),
            rating=rating,
            themes=' '.join(themes)
        )
        
        # Try to solve the puzzle with the engine
        click.echo("Testing the puzzle with the specified engine...")
        solved = solver.solve_puzzle(temp_puzzle)
        
        if solved:
            click.echo("Warning: The engine solved this puzzle correctly on the first try.")
            click.echo("This might be too easy or the engine already knows the solution.")
            
            if not click.confirm("Do you still want to add this puzzle to the database?"):
                return
        
        # Add the puzzle to the database
        session = puzzle_db.Session()
        session.add(temp_puzzle)
        session.commit()
        
        click.echo(f"Puzzle {puzzle_id} added to the database.")
        
    finally:
        solver.close()

def main():
    """Main entry point for the CLI."""
    cli()
