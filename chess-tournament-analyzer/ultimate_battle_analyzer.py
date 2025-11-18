#!/usr/bin/env python3
"""
Ultimate Engine Battle Analyzer
Analyzes the week-long 90-minute classical tournament results
"""

import chess.pgn
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
import json

class UltimateBattleAnalyzer:
    def __init__(self, pgn_file: str):
        self.pgn_file = pgn_file
        self.games = []
        self.engine_stats = defaultdict(lambda: {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'total_games': 0,
            'white_games': 0,
            'black_games': 0,
            'white_wins': 0,
            'black_wins': 0,
            'total_moves': 0,
            'total_depth': 0,
            'total_nodes': 0,
            'total_time': 0,
            'move_count': 0,
            'depths': [],
            'nodes': [],
            'times': [],
            'opponents_beaten': set(),
            'opponents_lost_to': set(),
            'openings': defaultdict(int),
            'game_lengths': [],
            'as_white': {'wins': 0, 'losses': 0, 'draws': 0},
            'as_black': {'wins': 0, 'losses': 0, 'draws': 0},
        })
        self.matchups = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0}))
        
    def parse_pgn(self):
        """Parse the PGN file and extract all games"""
        print(f"📖 Parsing PGN file: {self.pgn_file}")
        
        with open(self.pgn_file) as f:
            game_count = 0
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                
                self.games.append(game)
                game_count += 1
                
                if game_count % 10 == 0:
                    print(f"  Loaded {game_count} games...", end='\r')
        
        print(f"\n✓ Loaded {len(self.games)} total games")
        return len(self.games)
    
    def extract_move_data(self, comment: str) -> Tuple[int, int, int]:
        """Extract depth, nodes, and time from move comment"""
        # Comment format: (move-pv depth/max_depth time) score
        # Example: (Ng1-f3 e7-e6 d2-d3 Bf8-b4+ c2-c3) +0.48/5 12
        depth = 0
        nodes = 0
        time_ms = 0
        
        # Extract depth (format: score/depth or just /depth)
        depth_match = re.search(r'/(\d+)', comment)
        if depth_match:
            depth = int(depth_match.group(1))
        
        # Extract time (last number in comment, typically milliseconds)
        time_match = re.search(r'(\d+)\s*$', comment)
        if time_match:
            time_ms = int(time_match.group(1))
        
        return depth, nodes, time_ms
    
    def analyze_games(self):
        """Analyze all parsed games"""
        print(f"\n🔍 Analyzing {len(self.games)} games...")
        
        for game_idx, game in enumerate(self.games):
            white = game.headers.get('White', 'Unknown')
            black = game.headers.get('Black', 'Unknown')
            result = game.headers.get('Result', '*')
            opening = game.headers.get('Opening', 'Unknown')
            
            # Track opening usage
            self.engine_stats[white]['openings'][opening] += 1
            
            # Track game results
            self.engine_stats[white]['total_games'] += 1
            self.engine_stats[black]['total_games'] += 1
            self.engine_stats[white]['white_games'] += 1
            self.engine_stats[black]['black_games'] += 1
            
            if result == '1-0':
                self.engine_stats[white]['wins'] += 1
                self.engine_stats[white]['white_wins'] += 1
                self.engine_stats[white]['as_white']['wins'] += 1
                self.engine_stats[black]['losses'] += 1
                self.engine_stats[black]['as_black']['losses'] += 1
                self.engine_stats[white]['opponents_beaten'].add(black)
                self.engine_stats[black]['opponents_lost_to'].add(white)
                self.matchups[white][black]['wins'] += 1
                self.matchups[black][white]['losses'] += 1
            elif result == '0-1':
                self.engine_stats[black]['wins'] += 1
                self.engine_stats[black]['black_wins'] += 1
                self.engine_stats[black]['as_black']['wins'] += 1
                self.engine_stats[white]['losses'] += 1
                self.engine_stats[white]['as_white']['losses'] += 1
                self.engine_stats[black]['opponents_beaten'].add(white)
                self.engine_stats[white]['opponents_lost_to'].add(black)
                self.matchups[black][white]['wins'] += 1
                self.matchups[white][black]['losses'] += 1
            elif result == '1/2-1/2':
                self.engine_stats[white]['draws'] += 1
                self.engine_stats[black]['draws'] += 1
                self.engine_stats[white]['as_white']['draws'] += 1
                self.engine_stats[black]['as_black']['draws'] += 1
                self.matchups[white][black]['draws'] += 1
                self.matchups[black][white]['draws'] += 1
            
            # Analyze moves
            board = game.board()
            move_count = 0
            
            for node in game.mainline():
                move_count += 1
                comment = node.comment
                
                # Determine which engine made this move
                engine = white if board.turn == chess.WHITE else black
                
                # Extract move data from comment
                if comment:
                    depth, nodes, time_ms = self.extract_move_data(comment)
                    
                    if depth > 0:
                        self.engine_stats[engine]['depths'].append(depth)
                        self.engine_stats[engine]['total_depth'] += depth
                    
                    if nodes > 0:
                        self.engine_stats[engine]['nodes'].append(nodes)
                        self.engine_stats[engine]['total_nodes'] += nodes
                    
                    if time_ms > 0:
                        self.engine_stats[engine]['times'].append(time_ms)
                        self.engine_stats[engine]['total_time'] += time_ms
                    
                    self.engine_stats[engine]['move_count'] += 1
                
                board.push(node.move)
            
            # Track game length
            self.engine_stats[white]['game_lengths'].append(move_count)
            self.engine_stats[black]['game_lengths'].append(move_count)
            
            if (game_idx + 1) % 10 == 0:
                print(f"  Analyzed {game_idx + 1}/{len(self.games)} games...", end='\r')
        
        print(f"\n✓ Analysis complete!")
    
    def generate_report(self, output_file: str = None):
        """Generate comprehensive tournament report"""
        report = []
        
        report.append("=" * 80)
        report.append("ULTIMATE ENGINE BATTLE REPORT")
        report.append("90-Minute Classical Tournament Analysis")
        report.append("=" * 80)
        report.append("")
        
        # Tournament overview
        report.append("📊 TOURNAMENT OVERVIEW")
        report.append("-" * 80)
        report.append(f"Total Games: {len(self.games)}")
        report.append(f"Participating Engines: {len(self.engine_stats)}")
        report.append("")
        
        # Rankings by win rate
        rankings = []
        for engine, stats in self.engine_stats.items():
            total = stats['wins'] + stats['losses'] + stats['draws']
            win_rate = (stats['wins'] + 0.5 * stats['draws']) / total if total > 0 else 0
            rankings.append((engine, win_rate, stats))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        report.append("🏆 FINAL STANDINGS (by win rate)")
        report.append("-" * 80)
        report.append(f"{'Rank':<6} {'Engine':<30} {'W-L-D':<15} {'Win%':<10} {'Games':<10}")
        report.append("-" * 80)
        
        for rank, (engine, win_rate, stats) in enumerate(rankings, 1):
            wld = f"{stats['wins']}-{stats['losses']}-{stats['draws']}"
            total = stats['wins'] + stats['losses'] + stats['draws']
            report.append(f"{rank:<6} {engine:<30} {wld:<15} {win_rate*100:>6.1f}% {total:>8}")
        
        report.append("")
        
        # Detailed engine statistics
        report.append("📈 DETAILED ENGINE STATISTICS")
        report.append("=" * 80)
        
        for rank, (engine, win_rate, stats) in enumerate(rankings, 1):
            report.append("")
            report.append(f"#{rank} {engine}")
            report.append("-" * 80)
            
            total = stats['wins'] + stats['losses'] + stats['draws']
            report.append(f"Record: {stats['wins']}-{stats['losses']}-{stats['draws']} ({win_rate*100:.1f}% win rate)")
            report.append(f"As White: {stats['as_white']['wins']}-{stats['as_white']['losses']}-{stats['as_white']['draws']}")
            report.append(f"As Black: {stats['as_black']['wins']}-{stats['as_black']['losses']}-{stats['as_black']['draws']}")
            
            # Depth statistics
            if stats['depths']:
                avg_depth = sum(stats['depths']) / len(stats['depths'])
                max_depth = max(stats['depths'])
                min_depth = min(stats['depths'])
                report.append(f"Search Depth: Avg {avg_depth:.1f} | Max {max_depth} | Min {min_depth}")
            
            # Time statistics
            if stats['times']:
                avg_time = sum(stats['times']) / len(stats['times'])
                total_time_sec = sum(stats['times']) / 1000
                report.append(f"Time Usage: Avg {avg_time:.0f}ms/move | Total {total_time_sec/60:.1f} minutes")
            
            # Game length
            if stats['game_lengths']:
                avg_length = sum(stats['game_lengths']) / len(stats['game_lengths'])
                report.append(f"Avg Game Length: {avg_length:.1f} moves")
            
            # Most common openings
            if stats['openings']:
                top_openings = sorted(stats['openings'].items(), key=lambda x: x[1], reverse=True)[:3]
                report.append("Top Openings:")
                for opening, count in top_openings:
                    report.append(f"  - {opening}: {count} games")
            
            # Opponents beaten/lost to
            if stats['opponents_beaten']:
                report.append(f"Defeated: {', '.join(sorted(stats['opponents_beaten']))}")
            if stats['opponents_lost_to']:
                report.append(f"Lost to: {', '.join(sorted(stats['opponents_lost_to']))}")
        
        report.append("")
        report.append("=" * 80)
        
        # Save report
        report_text = '\n'.join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n📝 Report saved to: {output_file}")
        
        return report_text
    
    def generate_matchup_matrix(self, output_file: str = None):
        """Generate head-to-head matchup matrix"""
        engines = sorted(self.engine_stats.keys())
        
        matrix = []
        matrix.append("\n" + "=" * 80)
        matrix.append("HEAD-TO-HEAD MATCHUP MATRIX")
        matrix.append("=" * 80)
        matrix.append("")
        
        # Header
        header = "Engine".ljust(30)
        for engine in engines:
            # Truncate engine name for display
            short_name = engine[:12]
            header += f"{short_name:>14}"
        matrix.append(header)
        matrix.append("-" * (30 + 14 * len(engines)))
        
        # Rows
        for engine1 in engines:
            row = engine1[:30].ljust(30)
            for engine2 in engines:
                if engine1 == engine2:
                    row += "      -       "
                else:
                    matchup = self.matchups[engine1][engine2]
                    w = matchup['wins']
                    l = matchup['losses']
                    d = matchup['draws']
                    total = w + l + d
                    if total > 0:
                        score = (w + 0.5 * d) / total * 100
                        row += f"  {w}-{l}-{d}({score:>3.0f}%)"
                    else:
                        row += "      -       "
            matrix.append(row)
        
        matrix.append("")
        
        matrix_text = '\n'.join(matrix)
        
        if output_file:
            with open(output_file, 'a') as f:
                f.write(matrix_text)
        
        return matrix_text


def main():
    # Find the PGN file
    pgn_file = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-metrics/raw_data/game_records/Engine Battle 202511/Ultimate Engine Battle 20251108.pgn"
    
    if not Path(pgn_file).exists():
        print(f"❌ PGN file not found: {pgn_file}")
        return
    
    # Create analyzer
    analyzer = UltimateBattleAnalyzer(pgn_file)
    
    # Parse games
    analyzer.parse_pgn()
    
    # Analyze
    analyzer.analyze_games()
    
    # Generate report
    output_dir = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/chess-tournament-analyzer")
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "Ultimate_Engine_Battle_Report_20251108.md"
    
    print("\n" + "=" * 80)
    report = analyzer.generate_report(str(report_file))
    print(report)
    
    matchup_matrix = analyzer.generate_matchup_matrix(str(report_file))
    print(matchup_matrix)
    
    print("\n✅ Analysis complete!")
    print(f"📄 Full report saved to: {report_file}")


if __name__ == "__main__":
    main()
