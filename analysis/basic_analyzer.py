#!/usr/bin/env python3
"""
Basic move analyzer for testing
"""
import chess.pgn
import json
import os
from pathlib import Path

def analyze_games(pgn_path, results_dir):
    """Analyze chess games and save basic statistics."""
    pgn_path = Path(pgn_path)
    results_dir = Path(results_dir)
    player_name = "v7p3r"
    
    # Initialize counters
    move_counts = {}  # {"e2e4": count, ...}
    piece_squares = {}  # {"P": {"e4": count, ...}, ...}
    game_results = {"wins": 0, "losses": 0, "draws": 0}
    
    print(f"Starting analysis of {pgn_path}...")
    
    with open(pgn_path, encoding='utf-8') as pgn:
        game_count = 0
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            
            # Check if this is a game by our target player
            if (game.headers.get("White") == player_name or 
                game.headers.get("Black") == player_name):
                
                # Process game
                board = game.board()
                is_white = game.headers.get("White") == player_name
                result = game.headers.get("Result", "*")
                
                print(f"Analyzing {game.headers.get('White')} vs {game.headers.get('Black')} [{result}]")
                
                # Update game results
                if result == "1-0" and is_white or result == "0-1" and not is_white:
                    game_results["wins"] += 1
                elif result == "1/2-1/2":
                    game_results["draws"] += 1
                elif result != "*":  # Don't count unfinished games as losses
                    game_results["losses"] += 1
                
                # Process moves
                for node in game.mainline():
                    # Only analyze player's moves
                    if (board.turn == chess.WHITE) != is_white:
                        board.push(node.move)
                        continue
                    
                    move = node.move
                    uci_move = move.uci()
                    piece = board.piece_at(move.from_square)
                    
                    if piece:
                        # Update move counts
                        move_counts[uci_move] = move_counts.get(uci_move, 0) + 1
                        
                        # Update piece square preferences
                        piece_type = piece.symbol()
                        if piece_type not in piece_squares:
                            piece_squares[piece_type] = {}
                        
                        to_square = chess.square_name(move.to_square)
                        piece_squares[piece_type][to_square] = piece_squares[piece_type].get(to_square, 0) + 1
                    
                    board.push(move)
                
                game_count += 1
                if game_count % 10 == 0:
                    print(f"Analyzed {game_count} games...")
    
    print(f"Analysis complete. Found {game_count} games.")
    
    # Create results directory
    os.makedirs(results_dir, exist_ok=True)
    
    # Save results
    with open(results_dir / "move_counts.json", 'w') as f:
        json.dump(move_counts, f, indent=2)
    
    with open(results_dir / "piece_squares.json", 'w') as f:
        json.dump(piece_squares, f, indent=2)
    
    with open(results_dir / "game_results.json", 'w') as f:
        json.dump(game_results, f, indent=2)
    
    # Print summary
    print("\nAnalysis Summary:")
    print(f"Total Games: {game_count}")
    print(f"Wins: {game_results['wins']}")
    print(f"Draws: {game_results['draws']}")
    print(f"Losses: {game_results['losses']}")
    print(f"\nTotal Unique Moves: {len(move_counts)}")
    print("\nMost Common Moves:")
    sorted_moves = sorted(move_counts.items(), key=lambda x: x[1], reverse=True)
    for move, count in sorted_moves[:10]:
        print(f"{move}: {count} times")
    
    print("\nFavorite Squares by Piece:")
    for piece, squares in piece_squares.items():
        if squares:
            favorite_square = max(squares.items(), key=lambda x: x[1])
            print(f"{piece}: {favorite_square[0]} ({favorite_square[1]} times)")

def main():
    base_dir = Path("s:/Maker Stuff/Programming/Chess Engines/Copycat Chess AI/copycat_chess_engine")
    analyze_games(
        base_dir / "training_positions" / "games.pgn",
        base_dir / "results"
    )

if __name__ == "__main__":
    main()
