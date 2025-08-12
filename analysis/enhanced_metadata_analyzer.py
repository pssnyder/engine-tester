#!/usr/bin/env python3
"""
Enhanced Chess Game Metadata Analyzer
This module provides advanced analysis of chess games with focus on:
- Game outcome decisiveness metrics
- Opening recognition and weighting
- Time control-aware move timing analysis
- Enhanced piece movement statistics
- Relationship mapping between metrics
"""

import os
import json
import chess
import chess.pgn
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional, Any, Union
import io
import re
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Define constants
DECISIVENESS_WEIGHTS = {
    "checkmate": 1.0,        # Highest weight for decisive checkmates
    "resignation": 0.8,      # High weight for resignations
    "draw": 0.5,             # Medium weight for agreed draws
    "stalemate": 0.4,        # Lower medium weight for stalemates
    "timeout": 0.3,          # Low weight for timeout games
    "abandoned": 0.1         # Lowest weight for abandoned games
}

# Time controls categorization
TIME_CONTROLS = {
    "bullet": (0, 3),        # 0-3 minutes
    "blitz": (3, 10),        # 3-10 minutes
    "rapid": (10, 30),       # 10-30 minutes
    "classical": (30, float('inf'))  # 30+ minutes
}

# Focus openings with higher weights
FOCUS_OPENINGS = {
    "London": 1.5,
    "Vienna": 1.5,
    "Caro-Kann": 1.5,
    "Scandinavian": 1.5,
    "Other": 1.0
}

@dataclass
class GameMetadata:
    """Stores metadata about a chess game"""
    white_player: str = ""
    black_player: str = ""
    result: str = ""
    time_control: str = ""
    opening: str = ""
    eco_code: str = ""
    termination: str = ""  # How the game ended
    decisive_score: float = 0.0  # Decisiveness score
    total_moves: int = 0
    material_imbalance: int = 0  # Final material difference
    time_per_move: Dict[int, float] = field(default_factory=dict)  # Move number to time spent
    phase_transitions: Dict[str, int] = field(default_factory=dict)  # Phase to move number
    move_quality: Dict[int, float] = field(default_factory=dict)  # Move number to quality score

@dataclass
class PieceStatistics:
    """Statistics about piece movements"""
    total_moves: int = 0
    attack_moves: int = 0
    defense_moves: int = 0
    capture_moves: int = 0
    check_moves: int = 0
    squares_visited: Set[str] = field(default_factory=set)
    survival_time: int = 0  # Number of moves piece stayed on board
    phase_distribution: Dict[str, int] = field(default_factory=lambda: {"opening": 0, "middlegame": 0, "endgame": 0})

class EnhancedMetadataAnalyzer:
    def __init__(self, pgn_folder="training_positions", results_dir="results"):
        """Initialize the analyzer with paths to PGN files and results directory"""
        self.pgn_folder = pgn_folder
        self.results_dir = results_dir
        self.player_name = "v7p3r"  # Default player to analyze
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Data structures to store analysis results
        self.games_metadata: List[GameMetadata] = []
        self.piece_stats: Dict[str, Dict[str, PieceStatistics]] = defaultdict(lambda: defaultdict(PieceStatistics))
        self.move_weights: Dict[str, float] = {}  # Store calculated weights for moves
        self.opening_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(int))
        
        # Relationship data
        self.metric_correlations = {}
        
    def identify_termination_type(self, game) -> Tuple[str, float]:
        """
        Identify how a game ended and assign a decisiveness score.
        
        Returns:
            tuple: (termination_type, decisiveness_score)
        """
        headers = game.headers
        result = headers.get("Result", "*")
        termination = headers.get("Termination", "").lower()
        
        # Check for checkmate
        if "mate" in termination or "checkmate" in termination:
            return "checkmate", DECISIVENESS_WEIGHTS["checkmate"]
        
        # Check for resignation
        elif "resigns" in termination or "resignation" in termination:
            return "resignation", DECISIVENESS_WEIGHTS["resignation"]
        
        # Check for stalemate
        elif "stalemate" in termination:
            return "stalemate", DECISIVENESS_WEIGHTS["stalemate"]
        
        # Check for draw
        elif result == "1/2-1/2" or "draw" in termination:
            return "draw", DECISIVENESS_WEIGHTS["draw"]
        
        # Check for timeout
        elif "time" in termination or "timeout" in termination or "forfeit" in termination:
            return "timeout", DECISIVENESS_WEIGHTS["timeout"]
        
        # Default to abandoned
        else:
            return "abandoned", DECISIVENESS_WEIGHTS["abandoned"]
    
    def categorize_time_control(self, time_control_str: str) -> str:
        """
        Categorize the time control into bullet, blitz, rapid, or classical.
        
        Args:
            time_control_str: String with time control info (e.g., "5+3", "15+10")
            
        Returns:
            str: Category of time control
        """
        # Default to classical if we can't parse
        if not time_control_str:
            return "classical"
        
        # Try to extract base time in minutes
        try:
            # Handle formats like "5+3", "15+10"
            match = re.match(r'(\d+)(?:\+\d+)?', time_control_str)
            if match:
                base_minutes = int(match.group(1))
                
                for category, (min_time, max_time) in TIME_CONTROLS.items():
                    if min_time <= base_minutes < max_time:
                        return category
                
                return "classical"  # Default if no match
            else:
                return "classical"
        except:
            return "classical"  # Default on error
    
    def identify_opening(self, game) -> Tuple[str, str]:
        """
        Identify the opening played in the game.
        
        Returns:
            tuple: (opening_name, eco_code)
        """
        headers = game.headers
        opening = headers.get("Opening", "Unknown")
        eco = headers.get("ECO", "")
        
        # Check if it's one of our focus openings
        for focus_opening in FOCUS_OPENINGS:
            if focus_opening.lower() in opening.lower():
                return opening, eco
        
        return opening, eco
    
    def calculate_material_imbalance(self, board) -> int:
        """
        Calculate material imbalance at the end of the game.
        Positive means white has more material, negative means black has more.
        
        Returns:
            int: Material difference in centipawns
        """
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0  # King isn't counted for material
        }
        
        white_material = sum(
            piece_values[piece_type] * len(board.pieces(piece_type, chess.WHITE))
            for piece_type in piece_values
        )
        
        black_material = sum(
            piece_values[piece_type] * len(board.pieces(piece_type, chess.BLACK))
            for piece_type in piece_values
        )
        
        return white_material - black_material
    
    def detect_game_phase(self, board) -> str:
        """
        Detect the phase of the game based on the position.
        
        Returns:
            str: "opening", "middlegame", or "endgame"
        """
        # Count pieces on the board
        piece_count = 0
        queen_count = 0
        
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            piece_count += len(board.pieces(piece_type, chess.WHITE))
            piece_count += len(board.pieces(piece_type, chess.BLACK))
            
            if piece_type == chess.QUEEN:
                queen_count += len(board.pieces(piece_type, chess.WHITE))
                queen_count += len(board.pieces(piece_type, chess.BLACK))
        
        # Check castling rights
        castling_rights = any([
            board.has_kingside_castling_rights(chess.WHITE),
            board.has_queenside_castling_rights(chess.WHITE),
            board.has_kingside_castling_rights(chess.BLACK),
            board.has_queenside_castling_rights(chess.BLACK)
        ])
        
        # Opening: >= 14 pieces, castling rights available, less than 15 full moves
        if piece_count >= 14 and castling_rights and board.fullmove_number <= 15:
            return "opening"
        
        # Endgame: <= 10 pieces or no queens
        elif piece_count <= 10 or queen_count == 0:
            return "endgame"
        
        # Otherwise it's middlegame
        else:
            return "middlegame"
    
    def track_piece_movements(self, board, move, move_number, phase, color_to_move):
        """
        Track piece movements and update statistics.
        """
        piece = board.piece_at(move.from_square)
        if piece is None:
            return  # Skip if no piece (shouldn't happen with valid moves)
        
        piece_symbol = piece.symbol()
        piece_key = f"{chess.COLOR_NAMES[piece.color]} {chess.piece_name(piece.piece_type)}"
        
        # Update total moves for this piece type
        self.piece_stats[piece_key][piece_symbol].total_moves += 1
        
        # Track the square this piece moved to
        to_square = chess.square_name(move.to_square)
        self.piece_stats[piece_key][piece_symbol].squares_visited.add(to_square)
        
        # Track phase distribution
        self.piece_stats[piece_key][piece_symbol].phase_distribution[phase] += 1
        
        # Check if it's a capture move
        if board.is_capture(move):
            self.piece_stats[piece_key][piece_symbol].capture_moves += 1
        
        # Check if it gives check
        board.push(move)
        if board.is_check():
            self.piece_stats[piece_key][piece_symbol].check_moves += 1
        board.pop()
        
        # Attempt to classify as attack or defense (simplified heuristic)
        if piece.color == chess.WHITE:
            # For white, moving toward higher ranks is generally attacking
            from_rank = chess.square_rank(move.from_square)
            to_rank = chess.square_rank(move.to_square)
            if to_rank > from_rank:
                self.piece_stats[piece_key][piece_symbol].attack_moves += 1
            else:
                self.piece_stats[piece_key][piece_symbol].defense_moves += 1
        else:
            # For black, moving toward lower ranks is generally attacking
            from_rank = chess.square_rank(move.from_square)
            to_rank = chess.square_rank(move.to_square)
            if to_rank < from_rank:
                self.piece_stats[piece_key][piece_symbol].attack_moves += 1
            else:
                self.piece_stats[piece_key][piece_symbol].defense_moves += 1
    
    def track_piece_survival(self, board, move_number):
        """
        Update the survival time for each piece currently on the board.
        """
        for color in [chess.WHITE, chess.BLACK]:
            color_name = chess.COLOR_NAMES[color]
            for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                piece_name = chess.piece_name(piece_type)
                piece_key = f"{color_name} {piece_name}"
                piece_symbol = chess.Piece(piece_type, color).symbol()
                
                # Count how many of this piece are still on the board
                count = len(board.pieces(piece_type, color))
                
                # Update survival time for each piece still alive
                if count > 0:
                    self.piece_stats[piece_key][piece_symbol].survival_time += count
    
    def analyze_pgn_file(self, pgn_path):
        """
        Analyze a single PGN file and extract metadata.
        
        Args:
            pgn_path: Path to the PGN file
        """
        try:
            with open(pgn_path, encoding='utf-8') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    
                    # Extract basic metadata
                    metadata = GameMetadata()
                    metadata.white_player = game.headers.get("White", "")
                    metadata.black_player = game.headers.get("Black", "")
                    metadata.result = game.headers.get("Result", "*")
                    
                    # Determine if our player of interest is in this game
                    player_is_white = self.player_name.lower() in metadata.white_player.lower()
                    player_is_black = self.player_name.lower() in metadata.black_player.lower()
                    player_side = None
                    
                    if player_is_white:
                        player_side = chess.WHITE
                    elif player_is_black:
                        player_side = chess.BLACK
                    else:
                        # Skip games that don't involve our player
                        continue
                    
                    # Extract time control
                    time_control = game.headers.get("TimeControl", "")
                    metadata.time_control = self.categorize_time_control(time_control)
                    
                    # Determine game termination and decisiveness
                    metadata.termination, metadata.decisive_score = self.identify_termination_type(game)
                    
                    # Identify opening
                    metadata.opening, metadata.eco_code = self.identify_opening(game)
                    
                    # Update opening statistics
                    self.opening_stats[metadata.opening]["games"] += 1
                    if (metadata.result == "1-0" and player_is_white) or (metadata.result == "0-1" and player_is_black):
                        self.opening_stats[metadata.opening]["wins"] += 1
                    elif (metadata.result == "0-1" and player_is_white) or (metadata.result == "1-0" and player_is_black):
                        self.opening_stats[metadata.opening]["losses"] += 1
                    elif metadata.result == "1/2-1/2":
                        self.opening_stats[metadata.opening]["draws"] += 1
                    
                    # Process the moves and collect detailed statistics
                    board = game.board()
                    phase_transitions = {"opening": 1}  # Game starts in opening phase
                    current_phase = "opening"
                    moves_in_phase = {"opening": 0, "middlegame": 0, "endgame": 0}
                    
                    # Process each move
                    move_number = 0
                    node = game
                    
                    while not node.is_end():
                        node = node.variation(0)  # Follow the main line
                        move_number += 1
                        
                        # Detect phase
                        new_phase = self.detect_game_phase(board)
                        if new_phase != current_phase:
                            phase_transitions[new_phase] = move_number
                            current_phase = new_phase
                        
                        moves_in_phase[current_phase] += 1
                        
                        # Track piece movements
                        self.track_piece_movements(
                            board, 
                            node.move, 
                            move_number, 
                            current_phase, 
                            board.turn
                        )
                        
                        # Track piece survival
                        self.track_piece_survival(board, move_number)
                        
                        # Update the board
                        board.push(node.move)
                        
                        # Extract move timing if available
                        if node.comment:
                            # Look for time information in comments like [%clk 0:05:23]
                            time_match = re.search(r'\[%clk\s+(\d+):(\d+):(\d+(?:\.\d+)?)\]', node.comment)
                            if time_match:
                                hours, minutes, seconds = map(float, time_match.groups())
                                time_spent = 3600 * hours + 60 * minutes + seconds
                                
                                # Store time spent on this move
                                metadata.time_per_move[move_number] = time_spent
                    
                    metadata.total_moves = move_number
                    metadata.phase_transitions = phase_transitions
                    metadata.material_imbalance = self.calculate_material_imbalance(board)
                    
                    # Calculate move quality based on time spent and game outcome
                    if player_side is not None:
                        player_won = (metadata.result == "1-0" and player_side == chess.WHITE) or (metadata.result == "0-1" and player_side == chess.BLACK)
                        base_quality = 0.8 if player_won else 0.4
                        
                        # Adjust by decisiveness
                        base_quality *= metadata.decisive_score
                        
                        # Calculate move quality for each move
                        for move_num, time_spent in metadata.time_per_move.items():
                            # Higher quality for appropriate time usage
                            time_factor = 1.0
                            
                            # Penalize very quick moves in complex positions (middlegame)
                            phase = "opening"
                            for p, transition_move in sorted(metadata.phase_transitions.items(), key=lambda x: x[1]):
                                if move_num >= transition_move:
                                    phase = p
                            
                            if phase == "middlegame" and time_spent < 5:
                                time_factor = 0.7 + (time_spent / 5) * 0.3
                            elif phase == "endgame" and time_spent < 3:
                                time_factor = 0.8 + (time_spent / 3) * 0.2
                            
                            # Calculate final move quality
                            metadata.move_quality[move_num] = base_quality * time_factor
                    
                    # Store the game metadata
                    self.games_metadata.append(metadata)
                    
        except Exception as e:
            print(f"Error analyzing {pgn_path}: {str(e)}")
    
    def analyze_all_pgn_files(self):
        """
        Analyze all PGN files in the specified folder.
        """
        pgn_files = [
            os.path.join(self.pgn_folder, f) 
            for f in os.listdir(self.pgn_folder) 
            if f.endswith('.pgn')
        ]
        
        total_files = len(pgn_files)
        print(f"Found {total_files} PGN files to analyze")
        
        for i, pgn_file in enumerate(pgn_files):
            print(f"Analyzing file {i+1}/{total_files}: {os.path.basename(pgn_file)}")
            self.analyze_pgn_file(pgn_file)
        
        print(f"Analyzed {len(self.games_metadata)} games involving player {self.player_name}")
    
    def calculate_move_weights(self):
        """
        Calculate weights for moves based on all the collected metadata.
        """
        # Example weighting logic
        # We could weight moves differently based on phase, outcome, time spent, etc.
        pass
    
    def calculate_correlations(self):
        """
        Calculate correlations between different metrics.
        """
        # Prepare data for correlation analysis
        data = {
            'decisiveness': [game.decisive_score for game in self.games_metadata],
            'total_moves': [game.total_moves for game in self.games_metadata],
            'material_imbalance': [game.material_imbalance for game in self.games_metadata],
        }
        
        # Add average move quality per game
        data['avg_move_quality'] = [
            sum(game.move_quality.values()) / len(game.move_quality) if game.move_quality else 0
            for game in self.games_metadata
        ]
        
        # Add average time per move
        data['avg_time_per_move'] = [
            sum(game.time_per_move.values()) / len(game.time_per_move) if game.time_per_move else 0
            for game in self.games_metadata
        ]
        
        # Create a DataFrame for correlation calculation
        df = pd.DataFrame(data)
        self.metric_correlations = df.corr().to_dict()
    
    def generate_results(self):
        """
        Generate and save the analysis results.
        """
        # Calculate correlations
        self.calculate_correlations()
        
        # Prepare results
        results = {
            'game_decisiveness': {
                term: len([g for g in self.games_metadata if g.termination == term])
                for term in set(g.termination for g in self.games_metadata)
            },
            'time_control_distribution': {
                tc: len([g for g in self.games_metadata if g.time_control == tc])
                for tc in set(g.time_control for g in self.games_metadata)
            },
            'opening_stats': self.opening_stats,
            'phase_transitions': {
                'avg_opening_duration': sum(
                    g.phase_transitions.get('middlegame', g.total_moves) - 1
                    for g in self.games_metadata
                ) / len(self.games_metadata) if self.games_metadata else 0,
                'avg_middlegame_duration': sum(
                    g.phase_transitions.get('endgame', g.total_moves) - 
                    g.phase_transitions.get('middlegame', g.total_moves)
                    for g in self.games_metadata if 'middlegame' in g.phase_transitions
                ) / sum(1 for g in self.games_metadata if 'middlegame' in g.phase_transitions) 
                if sum(1 for g in self.games_metadata if 'middlegame' in g.phase_transitions) > 0 else 0,
            },
            'piece_stats': {
                piece_key: {
                    symbol: {
                        'total_moves': stats.total_moves,
                        'attack_moves': stats.attack_moves,
                        'defense_moves': stats.defense_moves,
                        'capture_moves': stats.capture_moves,
                        'check_moves': stats.check_moves,
                        'squares_visited': len(stats.squares_visited),
                        'avg_survival': stats.survival_time / stats.total_moves if stats.total_moves > 0 else 0,
                        'phase_distribution': stats.phase_distribution
                    }
                    for symbol, stats in piece_stats.items()
                }
                for piece_key, piece_stats in self.piece_stats.items()
            },
            'metric_correlations': self.metric_correlations
        }
        
        # Generate comprehensive player stats
        player_stats = {
            'total_games': len(self.games_metadata),
            'wins': len([g for g in self.games_metadata 
                        if (g.result == "1-0" and g.white_player.lower() == self.player_name.lower()) or 
                           (g.result == "0-1" and g.black_player.lower() == self.player_name.lower())]),
            'losses': len([g for g in self.games_metadata 
                          if (g.result == "0-1" and g.white_player.lower() == self.player_name.lower()) or 
                             (g.result == "1-0" and g.black_player.lower() == self.player_name.lower())]),
            'draws': len([g for g in self.games_metadata if g.result == "1/2-1/2"]),
            'avg_game_length': sum(g.total_moves for g in self.games_metadata) / len(self.games_metadata) if self.games_metadata else 0,
            'favorite_openings': {
                opening: stats['games'] 
                for opening, stats in sorted(
                    self.opening_stats.items(), 
                    key=lambda x: x[1]['games'], 
                    reverse=True
                )[:10]
            },
            'decisiveness_distribution': results['game_decisiveness'],
            'time_control_distribution': results['time_control_distribution'],
            'performance_by_color': {
                'white': {
                    'games': len([g for g in self.games_metadata if g.white_player.lower() == self.player_name.lower()]),
                    'wins': len([g for g in self.games_metadata 
                               if g.white_player.lower() == self.player_name.lower() and g.result == "1-0"]),
                    'losses': len([g for g in self.games_metadata 
                                 if g.white_player.lower() == self.player_name.lower() and g.result == "0-1"]),
                    'draws': len([g for g in self.games_metadata 
                                if g.white_player.lower() == self.player_name.lower() and g.result == "1/2-1/2"])
                },
                'black': {
                    'games': len([g for g in self.games_metadata if g.black_player.lower() == self.player_name.lower()]),
                    'wins': len([g for g in self.games_metadata 
                               if g.black_player.lower() == self.player_name.lower() and g.result == "0-1"]),
                    'losses': len([g for g in self.games_metadata 
                                 if g.black_player.lower() == self.player_name.lower() and g.result == "1-0"]),
                    'draws': len([g for g in self.games_metadata 
                                if g.black_player.lower() == self.player_name.lower() and g.result == "1/2-1/2"])
                }
            }
        }
        
        # Save results
        with open(os.path.join(self.results_dir, 'enhanced_analysis.json'), 'w') as f:
            json.dump(results, f, indent=2)
        
        with open(os.path.join(self.results_dir, 'enhanced_player_stats.json'), 'w') as f:
            json.dump(player_stats, f, indent=2)
        
        print("Enhanced analysis complete. Results saved.")
        return results, player_stats

    def generate_relationship_diagram(self):
        """
        Generate a relationship diagram showing connections between metrics.
        """
        # Create a correlation matrix visualization
        if not self.metric_correlations:
            self.calculate_correlations()
        
        # Convert correlation dict to DataFrame
        corr_df = pd.DataFrame(self.metric_correlations)
        
        # Create the correlation heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_df, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('Correlations Between Chess Metrics')
        plt.tight_layout()
        
        # Save the diagram
        plt.savefig(os.path.join(self.results_dir, 'metric_relationships.png'), dpi=300)
        plt.close()
        
        # Also generate piece relationships chart
        self.generate_piece_relationship_chart()
        
    def generate_piece_relationship_chart(self):
        """
        Generate a chart showing relationships between different piece statistics.
        """
        # Extract piece-related metrics for comparison
        piece_data = {}
        
        for piece_key, piece_stats in self.piece_stats.items():
            for symbol, stats in piece_stats.items():
                if stats.total_moves > 0:  # Only include pieces that moved
                    piece_name = piece_key.split()[-1]  # e.g., "white knight" -> "knight"
                    
                    # Calculate metrics
                    attack_ratio = stats.attack_moves / stats.total_moves if stats.total_moves > 0 else 0
                    capture_ratio = stats.capture_moves / stats.total_moves if stats.total_moves > 0 else 0
                    check_ratio = stats.check_moves / stats.total_moves if stats.total_moves > 0 else 0
                    
                    # Store data
                    if piece_name not in piece_data:
                        piece_data[piece_name] = {
                            'attack_ratio': [],
                            'capture_ratio': [],
                            'check_ratio': [],
                            'squares_visited': []
                        }
                    
                    piece_data[piece_name]['attack_ratio'].append(attack_ratio)
                    piece_data[piece_name]['capture_ratio'].append(capture_ratio)
                    piece_data[piece_name]['check_ratio'].append(check_ratio)
                    piece_data[piece_name]['squares_visited'].append(len(stats.squares_visited))
        
        # Calculate averages for each piece type
        for piece_name, metrics in piece_data.items():
            for metric, values in metrics.items():
                if values:
                    metrics[metric] = sum(values) / len(values)
        
        # Create a multi-metric comparison chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Define metrics to plot
        metrics = ['attack_ratio', 'capture_ratio', 'check_ratio']
        x = np.arange(len(piece_data))
        width = 0.25
        
        # Plot each metric as a grouped bar
        for i, metric in enumerate(metrics):
            values = [piece_data[piece][metric] for piece in piece_data]
            ax.bar(x + i*width - width, values, width, label=metric)
        
        ax.set_xlabel('Piece Type')
        ax.set_ylabel('Ratio')
        ax.set_title('Piece Behavior Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(list(piece_data.keys()))
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.results_dir, 'piece_relationships.png'), dpi=300)
        plt.close()

def main():
    analyzer = EnhancedMetadataAnalyzer()
    analyzer.analyze_all_pgn_files()
    analyzer.generate_results()
    analyzer.generate_relationship_diagram()

if __name__ == "__main__":
    main()
