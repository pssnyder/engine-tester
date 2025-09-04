#!/usr/bin/env python3
"""
V7P3R Historical Game Regression Tester
Comprehensive analysis of multiple V7P3R versions on historical game positions
with Stockfish move quality grading integration
"""

import chess
import chess.pgn
import subprocess
import time
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import threading

@dataclass
class EngineAnalysis:
    """Results from engine analysis of a position"""
    engine_name: str
    move: str
    evaluation: int
    depth: int
    nodes: int
    time_taken: float
    success: bool = True
    error: Optional[str] = None

@dataclass
class StockfishGrade:
    """Stockfish grading of a move"""
    best_move: str
    best_eval: int
    engine_move_eval: int
    move_quality: str  # "excellent", "good", "inaccurate", "mistake", "blunder"
    centipawn_loss: int

@dataclass
class PositionAnalysis:
    """Complete analysis of a position across all engines"""
    position_id: str
    fen: str
    move_number: int
    phase: str
    game_info: Dict[str, str]
    engine_analyses: List[EngineAnalysis]
    stockfish_grade: Optional[StockfishGrade]
    analysis_summary: Dict[str, Any]

class HistoricalGameRegressionTester:
    """Comprehensive regression tester for V7P3R engine versions"""
    
    def __init__(self, engines_dir: str = "engines"):
        self.engines_dir = Path(engines_dir)
        self.engines = self._detect_engines()
        self.stockfish_path = self._detect_stockfish()
        self.results = []
        
    def _detect_engines(self) -> Dict[str, str]:
        """Detect available V7P3R engine versions"""
        engines = {}
        v7p3r_dir = self.engines_dir / "V7P3R"
        
        if v7p3r_dir.exists():
            for exe_file in v7p3r_dir.glob("V7P3R_v*.exe"):
                # Extract version more carefully
                version_part = exe_file.stem.replace("V7P3R_v", "")
                if version_part.endswith(".0"):  # Only .0 versions like v7.0, v8.0, v9.0
                    engines[version_part] = str(exe_file)
        
        # Add our new v9.1 confidence engine
        v9_1_path = self.engines_dir / "V7P3R_v9.1.exe"
        if v9_1_path.exists():
            engines["9.1"] = str(v9_1_path)
        
        return engines
    
    def _detect_stockfish(self) -> Optional[str]:
        """Detect Stockfish executable"""
        possible_paths = [
            self.engines_dir / "Stockfish" / "stockfish-windows-x86-64-avx2.exe",
            Path("stockfish.exe"),
            Path("stockfish")
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def extract_historical_positions(self, pgn_file: str, max_positions: int = 20) -> List[Dict[str, Any]]:
        """Extract key positions from historical games with time control information"""
        positions = []
        
        try:
            with open(pgn_file, 'r') as f:
                game_count = 0
                while len(positions) < max_positions and game_count < 10:  # Limit games processed
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    game_count += 1
                    board = game.board()
                    moves = list(game.mainline_moves())
                    
                    # Get time control from game headers
                    time_control = game.headers.get('TimeControl', '300+5')  # Default 5min+5sec
                    base_time, increment = self._parse_time_control(time_control)
                    
                    # Track time for both players (assume equal time usage)
                    white_time = base_time
                    black_time = base_time
                    
                    # Extract positions at strategic points
                    extract_points = [5, 10, 15, 20, 25]  # Move numbers to extract
                    
                    for i, move in enumerate(moves):
                        board.push(move)
                        move_number = (i + 2) // 2
                        is_white_move = (i % 2) == 0
                        
                        # Estimate time usage (simple heuristic: 3-8 seconds per move)
                        estimated_move_time = min(max(3, move_number * 0.5), 8)
                        if is_white_move:
                            white_time = max(0, white_time - estimated_move_time + increment)
                        else:
                            black_time = max(0, black_time - estimated_move_time + increment)
                        
                        current_time = white_time if board.turn == chess.WHITE else black_time
                        
                        if move_number in extract_points and len(positions) < max_positions:
                            phase = 'opening' if move_number <= 10 else 'middlegame' if move_number <= 25 else 'endgame'
                            
                            positions.append({
                                'id': f"game_{game_count}_move_{move_number}",
                                'fen': board.fen(),
                                'move_number': move_number,
                                'phase': phase,
                                'time_remaining': current_time,
                                'increment': increment,
                                'game_info': {
                                    'white': game.headers.get('White', 'Unknown'),
                                    'black': game.headers.get('Black', 'Unknown'),
                                    'result': game.headers.get('Result', 'Unknown'),
                                    'date': game.headers.get('Date', 'Unknown'),
                                    'time_control': time_control
                                }
                            })
                            
                            if len(positions) >= max_positions:
                                break
        
        except Exception as e:
            print(f"Error extracting positions: {e}")
        
        return positions
    
    def _parse_time_control(self, time_control: str) -> Tuple[float, float]:
        """Parse time control string into base time and increment"""
        try:
            if '+' in time_control:
                base, inc = time_control.split('+')
                return float(base), float(inc)
            else:
                return float(time_control), 0.0
        except:
            return 300.0, 5.0  # Default 5 minutes + 5 seconds
    
    def analyze_position_with_engine(self, engine_path: str, fen: str, time_remaining: float, increment: float = 0.0, retry: bool = False) -> EngineAnalysis:
        """Analyze a position with a specific engine using dynamic time control"""
        engine_name = Path(engine_path).stem.replace("V7P3R_v", "v")
        
        # Calculate time limit based on remaining time
        if time_remaining <= 0:
            time_limit = 1.0  # Minimum time in time trouble
        elif time_remaining < 30:
            time_limit = min(time_remaining * 0.1, 3.0)  # Use 10% of remaining time
        elif time_remaining < 60:
            time_limit = min(time_remaining * 0.15, 5.0)  # Use 15% of remaining time
        else:
            time_limit = min(time_remaining * 0.05 + increment, 8.0)  # Use 5% + increment, max 8s
        
        # On retry, give more time
        if retry:
            time_limit = min(time_limit * 2.0, 15.0)  # Double time on retry, max 15s
        
        try:
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if not process.stdin or not process.stdout:
                return EngineAnalysis(engine_name, "", 0, 0, 0, 0, False, "Could not communicate with engine")
            
            start_time = time.time()
            
            # UCI handshake
            process.stdin.write("uci\n")
            process.stdin.flush()
            
            uci_start = time.time()
            while time.time() - uci_start < 3:
                line = process.stdout.readline().strip()
                if "uciok" in line:
                    break
            else:
                process.terminate()
                return EngineAnalysis(engine_name, "", 0, 0, 0, 0, False, "UCI timeout")
            
            # Set position and search
            process.stdin.write(f"position fen {fen}\n")
            process.stdin.flush()
            
            process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
            process.stdin.flush()
            
            # Collect results
            best_move = ""
            evaluation = 0
            depth = 0
            nodes = 0
            
            search_start = time.time()
            while time.time() - search_start < time_limit + 2:
                line = process.stdout.readline().strip()
                
                if line.startswith("info"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "depth" and i+1 < len(parts):
                            try:
                                depth = max(depth, int(parts[i+1]))
                            except:
                                pass
                        elif part == "score" and i+1 < len(parts):
                            if parts[i+1] == "cp" and i+2 < len(parts):
                                try:
                                    evaluation = int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate" and i+2 < len(parts):
                                try:
                                    mate_in = int(parts[i+2])
                                    evaluation = 900000 if mate_in > 0 else -900000
                                except:
                                    pass
                        elif part == "nodes" and i+1 < len(parts):
                            try:
                                nodes = int(parts[i+1])
                            except:
                                pass
                
                elif line.startswith("bestmove"):
                    best_move = line.split()[1] if len(line.split()) > 1 else ""
                    break
            
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            total_time = time.time() - start_time
            
            success = bool(best_move and best_move != "(none)")
            return EngineAnalysis(engine_name, best_move, evaluation, depth, nodes, total_time, success)
            
        except Exception as e:
            return EngineAnalysis(engine_name, "", 0, 0, 0, 0, False, str(e))
    
    def grade_move_with_stockfish(self, fen: str, engine_move: str, time_limit: float = 2.0) -> Optional[StockfishGrade]:
        """Grade an engine's move using Stockfish"""
        if not self.stockfish_path:
            return None
        
        try:
            process = subprocess.Popen(
                [self.stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if not process.stdin or not process.stdout:
                return None
            
            # UCI handshake
            process.stdin.write("uci\n")
            process.stdin.flush()
            
            uci_start = time.time()
            while time.time() - uci_start < 3:
                line = process.stdout.readline().strip()
                if "uciok" in line:
                    break
            else:
                process.terminate()
                return None
            
            # Get Stockfish's best move
            process.stdin.write(f"position fen {fen}\n")
            process.stdin.flush()
            
            process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
            process.stdin.flush()
            
            best_move = ""
            best_eval = 0
            
            search_start = time.time()
            while time.time() - search_start < time_limit + 2:
                line = process.stdout.readline().strip()
                
                if line.startswith("info"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "score" and i+1 < len(parts):
                            if parts[i+1] == "cp" and i+2 < len(parts):
                                try:
                                    best_eval = int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate" and i+2 < len(parts):
                                try:
                                    mate_in = int(parts[i+2])
                                    best_eval = 900000 if mate_in > 0 else -900000
                                except:
                                    pass
                
                elif line.startswith("bestmove"):
                    best_move = line.split()[1] if len(line.split()) > 1 else ""
                    break
            
            if not engine_move or not best_move:
                process.terminate()
                return None
            
            # Evaluate the engine's move
            board = chess.Board(fen)
            try:
                engine_move_obj = chess.Move.from_uci(engine_move)
                if engine_move_obj not in board.legal_moves:
                    process.terminate()
                    return None
                
                board.push(engine_move_obj)
                
                process.stdin.write(f"position fen {board.fen()}\n")
                process.stdin.flush()
                
                process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
                process.stdin.flush()
                
                engine_move_eval = 0
                
                search_start = time.time()
                while time.time() - search_start < time_limit + 2:
                    line = process.stdout.readline().strip()
                    
                    if line.startswith("info"):
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "score" and i+1 < len(parts):
                                if parts[i+1] == "cp" and i+2 < len(parts):
                                    try:
                                        engine_move_eval = -int(parts[i+2])  # Flip evaluation (opponent's perspective)
                                    except:
                                        pass
                                elif parts[i+1] == "mate" and i+2 < len(parts):
                                    try:
                                        mate_in = int(parts[i+2])
                                        engine_move_eval = -900000 if mate_in > 0 else 900000
                                    except:
                                        pass
                    
                    elif line.startswith("bestmove"):
                        break
                
            except Exception:
                process.terminate()
                return None
            
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            
            # Calculate centipawn loss and quality
            centipawn_loss = best_eval - engine_move_eval
            
            if engine_move.lower() == best_move.lower():
                quality = "excellent"
            elif centipawn_loss <= 10:
                quality = "excellent"
            elif centipawn_loss <= 25:
                quality = "good"
            elif centipawn_loss <= 50:
                quality = "inaccurate"
            elif centipawn_loss <= 100:
                quality = "mistake"
            else:
                quality = "blunder"
            
            return StockfishGrade(best_move, best_eval, engine_move_eval, quality, centipawn_loss)
            
        except Exception as e:
            return None
    
    def analyze_with_retry(self, engine_path: str, fen: str, time_remaining: float, increment: float = 0.0) -> EngineAnalysis:
        """Analyze position with retry logic for failed engines"""
        # First attempt
        result = self.analyze_position_with_engine(engine_path, fen, time_remaining, increment, retry=False)
        
        # If failed or returned no move, retry with more time
        if result.error or not result.move or result.move == "(none)":
            print(f"    Retrying {Path(engine_path).stem} with extended time...")
            result = self.analyze_position_with_engine(engine_path, fen, time_remaining, increment, retry=True)
        
        # If still failed and it's a critical failure, use Stockfish grading to check if it's worth another retry
        if result.error and self.stockfish_path and time_remaining > 10:
            # Quick Stockfish check to see if this is a complex position
            sf_grade = self.grade_move_with_stockfish(fen, "e2e4", 1.0)  # Dummy move for complexity check
            if sf_grade and abs(sf_grade.best_eval) > 200:  # Complex position
                print(f"    Complex position detected, final retry for {Path(engine_path).stem}...")
                result = self.analyze_position_with_engine(engine_path, fen, max(time_remaining * 0.5, 5.0), increment, retry=True)
        
        return result
    
    def analyze_position_comprehensive(self, position: Dict[str, Any]) -> PositionAnalysis:
        """Analyze a position with all engines using dynamic time controls and retry logic"""
        print(f"\n--- Analyzing Position: {position['id']} ---")
        print(f"Move {position['move_number']} ({position['phase']})")
        print(f"Game: {position['game_info']['white']} vs {position['game_info']['black']}")
        print(f"Time remaining: {position['time_remaining']:.1f}s")
        print(f"FEN: {position['fen'][:60]}...")
        
        engine_analyses = []
        
        # Get time control info
        time_remaining = position.get('time_remaining', 60.0)
        increment = position.get('increment', 0.0)
        
        # Analyze with each engine using dynamic time controls
        for version, engine_path in self.engines.items():
            print(f"  Testing {version}...", end=" ")
            analysis = self.analyze_with_retry(engine_path, position['fen'], time_remaining, increment)
            engine_analyses.append(analysis)
            
            if analysis.error:
                print(f"Error: {analysis.error}")
            else:
                print(f"Move: {analysis.move} | Eval: {analysis.evaluation:+d} cp | Depth: {analysis.depth} | Time: {analysis.time_taken:.1f}s")
        
        # Stockfish grading (use the first successful engine move for grading)
        stockfish_grade = None
        successful_analysis = next((a for a in engine_analyses if a.success and a.move), None)
        
        if successful_analysis and self.stockfish_path:
            print(f"  Stockfish grading...", end=" ")
            stockfish_grade = self.grade_move_with_stockfish(position['fen'], successful_analysis.move, 2.0)
            
            if stockfish_grade:
                print(f"Best: {stockfish_grade.best_move} | Quality: {stockfish_grade.move_quality} | Loss: {stockfish_grade.centipawn_loss} cp")
            else:
                print("Failed")
        
        # Analysis summary
        successful_engines = [a for a in engine_analyses if a.success]
        moves = set(a.move for a in successful_engines if a.move)
        
        summary = {
            'successful_engines': len(successful_engines),
            'total_engines': len(engine_analyses),
            'move_agreement': len(moves) <= 1,  # All engines chose same move
            'unique_moves': len(moves),
            'average_depth': sum(a.depth for a in successful_engines) / len(successful_engines) if successful_engines else 0,
            'average_time': sum(a.time_taken for a in successful_engines) / len(successful_engines) if successful_engines else 0
        }
        
        return PositionAnalysis(
            position['id'], position['fen'], position['move_number'], position['phase'],
            position['game_info'], engine_analyses, stockfish_grade, summary
        )
    
    def run_comprehensive_analysis(self, pgn_file: str, max_positions: int = 15) -> List[PositionAnalysis]:
        """Run comprehensive analysis on historical game positions with dynamic time controls"""
        
        print("=" * 80)
        print("V7P3R HISTORICAL GAME REGRESSION ANALYSIS")
        print("=" * 80)
        
        print(f"Detected engines: {list(self.engines.keys())}")
        print(f"Stockfish available: {'Yes' if self.stockfish_path else 'No'}")
        print(f"PGN file: {pgn_file}")
        print(f"Max positions: {max_positions}")
        print(f"Time controls: Dynamic based on game time remaining")
        
        # Extract positions
        print(f"\nExtracting positions from {pgn_file}...")
        positions = self.extract_historical_positions(pgn_file, max_positions)
        
        if not positions:
            print("No positions extracted!")
            return []
        
        print(f"Extracted {len(positions)} positions for analysis")
        
        # Analyze each position
        results = []
        for i, position in enumerate(positions, 1):
            print(f"\n{'='*60}")
            print(f"POSITION {i}/{len(positions)}")
            print(f"{'='*60}")
            
            analysis = self.analyze_position_comprehensive(position)
            results.append(analysis)
            
            # Brief pause between positions
            time.sleep(0.5)
        
        self.results = results
        return results
    
    def generate_regression_report(self) -> Dict[str, Any]:
        """Generate comprehensive regression analysis report"""
        if not self.results:
            return {}
        
        report = {
            'summary': {
                'total_positions': len(self.results),
                'engines_tested': list(self.engines.keys()),
                'stockfish_graded': sum(1 for r in self.results if r.stockfish_grade),
                'timestamp': datetime.now().isoformat()
            },
            'engine_performance': {},
            'move_quality_analysis': {},
            'regression_analysis': {},
            'phase_performance': {},
            'detailed_results': []
        }
        
        # Engine performance analysis
        for engine_version in self.engines.keys():
            engine_results = []
            for result in self.results:
                engine_analysis = next((a for a in result.engine_analyses if a.engine_name == engine_version), None)
                if engine_analysis:
                    engine_results.append(engine_analysis)
            
            successful = [r for r in engine_results if r.success]
            
            report['engine_performance'][engine_version] = {
                'success_rate': len(successful) / len(engine_results) if engine_results else 0,
                'average_depth': sum(r.depth for r in successful) / len(successful) if successful else 0,
                'average_time': sum(r.time_taken for r in successful) / len(successful) if successful else 0,
                'average_nodes': sum(r.nodes for r in successful) / len(successful) if successful else 0,
                'total_positions': len(engine_results),
                'successful_positions': len(successful)
            }
        
        # Move quality analysis (if Stockfish grading available)
        stockfish_graded = [r for r in self.results if r.stockfish_grade]
        if stockfish_graded:
            quality_counts = {}
            
            for result in stockfish_graded:
                quality = result.stockfish_grade.move_quality
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            report['move_quality_analysis'] = {
                'total_graded': len(stockfish_graded),
                'quality_distribution': quality_counts,
                'average_centipawn_loss': sum(r.stockfish_grade.centipawn_loss for r in stockfish_graded) / len(stockfish_graded),
                'excellent_moves': quality_counts.get('excellent', 0),
                'blunders': quality_counts.get('blunder', 0)
            }
        
        # Phase performance
        for phase in ['opening', 'middlegame', 'endgame']:
            phase_results = [r for r in self.results if r.phase == phase]
            if phase_results:
                report['phase_performance'][phase] = {
                    'total_positions': len(phase_results),
                    'engine_agreement': sum(1 for r in phase_results if r.analysis_summary['move_agreement']),
                    'average_depth': sum(r.analysis_summary['average_depth'] for r in phase_results) / len(phase_results),
                    'successful_analyses': sum(r.analysis_summary['successful_engines'] for r in phase_results)
                }
        
        # Convert results to dictionaries for JSON serialization
        for result in self.results:
            result_dict = asdict(result)
            report['detailed_results'].append(result_dict)
        
        return report
    
    def print_regression_summary(self, report: Dict[str, Any]):
        """Print a comprehensive regression analysis summary"""
        print("\n" + "=" * 80)
        print("REGRESSION ANALYSIS SUMMARY")
        print("=" * 80)
        
        summary = report['summary']
        print(f"📊 Total Positions Analyzed: {summary['total_positions']}")
        print(f"🤖 Engines Tested: {', '.join(summary['engines_tested'])}")
        print(f"⭐ Stockfish Graded: {summary['stockfish_graded']}")
        
        # Engine performance comparison
        print(f"\n🏆 ENGINE PERFORMANCE COMPARISON:")
        engine_perf = report['engine_performance']
        
        for version, perf in sorted(engine_perf.items()):
            success_rate = perf['success_rate'] * 100
            avg_depth = perf['average_depth']
            avg_time = perf['average_time']
            
            print(f"  {version}: {success_rate:.1f}% success | Depth: {avg_depth:.1f} | Time: {avg_time:.2f}s")
        
        # Move quality analysis
        if 'move_quality_analysis' in report and report['move_quality_analysis']:
            print(f"\n⭐ MOVE QUALITY ANALYSIS (Stockfish Graded):")
            quality = report['move_quality_analysis']
            
            print(f"  Total Graded: {quality['total_graded']}")
            print(f"  Average Centipawn Loss: {quality['average_centipawn_loss']:.1f}")
            print(f"  Quality Distribution:")
            
            for q_type, count in quality['quality_distribution'].items():
                percentage = (count / quality['total_graded']) * 100
                print(f"    {q_type.capitalize()}: {count} ({percentage:.1f}%)")
        
        # Phase performance
        if 'phase_performance' in report:
            print(f"\n📈 PERFORMANCE BY GAME PHASE:")
            
            for phase, perf in report['phase_performance'].items():
                agreement_rate = (perf['engine_agreement'] / perf['total_positions']) * 100
                avg_depth = perf['average_depth']
                
                print(f"  {phase.capitalize()}: {perf['total_positions']} positions | Agreement: {agreement_rate:.1f}% | Avg Depth: {avg_depth:.1f}")
        
        # Regression insights
        print(f"\n🔍 REGRESSION INSIGHTS:")
        
        # Version comparison
        versions = list(engine_perf.keys())
        if 'v9.1' in versions and 'v9.0' in versions:
            v91_success = engine_perf['v9.1']['success_rate']
            v90_success = engine_perf['v9.0']['success_rate']
            improvement = (v91_success - v90_success) * 100
            
            if improvement > 0:
                print(f"  ✅ v9.1 Confidence System: +{improvement:.1f}% improvement over v9.0")
            else:
                print(f"  ⚠️  v9.1 Confidence System: {improvement:.1f}% change from v9.0")
        
        # Historical comparison
        if 'v7.0' in versions and 'v9.1' in versions:
            v70_success = engine_perf['v7.0']['success_rate']
            v91_success = engine_perf['v9.1']['success_rate']
            total_improvement = (v91_success - v70_success) * 100
            
            print(f"  📈 Overall Progress (v7.0 → v9.1): +{total_improvement:.1f}% improvement")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"  • Analyze detailed move quality for specific improvements")
        print(f"  • Focus testing on phases with low agreement rates")
        print(f"  • Tournament validation of v9.1 confidence system")

def main():
    """Run comprehensive historical game regression analysis"""
    
    # Configuration
    pgn_file = "../engine-metrics/game_records/Engine Battle 20250829/Engine Regression Battle 20250829.pgn"
    max_positions = 15
    
    # Initialize tester
    tester = HistoricalGameRegressionTester()
    
    if not tester.engines:
        print("No V7P3R engines found!")
        return
    
    # Run analysis
    results = tester.run_comprehensive_analysis(pgn_file, max_positions)
    
    if not results:
        print("No analysis results generated!")
        return
    
    # Generate report
    report = tester.generate_regression_report()
    
    # Print summary
    tester.print_regression_summary(report)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"v7p3r_regression_analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")
    print("🎉 Historical game regression analysis complete!")

if __name__ == "__main__":
    main()
