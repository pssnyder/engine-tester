#!/usr/bin/env python3
"""
Enhanced Chess Game Analyzer
Analyzes PGN games with detailed statistics and patterns.
"""
import warnings
warnings.filterwarnings('ignore')

import chess.pgn
import chess
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field

@dataclass
class TimingStats:
    avg: float = 0.0
    fast_moves: int = 0
    slow_moves: int = 0
    total_time: float = 0.0
    times_list: List[float] = field(default_factory=list)

@dataclass
class PhaseDistribution:
    opening: int = 0
    middlegame: int = 0
    endgame: int = 0

@dataclass
class CaptureStats:
    captures: int = 0
    captured: int = 0

@dataclass
class CheckStats:
    gives_check: int = 0
    after_check: int = 0

@dataclass
class PieceData:
    frequency: int = 0
    timing: TimingStats = field(default_factory=TimingStats)
    phase_distribution: PhaseDistribution = field(default_factory=PhaseDistribution)
    capture_stats: CaptureStats = field(default_factory=CaptureStats)
    check_stats: CheckStats = field(default_factory=CheckStats)

    def to_dict(self) -> Dict:
        return {
            "frequency": self.frequency,
            "timing": {
                "avg": self.timing.avg,
                "fast_moves": self.timing.fast_moves,
                "slow_moves": self.timing.slow_moves,
                "total_time": self.timing.total_time,
                "times_list": self.timing.times_list
            },
            "phase_distribution": vars(self.phase_distribution),
            "capture_stats": vars(self.capture_stats),
            "check_stats": vars(self.check_stats)
        }

class GameAnalyzer:
    def __init__(self, pgn_path: str, results_dir: str):
        """Initialize the analyzer with paths."""
        self.pgn_path = pgn_path
        self.results_dir = results_dir
        self.player_name = "v7p3r"

        # Initialize data collectors
        self.piece_heatmaps: Dict[str, Dict[str, PieceData]] = {}
        self.analyzed_games = 0
        self.total_moves = 0
        self.player_stats = {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "avg_game_length": 0,
            "favorite_openings": defaultdict(int),
            "performance_by_color": {
                "white": {"wins": 0, "losses": 0, "draws": 0},
                "black": {"wins": 0, "losses": 0, "draws": 0}
            }
        }

    def determine_game_phase(self, move_number: int, total_pieces: int) -> str:
        """Determine the current game phase."""
        if move_number <= 10:
            return "opening"
        elif total_pieces >= 20:
            return "middlegame"
        return "endgame"

    def count_pieces(self, board: chess.Board) -> int:
        """Count total pieces on the board."""
        return sum(len(board.pieces(piece_type, color)) 
                  for color in [chess.WHITE, chess.BLACK]
                  for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, 
                                   chess.ROOK, chess.QUEEN, chess.KING])

    def update_piece_data(self, piece_key: str, square_key: str, 
                         phase: str, move_time: Optional[float] = None,
                         is_capture: bool = False, gives_check: bool = False,
                         after_check: bool = False) -> None:
        """Update statistics for a piece on a square."""
        if piece_key not in self.piece_heatmaps:
            self.piece_heatmaps[piece_key] = {}
        
        if square_key not in self.piece_heatmaps[piece_key]:
            self.piece_heatmaps[piece_key][square_key] = PieceData()
            
        data = self.piece_heatmaps[piece_key][square_key]
        data.frequency += 1
        
        if phase == "opening":
            data.phase_distribution.opening += 1
        elif phase == "middlegame":
            data.phase_distribution.middlegame += 1
        else:
            data.phase_distribution.endgame += 1
            
        if move_time is not None:
            data.timing.times_list.append(move_time)
            data.timing.total_time += move_time
            data.timing.avg = data.timing.total_time / data.frequency
            
            if move_time < 10:
                data.timing.fast_moves += 1
            if move_time > 30:
                data.timing.slow_moves += 1
                
        if is_capture:
            data.capture_stats.captures += 1
        if gives_check:
            data.check_stats.gives_check += 1
        if after_check:
            data.check_stats.after_check += 1

    def analyze_game(self, game: chess.pgn.Game) -> None:
        """Analyze a single game with enhanced metrics."""
        board = game.board()
        result = game.headers.get("Result", "*")
        is_white = game.headers.get("White") == self.player_name
        player_won = (is_white and result == "1-0") or (not is_white and result == "0-1")
        
        # Update player stats
        self.player_stats["total_games"] += 1
        color_stats = "white" if is_white else "black"
        
        if player_won:
            self.player_stats["wins"] += 1
            self.player_stats["performance_by_color"][color_stats]["wins"] += 1
        elif result == "1/2-1/2":
            self.player_stats["draws"] += 1
            self.player_stats["performance_by_color"][color_stats]["draws"] += 1
        elif result in ["1-0", "0-1"]:
            self.player_stats["losses"] += 1
            self.player_stats["performance_by_color"][color_stats]["losses"] += 1
            
        # Record opening
        if "Opening" in game.headers:
            self.player_stats["favorite_openings"][game.headers["Opening"]] += 1
        
        moves_in_game = 0
        for node in game.mainline():
            if (board.turn == chess.WHITE) != is_white:
                board.push(node.move)
                continue
                
            move = node.move
            self.total_moves += 1
            moves_in_game += 1
            
            # Get move timing
            move_time = None
            if '[%clk' in node.comment:
                try:
                    time_str = node.comment.split('[%clk ')[1].split(']')[0]
                    h, m, s = map(float, time_str.split(':'))
                    move_time = h * 3600 + m * 60 + s
                except:
                    pass
            
            # Analyze position and move
            phase = self.determine_game_phase(
                board.fullmove_number,
                self.count_pieces(board)
            )
            
            piece = board.piece_at(move.from_square)
            if piece:
                self.update_piece_data(
                    piece_key=piece.symbol(),
                    square_key=chess.square_name(move.to_square),
                    phase=phase,
                    move_time=move_time,
                    is_capture=board.is_capture(move),
                    gives_check=board.gives_check(move),
                    after_check=board.was_into_check()
                )
            
            board.push(move)
        
        # Update average game length
        total_games = self.player_stats["total_games"]
        current_avg = self.player_stats["avg_game_length"]
        self.player_stats["avg_game_length"] = (
            (current_avg * (total_games - 1) + moves_in_game) / total_games
        )

    def analyze_games(self) -> None:
        """Analyze all games in the PGN file."""
        print(f"Starting enhanced analysis of {self.pgn_path}...")
        with open(self.pgn_path) as pgn:
            while True:
                game = chess.pgn.read_game(pgn)
                if game is None:
                    break
                
                if (game.headers.get("White") == self.player_name or 
                    game.headers.get("Black") == self.player_name):
                    self.analyze_game(game)
                    self.analyzed_games += 1
                    if self.analyzed_games % 10 == 0:
                        print(f"Analyzed {self.analyzed_games} games...")
        
        print(f"\nAnalysis complete. Found {self.analyzed_games} games.")
        self.print_summary()

    def print_summary(self) -> None:
        """Print a summary of the analysis results."""
        print("\nPlayer Statistics:")
        print(f"Total Games: {self.player_stats['total_games']}")
        print(f"Wins: {self.player_stats['wins']}")
        print(f"Draws: {self.player_stats['draws']}")
        print(f"Losses: {self.player_stats['losses']}")
        print(f"Average Game Length: {self.player_stats['avg_game_length']:.1f} moves")
        
        print("\nMost Common Openings:")
        sorted_openings = sorted(
            self.player_stats["favorite_openings"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for opening, count in sorted_openings[:5]:
            print(f"{opening}: {count} games")
        
        print("\nPerformance by Color:")
        for color, stats in self.player_stats["performance_by_color"].items():
            total = sum(stats.values())
            if total > 0:
                win_rate = (stats['wins'] / total) * 100
                print(f"{color.title()}: {win_rate:.1f}% win rate "
                      f"({stats['wins']}/{stats['draws']}/{stats['losses']})")

    def save_results(self) -> None:
        """Save analysis results to JSON files."""
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Save piece heatmaps
        heatmap_data = {
            piece: {square: data.to_dict() 
                   for square, data in squares.items()}
            for piece, squares in self.piece_heatmaps.items()
        }
        
        with open(os.path.join(self.results_dir, "piece_heatmaps.json"), 'w') as f:
            json.dump(heatmap_data, f, indent=2)
        
        # Save player stats
        with open(os.path.join(self.results_dir, "player_stats.json"), 'w') as f:
            json.dump(self.player_stats, f, indent=2)
        
        # Save analysis summary
        summary = {
            "analysis_date": datetime.now().isoformat(),
            "total_games": self.analyzed_games,
            "total_moves": self.total_moves,
            "piece_stats": {
                piece: sum(square_data.frequency 
                          for square_data in squares.values())
                for piece, squares in self.piece_heatmaps.items()
            }
        }
        
        with open(os.path.join(self.results_dir, "analysis_summary.json"), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nResults saved to: {self.results_dir}")

if __name__ == "__main__":
    pgn_path = "training_positions/games.pgn"
    results_dir = "results"
    
    analyzer = GameAnalyzer(pgn_path, results_dir)
    analyzer.analyze_games()
    analyzer.save_results()
