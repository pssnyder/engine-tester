#!/usr/bin/env python3
"""
Enhanced PGN Game Analyzer

This module provides detailed parsing and analysis of PGN games,
extracting move sequences, time information, and position data
for use in version comparison analysis.
"""

import chess
import chess.pgn
import chess.engine
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from io import StringIO

@dataclass
class DetailedMove:
    """Detailed information about a single move"""
    move_number: int
    color: str  # "white" or "black"
    san_notation: str
    uci_notation: str
    position_before: str  # FEN
    position_after: str   # FEN
    time_spent: Optional[float] = None  # Seconds
    time_remaining: Optional[float] = None  # Seconds
    evaluation: Optional[float] = None  # Centipawns
    comment: str = ""
    
    @property
    def is_capture(self) -> bool:
        return 'x' in self.san_notation
    
    @property
    def is_check(self) -> bool:
        return '+' in self.san_notation
    
    @property
    def is_checkmate(self) -> bool:
        return '#' in self.san_notation
    
    @property
    def piece_moved(self) -> str:
        """Extract the piece that moved"""
        if self.san_notation[0] in 'KQRBN':
            return self.san_notation[0]
        elif self.san_notation.startswith('O-O'):
            return 'K'  # King castling
        else:
            return 'P'  # Pawn move

@dataclass 
class DetailedGameAnalysis:
    """Complete detailed analysis of a game"""
    white_player: str
    black_player: str
    result: str
    tournament: str
    date: str
    opening: str
    eco_code: str
    termination: str
    
    moves: List[DetailedMove] = field(default_factory=list)
    total_moves: int = 0
    game_duration: Optional[float] = None  # Total game time in seconds
    
    # Time analysis
    white_total_time: Optional[float] = None
    black_total_time: Optional[float] = None
    white_avg_move_time: Optional[float] = None
    black_avg_move_time: Optional[float] = None
    
    # Opening analysis
    opening_moves_count: int = 12  # First 12 moves considered opening
    middlegame_start: int = 13
    endgame_start: Optional[int] = None  # Determined by piece count
    
    def __post_init__(self):
        pass  # moves field now handled by default_factory
    
    def get_moves_by_player(self, color: str) -> List[DetailedMove]:
        """Get all moves by a specific player"""
        return [move for move in self.moves if move.color == color]
    
    def get_moves_by_phase(self, phase: str) -> List[DetailedMove]:
        """Get moves from a specific game phase"""
        if phase == "opening":
            return [m for m in self.moves if m.move_number <= self.opening_moves_count]
        elif phase == "middlegame":
            end_move = self.endgame_start or len(self.moves)
            return [m for m in self.moves if self.middlegame_start <= m.move_number < end_move]
        elif phase == "endgame":
            if self.endgame_start:
                return [m for m in self.moves if m.move_number >= self.endgame_start]
            else:
                return []
        else:
            return []
    
    def calculate_time_statistics(self):
        """Calculate time-related statistics"""
        white_moves = self.get_moves_by_player("white")
        black_moves = self.get_moves_by_player("black")
        
        # Calculate total time spent
        white_times = [m.time_spent for m in white_moves if m.time_spent is not None]
        black_times = [m.time_spent for m in black_moves if m.time_spent is not None]
        
        if white_times:
            self.white_total_time = sum(white_times)
            self.white_avg_move_time = self.white_total_time / len(white_times)
        
        if black_times:
            self.black_total_time = sum(black_times)
            self.black_avg_move_time = self.black_total_time / len(black_times)
    
    def determine_endgame_start(self):
        """Determine when endgame begins based on piece count"""
        for i, move in enumerate(self.moves):
            try:
                board = chess.Board(move.position_after)
                piece_count = len(board.piece_map())
                
                # Endgame typically starts when fewer than 14 pieces remain
                if piece_count <= 14:
                    self.endgame_start = move.move_number
                    break
            except:
                continue

class EnhancedPGNAnalyzer:
    """Enhanced PGN analyzer with detailed move extraction"""
    
    def __init__(self):
        self.time_control_regex = re.compile(r'\[TimeControl "(\d+)(?:\+(\d+))?"?\]')
        self.clock_regex = re.compile(r'\[%clk (\d+):(\d+):(\d+(?:\.\d+)?)\]')
        
    def extract_time_from_comment(self, comment: str) -> Optional[float]:
        """Extract time remaining from move comment"""
        match = self.clock_regex.search(comment)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        return None
    
    def parse_pgn_detailed(self, pgn_content: str) -> List[DetailedGameAnalysis]:
        """Parse PGN content with detailed move analysis"""
        games = []
        pgn_io = StringIO(pgn_content)
        
        while True:
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                
                analysis = self.analyze_game_detailed(game)
                if analysis:
                    games.append(analysis)
                    
            except Exception as e:
                print(f"Error parsing game: {e}")
                continue
        
        return games
    
    def analyze_game_detailed(self, game: chess.pgn.Game) -> Optional[DetailedGameAnalysis]:
        """Perform detailed analysis of a single game"""
        try:
            headers = game.headers
            
            # Extract basic game information
            analysis = DetailedGameAnalysis(
                white_player=headers.get("White", "Unknown"),
                black_player=headers.get("Black", "Unknown"),
                result=headers.get("Result", "*"),
                tournament=headers.get("Event", "Unknown"),
                date=headers.get("Date", "????.??.??"),
                opening=headers.get("Opening", ""),
                eco_code=headers.get("ECO", ""),
                termination=headers.get("Termination", "normal")
            )
            
            # Parse moves with detailed information
            board = chess.Board()
            node = game
            move_number = 1
            previous_eval = None
            
            while node.variations:
                next_node = node.variation(0)
                move = next_node.move
                
                if move is None:
                    break
                
                # Determine whose move it is
                color = "white" if board.turn == chess.WHITE else "black"
                
                # Get position before move
                position_before = board.fen()
                
                # Make the move
                board.push(move)
                position_after = board.fen()
                
                # Extract time information from comment
                comment = next_node.comment or ""
                time_spent = None
                time_remaining = self.extract_time_from_comment(comment)
                
                # Create detailed move
                detailed_move = DetailedMove(
                    move_number=move_number if color == "white" else move_number - 1,
                    color=color,
                    san_notation=board.san(move),
                    uci_notation=move.uci(),
                    position_before=position_before,
                    position_after=position_after,
                    time_spent=time_spent,
                    time_remaining=time_remaining,
                    comment=comment
                )
                
                analysis.moves.append(detailed_move)
                
                # Increment move number for white moves
                if color == "black":
                    move_number += 1
                
                node = next_node
            
            analysis.total_moves = len(analysis.moves)
            
            # Calculate time statistics
            analysis.calculate_time_statistics()
            
            # Determine game phases
            analysis.determine_endgame_start()
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing game: {e}")
            return None
    
    def load_pgn_file(self, filepath: str) -> List[DetailedGameAnalysis]:
        """Load and analyze a PGN file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.parse_pgn_detailed(content)
        except Exception as e:
            print(f"Error loading PGN file {filepath}: {e}")
            return []
    
    def filter_games_by_engine(self, games: List[DetailedGameAnalysis], 
                              engine_name: str) -> List[Tuple[DetailedGameAnalysis, str]]:
        """Filter games where the specified engine played and return (game, color) tuples"""
        filtered = []
        
        for game in games:
            if engine_name.lower() in game.white_player.lower():
                filtered.append((game, "white"))
            elif engine_name.lower() in game.black_player.lower():
                filtered.append((game, "black"))
        
        return filtered
    
    def extract_opening_repertoire(self, games: List[Tuple[DetailedGameAnalysis, str]]) -> Dict[str, Any]:
        """Extract opening repertoire statistics"""
        openings = {}
        eco_codes = {}
        
        for game, color in games:
            opening = game.opening or "Unknown"
            eco = game.eco_code or "Unknown"
            
            if opening not in openings:
                openings[opening] = {"count": 0, "wins": 0, "draws": 0, "losses": 0}
            
            if eco not in eco_codes:
                eco_codes[eco] = {"count": 0, "wins": 0, "draws": 0, "losses": 0}
            
            # Count the game
            openings[opening]["count"] += 1
            eco_codes[eco]["count"] += 1
            
            # Determine result from engine's perspective
            if game.result == "1-0":
                result = "wins" if color == "white" else "losses"
            elif game.result == "0-1":
                result = "wins" if color == "black" else "losses"
            else:
                result = "draws"
            
            openings[opening][result] += 1
            eco_codes[eco][result] += 1
        
        return {
            "openings": openings,
            "eco_codes": eco_codes,
            "total_games": len(games)
        }
    
    def analyze_time_management(self, games: List[Tuple[DetailedGameAnalysis, str]]) -> Dict[str, Any]:
        """Analyze time management patterns"""
        time_stats = {
            "avg_move_time": [],
            "total_game_time": [],
            "time_by_phase": {
                "opening": [],
                "middlegame": [],
                "endgame": []
            },
            "time_pressure_moves": 0,  # Moves made with <30 seconds
            "total_moves": 0
        }
        
        for game, color in games:
            # Get engine's moves
            engine_moves = game.get_moves_by_player(color)
            
            if not engine_moves:
                continue
            
            # Calculate average move time
            move_times = [m.time_spent for m in engine_moves if m.time_spent is not None]
            if move_times:
                time_stats["avg_move_time"].append(sum(move_times) / len(move_times))
                time_stats["total_game_time"].append(sum(move_times))
            
            # Analyze time by phase
            for phase in ["opening", "middlegame", "endgame"]:
                phase_moves = game.get_moves_by_phase(phase)
                engine_phase_moves = [m for m in phase_moves if m.color == color]
                
                phase_times = [m.time_spent for m in engine_phase_moves if m.time_spent is not None]
                if phase_times:
                    time_stats["time_by_phase"][phase].extend(phase_times)
            
            # Count time pressure moves (remaining time < 30 seconds)
            for move in engine_moves:
                if move.time_remaining is not None and move.time_remaining < 30:
                    time_stats["time_pressure_moves"] += 1
            
            time_stats["total_moves"] += len(engine_moves)
        
        # Calculate averages
        if time_stats["avg_move_time"]:
            time_stats["overall_avg_move_time"] = sum(time_stats["avg_move_time"]) / len(time_stats["avg_move_time"])
        
        if time_stats["total_game_time"]:
            time_stats["overall_avg_game_time"] = sum(time_stats["total_game_time"]) / len(time_stats["total_game_time"])
        
        for phase in time_stats["time_by_phase"]:
            phase_times = time_stats["time_by_phase"][phase]
            if phase_times:
                time_stats["time_by_phase"][phase] = {
                    "avg_time": sum(phase_times) / len(phase_times),
                    "total_moves": len(phase_times),
                    "total_time": sum(phase_times)
                }
            else:
                time_stats["time_by_phase"][phase] = {
                    "avg_time": 0,
                    "total_moves": 0,
                    "total_time": 0
                }
        
        # Calculate time pressure percentage
        if time_stats["total_moves"] > 0:
            time_stats["time_pressure_percentage"] = (time_stats["time_pressure_moves"] / time_stats["total_moves"]) * 100
        
        return time_stats

def main():
    """Test the enhanced PGN analyzer"""
    analyzer = EnhancedPGNAnalyzer()
    
    # Test with a sample PGN file
    # You would replace this with actual PGN file path
    test_file = "../../results/sample_tournament/games.pgn"
    
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found. Please provide a valid PGN file path.")
        return
    
    print("Testing Enhanced PGN Analyzer...")
    games = analyzer.load_pgn_file(test_file)
    print(f"Loaded {len(games)} games")
    
    # Filter for a specific engine
    engine_games = analyzer.filter_games_by_engine(games, "SlowMate")
    print(f"Found {len(engine_games)} games for SlowMate")
    
    if engine_games:
        # Analyze opening repertoire
        repertoire = analyzer.extract_opening_repertoire(engine_games)
        print(f"Opening analysis: {len(repertoire['openings'])} different openings")
        
        # Analyze time management
        time_analysis = analyzer.analyze_time_management(engine_games)
        print(f"Time analysis: {time_analysis.get('overall_avg_move_time', 0):.2f}s average move time")

if __name__ == "__main__":
    import os
    main()
