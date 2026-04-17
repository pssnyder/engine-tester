#!/usr/bin/env python3
"""
V7P3R Tournament Manager
Professional tournament system for testing chess engines with:
- Parallel game execution
- GM starting positions (moves 5-10 from historical games)
- Configurable time controls, resignation rules, adjudication
- Round-robin, gauntlet, or head-to-head formats
- Real-time ELO calculation
- Comprehensive statistics and reporting
"""

import chess
import chess.pgn
import chess.engine
import subprocess
import threading
import queue
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics


@dataclass
class EngineConfig:
    """Configuration for a tournament engine"""
    name: str
    path: str
    short_name: str = ""
    expected_elo: int = 1500
    
    def __post_init__(self):
        if not self.short_name:
            self.short_name = self.name[:8]


@dataclass
class TimeControl:
    """Time control configuration"""
    base_time_ms: int  # Base time in milliseconds
    increment_ms: int  # Increment per move
    
    @classmethod
    def from_string(cls, tc_string: str):
        """Parse time control from string like '5+3' (minutes+seconds)"""
        base, inc = tc_string.split('+')
        return cls(
            base_time_ms=int(float(base) * 60 * 1000),
            increment_ms=int(float(inc) * 1000)
        )
    
    def __str__(self):
        base_min = self.base_time_ms / 60000
        inc_sec = self.increment_ms / 1000
        return f"{base_min:.0f}+{inc_sec:.0f}"


@dataclass
class ResignationRules:
    """Rules for automatic resignation"""
    enabled: bool = True
    score_threshold_cp: int = -800  # Resign if score < -800cp
    consecutive_moves: int = 3  # Must be losing for N moves
    min_move_number: int = 10  # Don't resign before move 10


@dataclass
class AdjudicationRules:
    """Rules for automatic game adjudication"""
    enabled: bool = True
    win_score_cp: int = 1000  # Adjudicate win if score > 1000cp
    draw_score_cp: int = 10  # Adjudicate draw if |score| < 10cp
    consecutive_moves: int = 5  # Must hold for N moves
    min_move_number: int = 40  # Don't adjudicate before move 40
    fifty_move_rule: bool = True
    threefold_repetition: bool = True


@dataclass
class GameResult:
    """Result of a single game"""
    game_id: int
    white: str
    black: str
    result: str  # "1-0", "0-1", "1/2-1/2"
    termination: str  # "normal", "resignation", "adjudication", "time forfeit"
    moves: int
    duration_seconds: float
    opening: str
    white_elo_before: float
    black_elo_before: float
    white_elo_after: float
    black_elo_after: float
    pgn: str = ""
    final_position: str = ""
    
    def get_score(self, engine_name: str) -> float:
        """Get score for specific engine (1.0=win, 0.5=draw, 0.0=loss)"""
        if self.white == engine_name:
            if self.result == "1-0": return 1.0
            elif self.result == "0-1": return 0.0
            else: return 0.5
        else:
            if self.result == "1-0": return 0.0
            elif self.result == "0-1": return 1.0
            else: return 0.5


@dataclass
class TournamentStats:
    """Statistics for an engine in the tournament"""
    name: str
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    score: float = 0.0  # Total points (win=1, draw=0.5)
    performance_rating: float = 1500.0
    current_elo: float = 1500.0
    white_games: int = 0
    black_games: int = 0
    white_wins: int = 0
    black_wins: int = 0
    avg_game_length: float = 0.0
    resignations_for: int = 0
    resignations_against: int = 0
    time_forfeits: int = 0
    
    def update_from_result(self, result: GameResult):
        """Update stats from a game result"""
        self.games_played += 1
        is_white = (result.white == self.name)
        
        if is_white:
            self.white_games += 1
        else:
            self.black_games += 1
        
        score = result.get_score(self.name)
        self.score += score
        
        if score == 1.0:
            self.wins += 1
            if is_white:
                self.white_wins += 1
            else:
                self.black_wins += 1
        elif score == 0.0:
            self.losses += 1
        else:
            self.draws += 1
        
        if result.termination == "resignation":
            if score == 1.0:
                self.resignations_against += 1
            else:
                self.resignations_for += 1
        
        if result.termination == "time forfeit":
            if score == 0.0:
                self.time_forfeits += 1
        
        # Update derived stats
        self.win_rate = self.wins / self.games_played if self.games_played > 0 else 0.0


class StartingPositionGenerator:
    """Generates starting positions from historical GM games"""
    
    def __init__(self, pgn_directory: str, move_range: Tuple[int, int] = (5, 10)):
        self.pgn_directory = Path(pgn_directory)
        self.move_range = move_range
        self.positions: List[Tuple[str, str]] = []  # (FEN, opening_name)
        self.load_positions()
    
    def load_positions(self):
        """Load positions from PGN files"""
        print(f"Loading GM positions from {self.pgn_directory}...")
        
        if not self.pgn_directory.exists():
            print(f"WARNING: {self.pgn_directory} not found, using default positions")
            self._load_default_positions()
            return
        
        pgn_files = list(self.pgn_directory.glob("**/*.pgn"))
        if not pgn_files:
            print("No PGN files found, using default positions")
            self._load_default_positions()
            return
        
        # Load from up to 5 PGN files to get variety
        for pgn_file in random.sample(pgn_files, min(5, len(pgn_files))):
            positions_from_file = self._extract_positions_from_pgn(pgn_file, max_positions=20)
            self.positions.extend(positions_from_file)
        
        if not self.positions:
            self._load_default_positions()
        
        print(f"Loaded {len(self.positions)} starting positions")
    
    def _extract_positions_from_pgn(self, pgn_path: Path, max_positions: int = 20) -> List[Tuple[str, str]]:
        """Extract positions from a PGN file"""
        positions = []
        
        try:
            with open(pgn_path, 'r', encoding='utf-8', errors='ignore') as f:
                while len(positions) < max_positions:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    # Get opening name
                    opening = game.headers.get("Opening", "Unknown Opening")
                    
                    # Navigate to random position in move range
                    board = game.board()
                    move_num = random.randint(self.move_range[0], self.move_range[1])
                    moves_made = 0
                    
                    for node in game.mainline():
                        board.push(node.move)
                        moves_made += 1
                        if moves_made >= move_num:
                            break
                    
                    if moves_made >= self.move_range[0]:
                        positions.append((board.fen(), f"{opening} (move {moves_made})"))
        
        except Exception as e:
            print(f"Error loading {pgn_path}: {e}")
        
        return positions
    
    def _load_default_positions(self):
        """Load default theoretical opening positions"""
        self.positions = [
            ("rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1", "King's Indian Defense"),
            ("rnbqkb1r/pp2pppp/3p1n2/2p5/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 1", "Queen's Gambit Declined"),
            ("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1", "Ruy Lopez"),
            ("rnbqkb1r/pp1ppppp/5n2/2p5/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq - 0 1", "Sicilian Najdorf"),
            ("rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 1", "French Defense"),
        ]
    
    def get_random_position(self) -> Tuple[str, str]:
        """Get a random starting position"""
        return random.choice(self.positions)


class GameExecutor:
    """Executes a single game between two engines"""
    
    def __init__(self, game_id: int,
                 white_config: EngineConfig,
                 black_config: EngineConfig,
                 time_control: TimeControl,
                 starting_fen: str,
                 opening_name: str,
                 resignation_rules: ResignationRules,
                 adjudication_rules: AdjudicationRules):
        
        self.game_id = game_id
        self.white_config = white_config
        self.black_config = black_config
        self.time_control = time_control
        self.starting_fen = starting_fen
        self.opening_name = opening_name
        self.resignation_rules = resignation_rules
        self.adjudication_rules = adjudication_rules
        
        self.board = chess.Board(starting_fen)
        self.move_history = []
        self.score_history = []
        self.white_time_ms = time_control.base_time_ms
        self.black_time_ms = time_control.base_time_ms
    
    def execute(self) -> GameResult:
        """Execute the game and return result"""
        start_time = time.time()
        
        try:
            # Start engine processes
            white_proc = self._start_engine(self.white_config.path)
            black_proc = self._start_engine(self.black_config.path)
            
            # Initialize engines
            self._send_uci(white_proc)
            self._send_uci(black_proc)
            
            # Play the game
            result, termination = self._play_game(white_proc, black_proc)
            
            # Cleanup
            self._stop_engine(white_proc)
            self._stop_engine(black_proc)
            
        except Exception as e:
            print(f"Game {self.game_id} error: {e}")
            result = "1/2-1/2"
            termination = "error"
        
        duration = time.time() - start_time
        
        return GameResult(
            game_id=self.game_id,
            white=self.white_config.name,
            black=self.black_config.name,
            result=result,
            termination=termination,
            moves=len(self.move_history),
            duration_seconds=duration,
            opening=self.opening_name,
            white_elo_before=self.white_config.expected_elo,
            black_elo_before=self.black_config.expected_elo,
            white_elo_after=self.white_config.expected_elo,  # Updated by tournament manager
            black_elo_after=self.black_config.expected_elo,
            final_position=self.board.fen()
        )
    
    def _start_engine(self, engine_path: str):
        """Start an engine process"""
        return subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    
    def _stop_engine(self, proc):
        """Stop an engine process"""
        try:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=2)
        except:
            proc.terminate()
    
    def _send_uci(self, proc):
        """Initialize engine with UCI"""
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        while True:
            line = proc.stdout.readline().strip()
            if "uciok" in line:
                break
        
        proc.stdin.write("isready\n")
        proc.stdin.flush()
        while True:
            line = proc.stdout.readline().strip()
            if "readyok" in line:
                break
    
    def _play_game(self, white_proc, black_proc) -> Tuple[str, str]:
        """Play game and return (result, termination)"""
        consecutive_bad_scores = {"white": 0, "black": 0}
        consecutive_draw_scores = 0
        
        while not self.board.is_game_over():
            # Check move limit
            if len(self.move_history) > 200:
                return "1/2-1/2", "move limit"
            
            is_white = self.board.turn == chess.WHITE
            proc = white_proc if is_white else black_proc
            time_left = self.white_time_ms if is_white else self.black_time_ms
            
            # Get move from engine
            move, time_used, score = self._get_engine_move(proc, time_left)
            
            if move is None:
                # Time forfeit or engine failure
                return ("0-1" if is_white else "1-0"), "time forfeit"
            
            # Update time
            if is_white:
                self.white_time_ms -= time_used
                self.white_time_ms += self.time_control.increment_ms
            else:
                self.black_time_ms -= time_used
                self.black_time_ms += self.time_control.increment_ms
            
            # Make move
            self.board.push(move)
            self.move_history.append(move)
            self.score_history.append(score)
            
            # Check resignation rules
            if self.resignation_rules.enabled and len(self.move_history) >= self.resignation_rules.min_move_number:
                if score is not None and score < self.resignation_rules.score_threshold_cp:
                    side = "white" if is_white else "black"
                    consecutive_bad_scores[side] += 1
                    if consecutive_bad_scores[side] >= self.resignation_rules.consecutive_moves:
                        return ("0-1" if is_white else "1-0"), "resignation"
                else:
                    consecutive_bad_scores["white"] = 0
                    consecutive_bad_scores["black"] = 0
            
            # Check adjudication rules
            if self.adjudication_rules.enabled and len(self.move_history) >= self.adjudication_rules.min_move_number:
                if score is not None:
                    if score > self.adjudication_rules.win_score_cp:
                        consecutive_draw_scores = 0
                        # Could implement win adjudication here
                    elif abs(score) < self.adjudication_rules.draw_score_cp:
                        consecutive_draw_scores += 1
                        if consecutive_draw_scores >= self.adjudication_rules.consecutive_moves:
                            return "1/2-1/2", "adjudication"
                    else:
                        consecutive_draw_scores = 0
        
        # Game ended normally
        result = self.board.result()
        return result, "normal"
    
    def _get_engine_move(self, proc, time_left_ms: int) -> Tuple[Optional[chess.Move], int, Optional[int]]:
        """Get move from engine, return (move, time_used_ms, score_cp)"""
        # Set position
        position_cmd = f"position fen {self.board.fen()}\n"
        proc.stdin.write(position_cmd)
        proc.stdin.flush()
        
        # Start search with time remaining
        go_cmd = f"go wtime {time_left_ms} btime {time_left_ms} winc {self.time_control.increment_ms} binc {self.time_control.increment_ms}\n"
        proc.stdin.write(go_cmd)
        proc.stdin.flush()
        
        best_move = None
        score = None
        start_time = time.time()
        timeout = (time_left_ms / 1000) + 5  # Allow 5s grace period
        
        while time.time() - start_time < timeout:
            line = proc.stdout.readline().strip()
            
            if "bestmove" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        best_move = chess.Move.from_uci(parts[1])
                    except:
                        best_move = None
                break
            elif "info" in line and "score cp" in line:
                parts = line.split()
                try:
                    cp_idx = parts.index("cp")
                    score = int(parts[cp_idx + 1])
                except:
                    pass
        
        time_used_ms = int((time.time() - start_time) * 1000)
        return best_move, time_used_ms, score


class TournamentManager:
    """Manages a complete chess engine tournament"""
    
    def __init__(self,
                 engines: List[EngineConfig],
                 time_control: TimeControl,
                 starting_positions_dir: str,
                 num_games_per_pairing: int = 2,
                 parallel_games: int = 4,
                 resignation_rules: Optional[ResignationRules] = None,
                 adjudication_rules: Optional[AdjudicationRules] = None):
        
        self.engines = {e.name: e for e in engines}
        self.time_control = time_control
        self.num_games_per_pairing = num_games_per_pairing
        self.parallel_games = parallel_games
        self.resignation_rules = resignation_rules or ResignationRules()
        self.adjudication_rules = adjudication_rules or AdjudicationRules()
        
        # Load starting positions
        self.position_generator = StartingPositionGenerator(starting_positions_dir)
        
        # Tournament state
        self.stats = {name: TournamentStats(name, current_elo=config.expected_elo) 
                     for name, config in self.engines.items()}
        self.results: List[GameResult] = []
        self.current_game_id = 0
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"tournament_results_{timestamp}")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_pairings(self) -> List[Tuple[str, str]]:
        """Generate all pairings for round-robin tournament"""
        pairings = []
        engine_names = list(self.engines.keys())
        
        for i, white_name in enumerate(engine_names):
            for black_name in engine_names[i+1:]:
                for _ in range(self.num_games_per_pairing):
                    pairings.append((white_name, black_name))
                    pairings.append((black_name, white_name))  # Reverse colors
        
        random.shuffle(pairings)
        return pairings
    
    def run_tournament(self):
        """Run the complete tournament"""
        pairings = self.generate_pairings()
        total_games = len(pairings)
        
        print(f"\n{'='*70}")
        print("TOURNAMENT START")
        print(f"{'='*70}")
        print(f"Engines: {', '.join(self.engines.keys())}")
        print(f"Time Control: {self.time_control}")
        print(f"Total Games: {total_games}")
        print(f"Parallel Games: {self.parallel_games}")
        print(f"Starting Positions: {len(self.position_generator.positions)}")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        games_completed = 0
        
        # Execute games in parallel
        with ThreadPoolExecutor(max_workers=self.parallel_games) as executor:
            futures = []
            
            for white_name, black_name in pairings:
                fen, opening = self.position_generator.get_random_position()
                
                game = GameExecutor(
                    game_id=self.current_game_id,
                    white_config=self.engines[white_name],
                    black_config=self.engines[black_name],
                    time_control=self.time_control,
                    starting_fen=fen,
                    opening_name=opening,
                    resignation_rules=self.resignation_rules,
                    adjudication_rules=self.adjudication_rules
                )
                
                self.current_game_id += 1
                futures.append(executor.submit(game.execute))
            
            # Process results as they complete
            for future in as_completed(futures):
                result = future.result()
                self._process_result(result)
                games_completed += 1
                
                # Progress update
                if games_completed % 10 == 0 or games_completed == total_games:
                    elapsed = time.time() - start_time
                    games_per_min = (games_completed / elapsed) * 60
                    eta = ((total_games - games_completed) / games_per_min) if games_per_min > 0 else 0
                    
                    print(f"Progress: {games_completed}/{total_games} games ({games_completed/total_games*100:.0f}%) | "
                          f"{games_per_min:.1f} games/min | ETA: {eta:.1f}min")
                    
                    # Intermediate standings
                    if games_completed % 50 == 0:
                        self._print_standings()
        
        # Final report
        duration = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"TOURNAMENT COMPLETE - {duration/60:.1f} minutes")
        print(f"{'='*70}\n")
        
        self._print_final_report()
        self._save_results()
    
    def _process_result(self, result: GameResult):
        """Process a game result and update stats"""
        # Update ELO ratings
        white_elo = self.stats[result.white].current_elo
        black_elo = self.stats[result.black].current_elo
        
        white_score = result.get_score(result.white)
        
        # Simple ELO calculation (K=32)
        expected_white = 1 / (1 + 10 ** ((black_elo - white_elo) / 400))
        white_elo_change = 32 * (white_score - expected_white)
        
        result.white_elo_before = white_elo
        result.black_elo_before = black_elo
        result.white_elo_after = white_elo + white_elo_change
        result.black_elo_after = black_elo - white_elo_change
        
        self.stats[result.white].current_elo = result.white_elo_after
        self.stats[result.black].current_elo = result.black_elo_after
        
        # Update stats
        self.stats[result.white].update_from_result(result)
        self.stats[result.black].update_from_result(result)
        
        self.results.append(result)
    
    def _print_standings(self):
        """Print current standings"""
        sorted_stats = sorted(self.stats.values(), key=lambda s: s.score, reverse=True)
        
        print(f"\n{'='*70}")
        print("CURRENT STANDINGS")
        print(f"{'='*70}")
        print(f"{'Engine':<15} {'Games':>6} {'Score':>7} {'W-L-D':>10} {'ELO':>7} {'Rate%':>7}")
        print("-" * 70)
        
        for stat in sorted_stats:
            wld = f"{stat.wins}-{stat.losses}-{stat.draws}"
            print(f"{stat.name:<15} {stat.games_played:>6} {stat.score:>7.1f} {wld:>10} "
                  f"{stat.current_elo:>7.0f} {stat.win_rate*100:>6.1f}%")
        print()
    
    def _print_final_report(self):
        """Print comprehensive final report"""
        sorted_stats = sorted(self.stats.values(), key=lambda s: s.score, reverse=True)
        
        print(f"\n{'='*70}")
        print("FINAL STANDINGS")
        print(f"{'='*70}")
        print(f"{'Rank':<5} {'Engine':<15} {'Games':>6} {'Score':>7} {'W-L-D':>12} {'ELO':>7} {'Rate%':>7}")
        print("-" * 70)
        
        for rank, stat in enumerate(sorted_stats, 1):
            wld = f"{stat.wins}-{stat.losses}-{stat.draws}"
            print(f"{rank:<5} {stat.name:<15} {stat.games_played:>6} {stat.score:>7.1f} {wld:>12} "
                  f"{stat.current_elo:>7.0f} {stat.win_rate*100:>6.1f}%")
        
        print(f"\n{'='*70}")
        print("HEAD-TO-HEAD RESULTS")
        print(f"{'='*70}")
        
        # Calculate head-to-head
        h2h = {}
        for result in self.results:
            key = tuple(sorted([result.white, result.black]))
            if key not in h2h:
                h2h[key] = {result.white: {"wins": 0, "draws": 0, "losses": 0},
                           result.black: {"wins": 0, "draws": 0, "losses": 0}}
            
            white_score = result.get_score(result.white)
            if white_score == 1.0:
                h2h[key][result.white]["wins"] += 1
                h2h[key][result.black]["losses"] += 1
            elif white_score == 0.0:
                h2h[key][result.white]["losses"] += 1
                h2h[key][result.black]["wins"] += 1
            else:
                h2h[key][result.white]["draws"] += 1
                h2h[key][result.black]["draws"] += 1
        
        for pairing, stats in h2h.items():
            print(f"\n{pairing[0]} vs {pairing[1]}:")
            for engine in pairing:
                s = stats[engine]
                total = s["wins"] + s["draws"] + s["losses"]
                score = s["wins"] + s["draws"] * 0.5
                print(f"  {engine}: {s['wins']}-{s['draws']}-{s['losses']} ({score}/{total})")
    
    def _save_results(self):
        """Save tournament results to files"""
        # Save JSON
        json_path = self.output_dir / "results.json"
        with open(json_path, 'w') as f:
            json.dump({
                "tournament_info": {
                    "time_control": str(self.time_control),
                    "total_games": len(self.results),
                    "engines": [e.name for e in self.engines.values()]
                },
                "final_standings": [asdict(s) for s in sorted(self.stats.values(), key=lambda s: s.score, reverse=True)],
                "games": [asdict(r) for r in self.results]
            }, f, indent=2)
        
        print(f"\n✅ Results saved to {json_path}")


def main():
    """Example tournament configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='V7P3R Tournament Manager')
    parser.add_argument('--time-control', default='5+3', help='Time control (e.g., 5+3 for 5min+3sec)')
    parser.add_argument('--games-per-pairing', type=int, default=2, help='Games per pairing')
    parser.add_argument('--parallel', type=int, default=4, help='Parallel games')
    
    args = parser.parse_args()
    
    # Configure engines (update paths as needed)
    engines = [
        EngineConfig(
            name="V7P3R v18.4",
            path=r"e:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\lichess\engines\V7P3R_v18.4_20260415\V7P3R_v18.4.bat",
            expected_elo=1500
        ),
        EngineConfig(
            name="V7P3R v18.3",
            path=r"e:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\lichess\engines\V7P3R_v18.3_20251229\V7P3R_v18.3.bat",
            expected_elo=1500
        ),
        # Add more engines as needed
    ]
    
    time_control = TimeControl.from_string(args.time_control)
    
    tournament = TournamentManager(
        engines=engines,
        time_control=time_control,
        starting_positions_dir=r"e:\Programming Stuff\Chess Engines\Chess PGNs\training_data\pgn_data_important_games",
        num_games_per_pairing=args.games_per_pairing,
        parallel_games=args.parallel,
        resignation_rules=ResignationRules(enabled=True, score_threshold_cp=-800, consecutive_moves=3),
        adjudication_rules=AdjudicationRules(enabled=True, draw_score_cp=10, consecutive_moves=5)
    )
    
    tournament.run_tournament()


if __name__ == "__main__":
    main()
