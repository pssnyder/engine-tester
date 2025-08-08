#!/usr/bin/env python3
"""
Tournament Analyzer for Chess Engine Performance Metrics

Parses PGN files from tournament_results/ directory and generates comprehensive
statistics for engine performance comparison and ranking.

Key Metrics:
- Total games, wins, losses, draws per engine
- Tournament points (1 win = 1 point, 0.5 draw = 0.5 points)
- Overall win rate percentage
- Decisive win rate (checkmate victories only)
- Head-to-head records between engines
"""

import re
import os
import glob
import json
import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

@dataclass
class GameResult:
    """Single game result parsed from PGN"""
    white: str
    black: str
    result: str  # "1-0", "0-1", "1/2-1/2"
    termination: str  # "normal", "time forfeit", etc.
    event: str
    date: str
    ply_count: int
    moves: str  # actual move sequence for analysis

@dataclass
class EngineStats:
    """Comprehensive statistics for a single engine"""
    name: str
    games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    
    # Decisive wins (checkmate only)
    decisive_wins: int = 0
    
    # Tournament points (1 for win, 0.5 for draw)
    points: float = 0.0
    
    # Head-to-head records against specific opponents
    head_to_head: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0}))
    
    def add_game(self, game: GameResult, playing_white: bool):
        """Add a game result to this engine's statistics"""
        self.games += 1
        
        opponent = game.black if playing_white else game.white
        
        if game.result == "1-0":  # White wins
            if playing_white:
                self.wins += 1
                self.points += 1.0
                self.head_to_head[opponent]["wins"] += 1
                if "#" in game.moves:  # Checkmate symbol in moves
                    self.decisive_wins += 1
            else:
                self.losses += 1
                self.head_to_head[opponent]["losses"] += 1
                
        elif game.result == "0-1":  # Black wins
            if not playing_white:
                self.wins += 1
                self.points += 1.0
                self.head_to_head[opponent]["wins"] += 1
                if "#" in game.moves:  # Checkmate symbol in moves
                    self.decisive_wins += 1
            else:
                self.losses += 1
                self.head_to_head[opponent]["losses"] += 1
                
        else:  # Draw (1/2-1/2)
            self.draws += 1
            self.points += 0.5
            self.head_to_head[opponent]["draws"] += 1
    
    @property
    def win_rate(self) -> float:
        """Overall win percentage"""
        return (self.wins / self.games * 100) if self.games > 0 else 0.0
    
    @property
    def decisive_win_rate(self) -> float:
        """Percentage of games won by checkmate"""
        return (self.decisive_wins / self.games * 100) if self.games > 0 else 0.0
    
    @property
    def draw_rate(self) -> float:
        """Draw percentage"""
        return (self.draws / self.games * 100) if self.games > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "games": self.games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "decisive_wins": self.decisive_wins,
            "points": self.points,
            "win_rate": round(self.win_rate, 2),
            "decisive_win_rate": round(self.decisive_win_rate, 2),
            "draw_rate": round(self.draw_rate, 2),
            "head_to_head": dict(self.head_to_head)
        }


class PGNParser:
    """Parser for tournament PGN files"""
    
    def __init__(self):
        self.header_pattern = re.compile(r'\[(\w+)\s+"([^"]+)"\]')
        self.result_pattern = re.compile(r'(1-0|0-1|1/2-1/2)$')
    
    def parse_file(self, filepath: str) -> List[GameResult]:
        """Parse a single PGN file and return list of games"""
        games = []
        
        # Try multiple encodings for PGN files
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                return games
        
        if content is None:
            print(f"Could not decode {filepath} with any encoding")
            return games
        
        # Split into individual games (separated by double newlines)
        raw_games = re.split(r'\n\s*\n(?=\[)', content.strip())
        
        for raw_game in raw_games:
            if not raw_game.strip():
                continue
                
            game = self._parse_single_game(raw_game)
            if game:
                games.append(game)
        
        return games
    
    def _parse_single_game(self, raw_game: str) -> Optional[GameResult]:
        """Parse a single game from PGN text"""
        lines = raw_game.strip().split('\n')
        
        headers = {}
        move_lines = []
        
        # Separate headers from moves
        in_moves = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('[') and line.endswith(']'):
                if not in_moves:
                    match = self.header_pattern.match(line)
                    if match:
                        headers[match.group(1)] = match.group(2)
            else:
                in_moves = True
                move_lines.append(line)
        
        # Extract required headers
        try:
            white = headers.get('White', 'Unknown')
            black = headers.get('Black', 'Unknown')
            result = headers.get('Result', '*')
            termination = headers.get('Termination', 'unknown')
            event = headers.get('Event', 'Unknown Tournament')
            date = headers.get('Date', '????.??.??')
            ply_count = int(headers.get('PlyCount', '0'))
            
            # Join move text
            moves = ' '.join(move_lines)
            
            # Skip incomplete games
            if result == '*' or result not in ['1-0', '0-1', '1/2-1/2']:
                return None
                
            return GameResult(
                white=white,
                black=black,
                result=result,
                termination=termination,
                event=event,
                date=date,
                ply_count=ply_count,
                moves=moves
            )
            
        except Exception as e:
            print(f"Error parsing game: {e}")
            return None


class TournamentAnalyzer:
    """Main analyzer class for processing tournament results"""
    
    def __init__(self, results_dir: str = "tournament_results"):
        self.results_dir = results_dir
        self.parser = PGNParser()
        self.engines: Dict[str, EngineStats] = {}
        self.all_games: List[GameResult] = []
    
    def analyze_tournaments(self):
        """Process all PGN files in the results directory"""
        pgn_files = glob.glob(os.path.join(self.results_dir, "*.pgn"))
        
        if not pgn_files:
            print(f"No PGN files found in {self.results_dir}")
            return
        
        print(f"Processing {len(pgn_files)} PGN files...")
        
        for pgn_file in pgn_files:
            print(f"  Parsing {os.path.basename(pgn_file)}...")
            games = self.parser.parse_file(pgn_file)
            self.all_games.extend(games)
            
            for game in games:
                self._process_game(game)
        
        print(f"Processed {len(self.all_games)} games from {len(self.engines)} engines")
    
    def _process_game(self, game: GameResult):
        """Process a single game and update engine statistics"""
        # Ensure both engines exist in our stats
        if game.white not in self.engines:
            self.engines[game.white] = EngineStats(name=game.white)
        if game.black not in self.engines:
            self.engines[game.black] = EngineStats(name=game.black)
        
        # Update statistics for both engines
        self.engines[game.white].add_game(game, playing_white=True)
        self.engines[game.black].add_game(game, playing_white=False)
    
    def get_rankings_by_points(self) -> List[EngineStats]:
        """Get engines ranked by tournament points (descending)"""
        return sorted(self.engines.values(), key=lambda e: e.points, reverse=True)
    
    def get_rankings_by_win_rate(self) -> List[EngineStats]:
        """Get engines ranked by win rate (descending)"""
        # Only rank engines with at least 5 games to avoid statistical noise
        qualified = [e for e in self.engines.values() if e.games >= 5]
        return sorted(qualified, key=lambda e: e.win_rate, reverse=True)
    
    def get_rankings_by_decisive_wins(self) -> List[EngineStats]:
        """Get engines ranked by decisive win rate (descending)"""
        qualified = [e for e in self.engines.values() if e.games >= 5]
        return sorted(qualified, key=lambda e: e.decisive_win_rate, reverse=True)
    
    def generate_reports(self, json_path: str, md_path: str):
        """Generate JSON and Markdown reports"""
        
        # Prepare data for JSON
        report_data = {
            "total_games": len(self.all_games),
            "total_engines": len(self.engines),
            "rankings_by_points": [e.to_dict() for e in self.get_rankings_by_points()],
            "rankings_by_win_rate": [e.to_dict() for e in self.get_rankings_by_win_rate()],
            "rankings_by_decisive_wins": [e.to_dict() for e in self.get_rankings_by_decisive_wins()],
            "all_engines": {name: stats.to_dict() for name, stats in self.engines.items()}
        }
        
        # Write JSON report
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate Markdown report
        self._generate_markdown_report(md_path)
        
        print(f"Reports generated:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
    
    def _generate_markdown_report(self, md_path: str):
        """Generate detailed Markdown report"""
        lines = []
        
        lines.append("# Chess Engine Tournament Analysis")
        lines.append("")
        lines.append(f"**Total Games Analyzed:** {len(self.all_games)}")
        lines.append(f"**Total Engines:** {len(self.engines)}")
        lines.append("")
        
        # Tournament Points Ranking
        lines.append("## Rankings by Tournament Points")
        lines.append("")
        lines.append("| Rank | Engine | Games | W-L-D | Points | Win Rate | Checkmates | Decisive Win Rate |")
        lines.append("|------|---------|-------|-------|---------|----------|------------|-------------------|")
        
        for i, engine in enumerate(self.get_rankings_by_points(), 1):
            wld = f"{engine.wins}-{engine.losses}-{engine.draws}"
            lines.append(f"| {i} | {engine.name} | {engine.games} | {wld} | {engine.points:.1f} | {engine.win_rate:.1f}% | {engine.decisive_wins} | {engine.decisive_win_rate:.1f}% |")
        
        lines.append("")
        
        # Win Rate Ranking
        lines.append("## Rankings by Win Rate (≥5 games)")
        lines.append("")
        lines.append("| Rank | Engine | Games | Win Rate | Wins | Losses | Draws | Checkmates |")
        lines.append("|------|---------|-------|----------|------|--------|-------|------------|")
        
        for i, engine in enumerate(self.get_rankings_by_win_rate(), 1):
            lines.append(f"| {i} | {engine.name} | {engine.games} | {engine.win_rate:.1f}% | {engine.wins} | {engine.losses} | {engine.draws} | {engine.decisive_wins} |")
        
        lines.append("")
        
        # Decisive Wins Ranking
        lines.append("## Rankings by Decisive Win Rate (≥5 games)")
        lines.append("*Decisive wins = victories by checkmate*")
        lines.append("")
        lines.append("| Rank | Engine | Games | Checkmates | Decisive Win Rate | Total Wins |")
        lines.append("|------|---------|-------|------------|-------------------|------------|")
        
        for i, engine in enumerate(self.get_rankings_by_decisive_wins(), 1):
            lines.append(f"| {i} | {engine.name} | {engine.games} | {engine.decisive_wins} | {engine.decisive_win_rate:.1f}% | {engine.wins} |")
        
        lines.append("")
        
        # Detailed Statistics
        lines.append("## Detailed Engine Statistics")
        lines.append("")
        
        for engine in self.get_rankings_by_points():
            lines.append(f"### {engine.name}")
            lines.append(f"- **Games:** {engine.games}")
            lines.append(f"- **Record:** {engine.wins}W-{engine.losses}L-{engine.draws}D")
            lines.append(f"- **Tournament Points:** {engine.points:.1f}")
            lines.append(f"- **Win Rate:** {engine.win_rate:.1f}%")
            lines.append(f"- **Decisive Wins:** {engine.decisive_wins} ({engine.decisive_win_rate:.1f}%)")
            lines.append(f"- **Draw Rate:** {engine.draw_rate:.1f}%")
            lines.append("")
        
        # Write to file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description='Analyze chess engine tournament results from PGN files')
    parser.add_argument('--dir', default='tournament_results', help='Directory containing PGN files')
    parser.add_argument('--json', help='Output JSON report path')
    parser.add_argument('--md', help='Output Markdown report path')
    args = parser.parse_args()
    
    # Default output paths
    if not args.json:
        args.json = 'tournament_analysis.json'
    if not args.md:
        args.md = 'tournament_analysis.md'
    
    # Run analysis
    analyzer = TournamentAnalyzer(args.dir)
    analyzer.analyze_tournaments()
    analyzer.generate_reports(args.json, args.md)


if __name__ == '__main__':
    main()
