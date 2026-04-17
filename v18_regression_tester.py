#!/usr/bin/env python3
"""
V7P3R v18.3 vs v18.4 Regression Testing Suite
Extracts critical positions from v18.3 losses and tests both versions

This script:
1. Parses 2026 v7p3r_bot games from Lichess PGN
2. Identifies lost games for v7p3r_bot
3. Uses Stockfish to analyze and find critical mistake positions
4. Tests both v18.3 and v18.4 on those positions
5. Generates a comprehensive comparison report
"""

import chess
import chess.pgn
import chess.engine
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import io

@dataclass
class CriticalPosition:
    """A position where v18.3 made a significant mistake"""
    fen: str
    game_url: str
    move_number: int
    evaluation_drop: float  # Centipawn loss
    stockfish_best_move: str
    v18_3_move: str
    description: str
    game_phase: str  # opening, middlegame, endgame

@dataclass
class EngineTestResult:
    """Result of testing an engine on a position"""
    engine_version: str
    position_fen: str
    best_move: str
    evaluation: Optional[float]
    depth: int
    nodes: int
    time_ms: int
    agrees_with_stockfish: bool
    centipawn_loss: float

@dataclass
class ComparisonReport:
    """Overall comparison report"""
    test_date: str
    v18_3_path: str
    v18_4_path: str
    stockfish_path: str
    total_positions_tested: int
    v18_3_stockfish_agreements: int
    v18_4_stockfish_agreements: int
    v18_3_avg_cp_loss: float
    v18_4_avg_cp_loss: float
    improvement_percentage: float
    positions: List[Dict]
    summary: str


class V18RegressionTester:
    """Test suite for comparing V7P3R v18.3 and v18.4"""
    
    def __init__(self, 
                 pgn_path: str,
                 v18_3_path: str,
                 v18_4_path: str,
                 stockfish_path: str = None,
                 cache_dir: str = None):
        self.pgn_path = Path(pgn_path)
        self.v18_3_path = Path(v18_3_path)
        self.v18_4_path = Path(v18_4_path)
        
        # Default Stockfish path if not provided
        if stockfish_path is None:
            self.stockfish_path = Path(r"E:\Programming Stuff\Chess Engines\Tournament Engines\Stockfish\stockfish-windows-x86-64-avx2.exe")
        else:
            self.stockfish_path = Path(stockfish_path)
        
        # Set up cache directory
        if cache_dir is None:
            self.cache_dir = Path(r"e:\Programming Stuff\Chess Engines\Chess Engine Playground\engine-metrics\raw_data\analysis_results") / ".cache"
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        self.critical_positions: List[CriticalPosition] = []
        self.test_results: List[Dict] = []
        
    def parse_lost_games_2026(self) -> List[chess.pgn.Game]:
        """Extract all games from 2026 where v7p3r_bot lost"""
        print(f"\n{'='*70}")
        print("STEP 1: Parsing PGN for v18.3 Lost Games (2026)")
        print(f"{'='*70}")
        
        lost_games = []
        
        with open(self.pgn_path, 'r', encoding='utf-8', errors='ignore') as pgn_file:
            game_count = 0
            lost_count = 0
            
            while True:
                try:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    
                    game_count += 1
                    
                    # Check if game is from 2026
                    date = game.headers.get("Date", "")
                    if not date.startswith("2026"):
                        continue
                    
                    # Check if v7p3r_bot played and lost
                    white = game.headers.get("White", "")
                    black = game.headers.get("Black", "")
                    result = game.headers.get("Result", "")
                    
                    is_v7p3r_white = "v7p3r" in white.lower()
                    is_v7p3r_black = "v7p3r" in black.lower()
                    
                    if is_v7p3r_white and result == "0-1":
                        lost_games.append(game)
                        lost_count += 1
                        print(f"  Found loss #{lost_count}: {white} vs {black} on {date}")
                    elif is_v7p3r_black and result == "1-0":
                        lost_games.append(game)
                        lost_count += 1
                        print(f"  Found loss #{lost_count}: {white} vs {black} on {date}")
                        
                except Exception as e:
                    print(f"  Warning: Error parsing game: {e}")
                    continue
        
        print(f"\n  Total games parsed: {game_count}")
        print(f"  v7p3r_bot losses in 2026: {lost_count}")
        return lost_games
    
    def analyze_game_with_stockfish(self, game: chess.pgn.Game, max_positions: int = 5) -> List[CriticalPosition]:
        """Analyze a game with Stockfish to find critical mistake positions"""
        
        critical_positions = []
        board = game.board()
        
        white = game.headers.get("White", "")
        is_v7p3r_white = "v7p3r" in white.lower()
        game_url = game.headers.get("Site", "")
        
        try:
            with chess.engine.SimpleEngine.popen_uci(str(self.stockfish_path)) as engine:
                move_number = 1
                previous_eval = None
                
                for node in game.mainline():
                    move = node.move
                    
                    # Only analyze v7p3r's moves
                    is_v7p3r_turn = (board.turn == chess.WHITE and is_v7p3r_white) or \
                                   (board.turn == chess.BLACK and not is_v7p3r_white)
                    
                    if is_v7p3r_turn:
                        # Get evaluation before the move
                        info_before = engine.analyse(board, chess.engine.Limit(depth=18))
                        eval_before = info_before["score"].relative.score(mate_score=10000)
                        
                        # Get best move according to Stockfish
                        best_move = info_before.get("pv", [None])[0]
                        
                        # Make the actual move
                        board.push(move)
                        
                        # Get evaluation after the move
                        info_after = engine.analyse(board, chess.engine.Limit(depth=18))
                        eval_after = info_after["score"].relative.score(mate_score=10000)
                        
                        # Calculate centipawn loss (from opponent's perspective, flip sign)
                        if eval_before is not None and eval_after is not None:
                            cp_loss = -(eval_after - eval_before)  # Negative because perspective flips
                            
                            # If this is a significant blunder (>50cp loss) - lowered threshold for more sensitivity
                            if cp_loss > 50 and best_move is not None:
                                # Determine game phase
                                phase = self._determine_game_phase(board)
                                
                                # Get FEN before the move
                                board.pop()  # Go back
                                fen_before = board.fen()
                                board.push(move)  # Re-apply
                                
                                critical_pos = CriticalPosition(
                                    fen=fen_before,
                                    game_url=game_url,
                                    move_number=move_number,
                                    evaluation_drop=cp_loss,
                                    stockfish_best_move=best_move.uci(),
                                    v18_3_move=move.uci(),
                                    description=f"Move {move_number}: {move.uci()} (loss: {cp_loss:.0f}cp)",
                                    game_phase=phase
                                )
                                critical_positions.append(critical_pos)
                                
                                print(f"    Move {move_number}: Blunder detected! "
                                      f"Played {move.uci()}, best was {best_move.uci()} "
                                      f"(loss: {cp_loss:.0f}cp)")
                        
                        previous_eval = eval_after
                    else:
                        # Just make opponent's move
                        board.push(move)
                    
                    if board.turn == chess.WHITE:
                        move_number += 1
                    
                    # Stop if we have enough positions
                    if len(critical_positions) >= max_positions:
                        break
                        
        except Exception as e:
            print(f"    Error analyzing game: {e}")
        
        return critical_positions
    
    def _determine_game_phase(self, board: chess.Board) -> str:
        """Determine if position is opening, middlegame, or endgame"""
        move_count = board.fullmove_number
        
        # Count pieces
        piece_count = len(board.piece_map())
        
        if move_count < 10:
            return "opening"
        elif piece_count <= 10:
            return "endgame"
        else:
            return "middlegame"
    
    def extract_critical_positions(self, max_games: int = 10, positions_per_game: int = 3) -> List[CriticalPosition]:
        """Extract critical mistake positions from lost games"""
        print(f"\n{'='*70}")
        print("STEP 2: Analyzing Games with Stockfish")
        print(f"{'='*70}")
        
        lost_games = self.parse_lost_games_2026()
        
        # Limit number of games to analyze
        games_to_analyze = lost_games[:max_games]
        print(f"\nAnalyzing {len(games_to_analyze)} games for critical positions...")
        
        all_critical_positions = []
        
        for idx, game in enumerate(games_to_analyze, 1):
            white = game.headers.get("White", "")
            black = game.headers.get("Black", "")
            date = game.headers.get("Date", "")
            
            print(f"\n  Game {idx}/{len(games_to_analyze)}: {white} vs {black} ({date})")
            
            positions = self.analyze_game_with_stockfish(game, max_positions=positions_per_game)
            all_critical_positions.extend(positions)
            
            print(f"    Found {len(positions)} critical positions")
        
        # Sort by evaluation drop (worst mistakes first)
        all_critical_positions.sort(key=lambda p: p.evaluation_drop, reverse=True)
        
        print(f"\n  Total critical positions extracted: {len(all_critical_positions)}")
        self.critical_positions = all_critical_positions
        
        return all_critical_positions
    
    def get_cache_filename(self, max_games: int, positions_per_game: int) -> Path:
        """Generate cache filename based on PGN file and parameters"""
        pgn_name = self.pgn_path.stem
        cache_name = f"critical_positions_{pgn_name}_g{max_games}_p{positions_per_game}.json"
        return self.cache_dir / cache_name
    
    def save_positions_to_cache(self, positions: List[CriticalPosition], max_games: int, positions_per_game: int):
        """Save critical positions to cache file"""
        cache_file = self.get_cache_filename(max_games, positions_per_game)
        
        cache_data = {
            "metadata": {
                "pgn_file": str(self.pgn_path),
                "max_games": max_games,
                "positions_per_game": positions_per_game,
                "total_positions": len(positions),
                "generated_at": datetime.now().isoformat(),
                "stockfish_path": str(self.stockfish_path)
            },
            "positions": [asdict(p) for p in positions]
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"\n💾 Cache saved: {cache_file}")
        print(f"   {len(positions)} positions cached for future runs")
    
    def load_positions_from_cache(self, max_games: int, positions_per_game: int) -> Optional[List[CriticalPosition]]:
        """Load critical positions from cache if available"""
        cache_file = self.get_cache_filename(max_games, positions_per_game)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Validate cache metadata
            metadata = cache_data.get("metadata", {})
            if metadata.get("pgn_file") != str(self.pgn_path):
                print("\n⚠️  Cache PGN mismatch, re-analyzing...")
                return None
            
            # Convert dict back to CriticalPosition objects
            positions = [CriticalPosition(**p) for p in cache_data["positions"]]
            
            print(f"\n📦 Loaded {len(positions)} positions from cache")
            print(f"   Cache file: {cache_file}")
            print(f"   Generated: {metadata.get('generated_at', 'unknown')}")
            print(f"   ⚡ Skipping Stockfish analysis (saved ~60+ seconds)")
            
            return positions
            
        except Exception as e:
            print(f"\n⚠️  Cache load failed: {e}")
            print("   Re-analyzing games with Stockfish...")
            return None
    
    def test_engine_on_position(self, engine_path: Path, position: CriticalPosition, 
                                 time_limit: float = 3.0) -> EngineTestResult:
        """Test a single engine on a position using direct subprocess for .bat compatibility"""
        
        version = "v18.3" if "18.3" in str(engine_path) else "v18.4"
        
        try:
            # Detect engine type (.bat vs .exe)
            is_bat = str(engine_path).lower().endswith('.bat')
            
            if is_bat:
                # For .bat files, use cmd.exe wrapper with proper working directory
                cmd = ['cmd.exe', '/c', str(engine_path)]
                cwd = str(engine_path.parent)
            else:
                cmd = [str(engine_path)]
                cwd = None
            
            # Use subprocess for direct UCI communication (more reliable for .bat)
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=cwd
            )
            
            # UCI handshake
            proc.stdin.write("uci\n")
            proc.stdin.flush()
            
            # Wait for uciok
            uci_ready = False
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if "uciok" in line:
                    uci_ready = True
                    break
            
            if not uci_ready:
                raise Exception("Engine did not respond to UCI")
            
            # Set position
            proc.stdin.write(f"position fen {position.fen}\n")
            proc.stdin.flush()
            
            # Start search
            proc.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
            proc.stdin.flush()
            
            # Parse engine output
            best_move = None
            evaluation = None
            depth = 0
            nodes = 0
            
            import time
            start_time = time.time()
            timeout = time_limit + 3.0
            
            while time.time() - start_time < timeout:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                
                if "bestmove" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        best_move = parts[1]
                    break
                    
                elif "info" in line and "depth" in line:
                    parts = line.split()
                    try:
                        if "depth" in parts:
                            depth_idx = parts.index("depth")
                            if depth_idx + 1 < len(parts):
                                depth = max(depth, int(parts[depth_idx + 1]))
                        
                        if "score" in parts and "cp" in parts:
                            cp_idx = parts.index("cp")
                            if cp_idx + 1 < len(parts):
                                evaluation = int(parts[cp_idx + 1])
                        elif "score" in parts and "mate" in parts:
                            mate_idx = parts.index("mate")
                            if mate_idx + 1 < len(parts):
                                mate_in = int(parts[mate_idx + 1])
                                evaluation = 10000 if mate_in > 0 else -10000
                        
                        if "nodes" in parts:
                            nodes_idx = parts.index("nodes")
                            if nodes_idx + 1 < len(parts):
                                nodes = int(parts[nodes_idx + 1])
                    except (ValueError, IndexError):
                        pass
            
            # Clean up
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.terminate()
            try:
                proc.wait(timeout=1.0)
            except:
                proc.kill()
            
            # Check if move agrees with Stockfish
            agrees_with_stockfish = (best_move == position.stockfish_best_move)
            
            # Calculate centipawn loss
            cp_loss = 0.0 if agrees_with_stockfish else position.evaluation_drop
            
            return EngineTestResult(
                engine_version=version,
                position_fen=position.fen,
                best_move=best_move or "none",
                evaluation=evaluation,
                depth=depth,
                nodes=nodes,
                time_ms=int(time_limit * 1000),
                agrees_with_stockfish=agrees_with_stockfish,
                centipawn_loss=cp_loss
            )
            
        except Exception as e:
            print(f"    Error testing engine: {e}")
            import traceback
            traceback.print_exc()
            return EngineTestResult(
                engine_version=version,
                position_fen=position.fen,
                best_move="error",
                evaluation=0,
                depth=0,
                nodes=0,
                time_ms=0,
                agrees_with_stockfish=False,
                centipawn_loss=position.evaluation_drop
            )
    
    def run_comparison_tests(self, time_per_position: float = 5.0) -> ComparisonReport:
        """Run comparison tests on all critical positions"""
        print(f"\n{'='*70}")
        print("STEP 3: Testing Both Engine Versions")
        print(f"{'='*70}")
        
        if not self.critical_positions:
            print("  No critical positions to test!")
            return None
        
        print(f"\nTesting {len(self.critical_positions)} positions...")
        print(f"Time per position: {time_per_position}s")
        print(f"v18.3: {self.v18_3_path}")
        print(f"v18.4: {self.v18_4_path}")
        
        v18_3_agreements = 0
        v18_4_agreements = 0
        v18_3_cp_losses = []
        v18_4_cp_losses = []
        
        position_results = []
        
        for idx, position in enumerate(self.critical_positions, 1):
            print(f"\n  Position {idx}/{len(self.critical_positions)}: "
                  f"Move {position.move_number} ({position.game_phase})")
            print(f"    Original mistake: {position.v18_3_move} (loss: {position.evaluation_drop:.0f}cp)")
            print(f"    Stockfish best: {position.stockfish_best_move}")
            
            # Test v18.3
            print(f"    Testing v18.3...", end=" ", flush=True)
            result_18_3 = self.test_engine_on_position(self.v18_3_path, position, time_per_position)
            print(f"Move: {result_18_3.best_move} (depth {result_18_3.depth})")
            
            # Test v18.4
            print(f"    Testing v18.4...", end=" ", flush=True)
            result_18_4 = self.test_engine_on_position(self.v18_4_path, position, time_per_position)
            print(f"Move: {result_18_4.best_move} (depth {result_18_4.depth})")
            
            # Track statistics
            if result_18_3.agrees_with_stockfish:
                v18_3_agreements += 1
                print(f"    ✓ v18.3 agrees with Stockfish!")
            
            if result_18_4.agrees_with_stockfish:
                v18_4_agreements += 1
                print(f"    ✓ v18.4 agrees with Stockfish!")
            
            if result_18_4.agrees_with_stockfish and not result_18_3.agrees_with_stockfish:
                print(f"    🎯 v18.4 FIXED THIS BLUNDER!")
            elif not result_18_4.agrees_with_stockfish and result_18_3.agrees_with_stockfish:
                print(f"    ⚠️  v18.4 BROKE THIS POSITION!")
            
            v18_3_cp_losses.append(result_18_3.centipawn_loss)
            v18_4_cp_losses.append(result_18_4.centipawn_loss)
            
            # Store results
            position_results.append({
                "position": asdict(position),
                "v18_3_result": asdict(result_18_3),
                "v18_4_result": asdict(result_18_4)
            })
        
        # Calculate overall statistics
        v18_3_avg_cp = sum(v18_3_cp_losses) / len(v18_3_cp_losses) if v18_3_cp_losses else 0
        v18_4_avg_cp = sum(v18_4_cp_losses) / len(v18_4_cp_losses) if v18_4_cp_losses else 0
        
        improvement = ((v18_3_avg_cp - v18_4_avg_cp) / v18_3_avg_cp * 100) if v18_3_avg_cp > 0 else 0
        
        # Generate summary
        summary_lines = [
            f"V7P3R v18.3 vs v18.4 Regression Test Results",
            f"=" * 70,
            f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Positions Tested: {len(self.critical_positions)}",
            f"",
            f"Stockfish Agreement:",
            f"  v18.3: {v18_3_agreements}/{len(self.critical_positions)} ({v18_3_agreements/len(self.critical_positions)*100:.1f}%)",
            f"  v18.4: {v18_4_agreements}/{len(self.critical_positions)} ({v18_4_agreements/len(self.critical_positions)*100:.1f}%)",
            f"",
            f"Average Centipawn Loss:",
            f"  v18.3: {v18_3_avg_cp:.1f}cp",
            f"  v18.4: {v18_4_avg_cp:.1f}cp",
            f"",
            f"Improvement: {improvement:+.1f}%",
            f"",
        ]
        
        if v18_4_agreements > v18_3_agreements:
            summary_lines.append(f"✅ RECOMMENDATION: v18.4 shows improvement, safe to deploy")
        elif v18_4_agreements < v18_3_agreements:
            summary_lines.append(f"⚠️  WARNING: v18.4 shows regression, review before deployment")
        else:
            summary_lines.append(f"ℹ️  NEUTRAL: v18.4 shows no significant change")
        
        summary = "\n".join(summary_lines)
        
        report = ComparisonReport(
            test_date=datetime.now().isoformat(),
            v18_3_path=str(self.v18_3_path),
            v18_4_path=str(self.v18_4_path),
            stockfish_path=str(self.stockfish_path),
            total_positions_tested=len(self.critical_positions),
            v18_3_stockfish_agreements=v18_3_agreements,
            v18_4_stockfish_agreements=v18_4_agreements,
            v18_3_avg_cp_loss=v18_3_avg_cp,
            v18_4_avg_cp_loss=v18_4_avg_cp,
            improvement_percentage=improvement,
            positions=position_results,
            summary=summary
        )
        
        return report
    
    def save_report(self, report: ComparisonReport, output_path: str = None):
        """Save the comparison report to JSON and markdown files"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"v18_regression_report_{timestamp}"
        
        output_path = Path(output_path)
        
        # Save JSON
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2)
        print(f"\n✓ JSON report saved: {json_path}")
        
        # Save Markdown
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report.summary)
            f.write("\n\n## Detailed Position Analysis\n\n")
            
            for idx, pos_result in enumerate(report.positions, 1):
                pos = pos_result["position"]
                v3 = pos_result["v18_3_result"]
                v4 = pos_result["v18_4_result"]
                
                f.write(f"### Position {idx}: {pos['description']}\n\n")
                f.write(f"- **Game**: {pos['game_url']}\n")
                f.write(f"- **Phase**: {pos['game_phase']}\n")
                f.write(f"- **FEN**: `{pos['fen']}`\n")
                f.write(f"- **Original mistake**: {pos['v18_3_move']} (loss: {pos['evaluation_drop']:.0f}cp)\n")
                f.write(f"- **Stockfish best**: {pos['stockfish_best_move']}\n\n")
                f.write(f"**v18.3 Result:**\n")
                f.write(f"- Move: {v3['best_move']}\n")
                f.write(f"- Depth: {v3['depth']}\n")
                f.write(f"- Agrees with Stockfish: {'✓' if v3['agrees_with_stockfish'] else '✗'}\n\n")
                f.write(f"**v18.4 Result:**\n")
                f.write(f"- Move: {v4['best_move']}\n")
                f.write(f"- Depth: {v4['depth']}\n")
                f.write(f"- Agrees with Stockfish: {'✓' if v4['agrees_with_stockfish'] else '✗'}\n\n")
                
                if v4['agrees_with_stockfish'] and not v3['agrees_with_stockfish']:
                    f.write(f"**🎯 v18.4 FIXED THIS POSITION!**\n\n")
                elif not v4['agrees_with_stockfish'] and v3['agrees_with_stockfish']:
                    f.write(f"**⚠️ v18.4 REGRESSED ON THIS POSITION!**\n\n")
                
                f.write("---\n\n")
        
        print(f"✓ Markdown report saved: {md_path}")
        
        return json_path, md_path


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='V7P3R v18.3 vs v18.4 Regression Testing')
    parser.add_argument('--force-reanalyze', action='store_true', 
                       help='Force re-analysis with Stockfish, ignore cache')
    parser.add_argument('--max-games', type=int, default=10,
                       help='Number of lost games to analyze (default: 10)')
    parser.add_argument('--positions-per-game', type=int, default=3,
                       help='Critical positions to extract per game (default: 3)')
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print("V7P3R v18.3 vs v18.4 REGRESSION TESTING SUITE")
    print(f"{'='*70}")
    
    # Configuration
    pgn_path = r"e:\Programming Stuff\Chess Engines\Chess Engine Playground\engine-metrics\raw_data\game_records\Lichess V7P3R Bot\lichess_v7p3r_bot_2026-04-09.pgn"
    v18_3_path = r"E:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\lichess\engines\V7P3R_v18.3_20251229\V7P3R_v18.3.bat"
    v18_4_path = r"E:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\development\V7P3R_v18.4_20260415\V7P3R_v18.4.bat"
    
    # Create tester
    tester = V18RegressionTester(
        pgn_path=pgn_path,
        v18_3_path=v18_3_path,
        v18_4_path=v18_4_path
    )
    
    # Try to load from cache first (unless forced to reanalyze)
    positions = None
    if not args.force_reanalyze:
        positions = tester.load_positions_from_cache(
            max_games=args.max_games,
            positions_per_game=args.positions_per_game
        )
    
    # Extract critical positions from lost games (if not cached)
    if positions is None:
        positions = tester.extract_critical_positions(
            max_games=args.max_games,
            positions_per_game=args.positions_per_game
        )
        
        # Save to cache for future runs
        if positions:
            tester.save_positions_to_cache(positions, args.max_games, args.positions_per_game)
    
    if not positions:
        print("\n❌ No critical positions found. Exiting.")
        return
    
    # Run comparison tests
    report = tester.run_comparison_tests(time_per_position=5.0)
    
    # Print summary
    print(f"\n{'='*70}")
    print("FINAL REPORT")
    print(f"{'='*70}")
    print(report.summary)
    
    # Save reports
    output_dir = Path(r"e:\Programming Stuff\Chess Engines\Chess Engine Playground\engine-metrics\raw_data\analysis_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"v18_regression_test_{timestamp}"
    
    tester.save_report(report, str(output_path))
    
    print(f"\n{'='*70}")
    print("Testing Complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
