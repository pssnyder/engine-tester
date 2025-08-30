#!/usr/bin/env python3
"""
V7P3R Positional Analysis Tool with Stockfish Validation
========================================================

This tool performs comprehensive positional analysis by:
1. Extracting positions from historical games
2. Testing multiple engine versions on each position  
3. Using Stockfish to evaluate move quality objectively
4. Generating detailed comparison reports

Features:
- PGN game parsing and position extraction
- Multi-engine comparison (v7.0, v8.0, v9.0, v9.1)
- Stockfish move quality validation
- Performance metrics (time, depth, nodes)
- Move decision analysis and regression detection
"""

import chess
import chess.pgn
import chess.engine
import json
import time
import subprocess
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import concurrent.futures

@dataclass
class PositionAnalysis:
    """Analysis results for a single position"""
    fen: str
    move_number: int
    game_phase: str  # opening, middlegame, endgame
    
    # Engine results
    engine_moves: Dict[str, str]  # engine_version -> move_uci
    engine_evaluations: Dict[str, float]  # engine_version -> evaluation
    engine_times: Dict[str, float]  # engine_version -> time_taken
    engine_depths: Dict[str, int]  # engine_version -> search_depth
    engine_nodes: Dict[str, int]  # engine_version -> nodes_searched
    
    # Stockfish validation
    stockfish_best_move: str
    stockfish_evaluation: float
    stockfish_top_moves: List[Tuple[str, float]]  # [(move, eval), ...]
    
    # Analysis results
    move_quality_scores: Dict[str, float]  # engine_version -> quality_score (0-100)
    consistency_analysis: Dict[str, Any]
    regression_flags: List[str]

@dataclass 
class GameAnalysisReport:
    """Complete analysis report for a game"""
    game_info: Dict[str, str]
    total_positions: int
    positions_analyzed: List[PositionAnalysis]
    
    # Summary statistics
    engine_performance: Dict[str, Dict[str, float]]  # engine -> {avg_quality, avg_time, etc}
    move_consistency_matrix: Dict[str, Dict[str, float]]  # engine1 -> engine2 -> consistency%
    regression_summary: Dict[str, List[str]]  # engine -> [regression_types]
    
    # Insights
    key_findings: List[str]
    recommendations: List[str]

class EngineInterface:
    """Interface for communicating with different engine versions"""
    
    def __init__(self, engine_path: str, engine_name: str):
        self.engine_path = engine_path
        self.engine_name = engine_name
        self.engine = None
        
    def __enter__(self):
        """Context manager entry - start engine"""
        try:
            if self.engine_path.endswith('.py'):
                # Python engine - use subprocess with Python
                self.process = subprocess.Popen(
                    [sys.executable, self.engine_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(self.engine_path)
                )
                self.engine = chess.engine.SimpleEngine.popen_uci(
                    [sys.executable, self.engine_path],
                    cwd=os.path.dirname(self.engine_path)
                )
            else:
                # Executable engine
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            return self
        except Exception as e:
            print(f"Failed to start engine {self.engine_name}: {e}")
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up engine"""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
    
    def analyze_position(self, board: chess.Board, time_limit: float = 2.0) -> Dict[str, Any]:
        """Analyze position and return move, evaluation, and stats"""
        if not self.engine:
            return None
            
        try:
            start_time = time.time()
            
            # Get engine analysis
            result = self.engine.analyse(
                board, 
                chess.engine.Limit(time=time_limit),
                info=chess.engine.INFO_ALL
            )
            
            # Get best move
            best_move_result = self.engine.play(
                board,
                chess.engine.Limit(time=time_limit)
            )
            
            analysis_time = time.time() - start_time
            
            return {
                'move': best_move_result.move.uci() if best_move_result.move else None,
                'evaluation': result.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score(mate_score=10000),
                'depth': result.get('depth', 0),
                'nodes': result.get('nodes', 0), 
                'time': analysis_time,
                'pv': [move.uci() for move in result.get('pv', [])[:5]]  # Top 5 principal variation moves
            }
            
        except Exception as e:
            print(f"Error analyzing position with {self.engine_name}: {e}")
            return None

class StockfishValidator:
    """Uses Stockfish to provide objective move quality assessment"""
    
    def __init__(self, stockfish_path: str = "stockfish", depth: int = 15):
        self.stockfish_path = stockfish_path
        self.depth = depth
        self.engine = None
    
    def __enter__(self):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            return self
        except Exception as e:
            print(f"Failed to start Stockfish: {e}")
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
    
    def evaluate_position(self, board: chess.Board) -> Dict[str, Any]:
        """Get Stockfish's evaluation of the position"""
        if not self.engine:
            return None
            
        try:
            # Get multi-PV analysis to see top moves
            result = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.depth),
                multipv=5,
                info=chess.engine.INFO_ALL
            )
            
            if not result:
                return None
            
            # Extract top moves and their evaluations
            top_moves = []
            best_move = None
            best_eval = None
            
            # Handle both single result and multi-PV results
            if isinstance(result, list):
                for i, pv_result in enumerate(result):
                    pv = pv_result.get('pv', [])
                    if pv:
                        move = pv[0].uci()
                        score = pv_result.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                        eval_cp = score.relative.score(mate_score=10000)
                        top_moves.append((move, eval_cp))
                        
                        if i == 0:  # Best move
                            best_move = move
                            best_eval = eval_cp
            else:
                pv = result.get('pv', [])
                if pv:
                    best_move = pv[0].uci()
                    score = result.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    best_eval = score.relative.score(mate_score=10000)
                    top_moves.append((best_move, best_eval))
            
            return {
                'best_move': best_move,
                'evaluation': best_eval,
                'top_moves': top_moves[:5],  # Top 5 moves
                'depth': result[0].get('depth', self.depth) if isinstance(result, list) else result.get('depth', self.depth)
            }
            
        except Exception as e:
            print(f"Error evaluating position with Stockfish: {e}")
            return None
    
    def calculate_move_quality(self, board: chess.Board, move_uci: str, stockfish_result: Dict[str, Any]) -> float:
        """Calculate quality score (0-100) for a move based on Stockfish analysis"""
        if not stockfish_result or not stockfish_result.get('top_moves'):
            return 50.0  # Neutral score if no data
        
        top_moves = stockfish_result['top_moves']
        best_eval = top_moves[0][1]
        
        # Find the move in top moves
        move_eval = None
        for move, eval_score in top_moves:
            if move == move_uci:
                move_eval = eval_score
                break
        
        if move_eval is None:
            # Move not in top 5, need to evaluate it specifically
            try:
                board_copy = board.copy()
                board_copy.push(chess.Move.from_uci(move_uci))
                temp_result = self.evaluate_position(board_copy)
                if temp_result:
                    move_eval = -temp_result['evaluation']  # Negative because we're evaluating the resulting position
                else:
                    return 25.0  # Low score if we can't evaluate
            except:
                return 25.0
        
        # Calculate quality based on how close the move is to the best move
        eval_diff = abs(move_eval - best_eval)
        
        # Convert centipawn difference to quality score
        if eval_diff <= 10:
            return 100.0  # Excellent move
        elif eval_diff <= 25:
            return 90.0   # Very good move
        elif eval_diff <= 50:
            return 80.0   # Good move
        elif eval_diff <= 100:
            return 70.0   # Decent move
        elif eval_diff <= 200:
            return 50.0   # Average move
        elif eval_diff <= 300:
            return 30.0   # Poor move
        else:
            return 10.0   # Very poor move

class PositionalAnalyzer:
    """Main class for conducting positional analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engines = {}
        self.stockfish = None
        
        # Setup engines
        for engine_name, engine_config in config.get('engines', {}).items():
            self.engines[engine_name] = {
                'path': engine_config['path'],
                'name': engine_name
            }
    
    def extract_positions_from_pgn(self, pgn_file: str, max_positions: int = 30) -> List[Tuple[str, int, str]]:
        """Extract positions from a PGN file - returns [(fen, move_number, phase), ...]"""
        positions = []
        
        try:
            with open(pgn_file, 'r') as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    board = game.board()
                    move_number = 1
                    
                    for move in game.mainline_moves():
                        # Classify game phase
                        piece_count = len(board.piece_map())
                        if move_number <= 10:
                            phase = "opening"
                        elif piece_count > 12:
                            phase = "middlegame"
                        else:
                            phase = "endgame"
                        
                        # Store position before the move
                        positions.append((board.fen(), move_number, phase))
                        
                        board.push(move)
                        move_number += 1
                        
                        if len(positions) >= max_positions:
                            break
                    
                    if len(positions) >= max_positions:
                        break
                        
        except Exception as e:
            print(f"Error reading PGN file {pgn_file}: {e}")
        
        return positions
    
    def analyze_position(self, fen: str, move_number: int, phase: str) -> PositionAnalysis:
        """Analyze a single position with all engines and Stockfish"""
        board = chess.Board(fen)
        
        print(f"Analyzing position {move_number} ({phase}): {fen[:50]}...")
        
        # Initialize analysis result
        analysis = PositionAnalysis(
            fen=fen,
            move_number=move_number,
            game_phase=phase,
            engine_moves={},
            engine_evaluations={},
            engine_times={},
            engine_depths={},
            engine_nodes={},
            stockfish_best_move="",
            stockfish_evaluation=0.0,
            stockfish_top_moves=[],
            move_quality_scores={},
            consistency_analysis={},
            regression_flags=[]
        )
        
        # Get Stockfish evaluation first
        with StockfishValidator(depth=12) as stockfish:
            if stockfish:
                sf_result = stockfish.evaluate_position(board)
                if sf_result:
                    analysis.stockfish_best_move = sf_result.get('best_move', '')
                    analysis.stockfish_evaluation = sf_result.get('evaluation', 0)
                    analysis.stockfish_top_moves = sf_result.get('top_moves', [])
        
        # Test each engine
        time_limit = self.config.get('analysis_time_per_position', 2.0)
        
        for engine_name, engine_config in self.engines.items():
            print(f"  Testing {engine_name}...")
            
            with EngineInterface(engine_config['path'], engine_name) as engine_interface:
                if engine_interface:
                    result = engine_interface.analyze_position(board, time_limit)
                    if result:
                        analysis.engine_moves[engine_name] = result.get('move', '')
                        analysis.engine_evaluations[engine_name] = result.get('evaluation', 0)
                        analysis.engine_times[engine_name] = result.get('time', 0)
                        analysis.engine_depths[engine_name] = result.get('depth', 0)
                        analysis.engine_nodes[engine_name] = result.get('nodes', 0)
                        
                        # Calculate move quality using Stockfish
                        if analysis.stockfish_top_moves:
                            with StockfishValidator(depth=8) as sf_validator:
                                if sf_validator:
                                    quality = sf_validator.calculate_move_quality(
                                        board, result.get('move', ''), 
                                        {'top_moves': analysis.stockfish_top_moves}
                                    )
                                    analysis.move_quality_scores[engine_name] = quality
        
        # Analyze consistency and regressions
        analysis.consistency_analysis = self._analyze_move_consistency(analysis)
        analysis.regression_flags = self._detect_regressions(analysis)
        
        return analysis
    
    def _analyze_move_consistency(self, analysis: PositionAnalysis) -> Dict[str, Any]:
        """Analyze how consistent moves are between engine versions"""
        moves = analysis.engine_moves
        if len(moves) < 2:
            return {}
        
        consistency = {}
        engine_names = list(moves.keys())
        
        # Check pairwise consistency
        for i, engine1 in enumerate(engine_names):
            for engine2 in engine_names[i+1:]:
                move1 = moves.get(engine1, '')
                move2 = moves.get(engine2, '')
                key = f"{engine1}_vs_{engine2}"
                consistency[key] = move1 == move2
        
        # Check if all engines agree
        unique_moves = set(moves.values())
        consistency['all_agree'] = len(unique_moves) == 1
        consistency['agreement_rate'] = 1.0 / len(unique_moves) if unique_moves else 0.0
        
        return consistency
    
    def _detect_regressions(self, analysis: PositionAnalysis) -> List[str]:
        """Detect potential regressions in engine performance"""
        flags = []
        
        # Quality regression: newer version performs worse than older version
        qualities = analysis.move_quality_scores
        if 'v7.0' in qualities and 'v9.1' in qualities:
            if qualities['v9.1'] < qualities['v7.0'] - 10:  # 10+ point quality drop
                flags.append(f"Quality regression: v9.1 ({qualities['v9.1']:.1f}) vs v7.0 ({qualities['v7.0']:.1f})")
        
        # Time regression: much slower without quality improvement
        times = analysis.engine_times
        if 'v7.0' in times and 'v9.1' in times:
            if times['v9.1'] > times['v7.0'] * 2 and qualities.get('v9.1', 0) <= qualities.get('v7.0', 0):
                flags.append(f"Time regression: v9.1 is {times['v9.1']/times['v7.0']:.1f}x slower without quality gain")
        
        # Move consistency regression: changed move for the worse
        moves = analysis.engine_moves
        if 'v7.0' in moves and 'v9.1' in moves and moves['v7.0'] != moves['v9.1']:
            if qualities.get('v9.1', 0) < qualities.get('v7.0', 0):
                flags.append(f"Move change regression: v9.1 chose worse move ({moves['v9.1']} vs {moves['v7.0']})")
        
        return flags
    
    def analyze_game(self, pgn_file: str, output_file: str) -> GameAnalysisReport:
        """Analyze all positions from a game and generate comprehensive report"""
        print(f"Starting positional analysis of {pgn_file}")
        
        # Extract positions
        positions = self.extract_positions_from_pgn(pgn_file, self.config.get('max_positions', 30))
        print(f"Extracted {len(positions)} positions for analysis")
        
        # Analyze each position
        analyzed_positions = []
        for i, (fen, move_num, phase) in enumerate(positions):
            print(f"\n=== Position {i+1}/{len(positions)} ===")
            analysis = self.analyze_position(fen, move_num, phase)
            analyzed_positions.append(analysis)
        
        # Generate report
        report = self._generate_report(pgn_file, analyzed_positions)
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        
        print(f"\nAnalysis complete! Report saved to {output_file}")
        return report
    
    def _generate_report(self, pgn_file: str, positions: List[PositionAnalysis]) -> GameAnalysisReport:
        """Generate comprehensive analysis report"""
        # Extract game info from PGN
        game_info = {"source_file": pgn_file, "analysis_date": datetime.now().isoformat()}
        
        # Calculate engine performance statistics
        engine_performance = {}
        for engine_name in self.engines.keys():
            qualities = [p.move_quality_scores.get(engine_name, 0) for p in positions]
            times = [p.engine_times.get(engine_name, 0) for p in positions if p.engine_times.get(engine_name, 0) > 0]
            depths = [p.engine_depths.get(engine_name, 0) for p in positions if p.engine_depths.get(engine_name, 0) > 0]
            nodes = [p.engine_nodes.get(engine_name, 0) for p in positions if p.engine_nodes.get(engine_name, 0) > 0]
            
            engine_performance[engine_name] = {
                'avg_move_quality': sum(qualities) / len(qualities) if qualities else 0,
                'avg_time': sum(times) / len(times) if times else 0,
                'avg_depth': sum(depths) / len(depths) if depths else 0,
                'avg_nodes': sum(nodes) / len(nodes) if nodes else 0,
                'positions_analyzed': len([q for q in qualities if q > 0])
            }
        
        # Calculate consistency matrix
        consistency_matrix = {}
        engine_names = list(self.engines.keys())
        for engine1 in engine_names:
            consistency_matrix[engine1] = {}
            for engine2 in engine_names:
                if engine1 != engine2:
                    agreements = sum(1 for p in positions 
                                   if p.engine_moves.get(engine1) == p.engine_moves.get(engine2))
                    total = len([p for p in positions 
                               if p.engine_moves.get(engine1) and p.engine_moves.get(engine2)])
                    consistency_matrix[engine1][engine2] = agreements / total if total > 0 else 0
        
        # Aggregate regression flags
        regression_summary = {}
        for engine_name in engine_names:
            regression_summary[engine_name] = []
            for position in positions:
                for flag in position.regression_flags:
                    if engine_name in flag:
                        regression_summary[engine_name].append(flag)
        
        # Generate insights and recommendations
        key_findings = self._generate_key_findings(engine_performance, consistency_matrix, regression_summary)
        recommendations = self._generate_recommendations(engine_performance, regression_summary)
        
        return GameAnalysisReport(
            game_info=game_info,
            total_positions=len(positions),
            positions_analyzed=positions,
            engine_performance=engine_performance,
            move_consistency_matrix=consistency_matrix,
            regression_summary=regression_summary,
            key_findings=key_findings,
            recommendations=recommendations
        )
    
    def _generate_key_findings(self, performance: Dict, consistency: Dict, regressions: Dict) -> List[str]:
        """Generate key findings from the analysis"""
        findings = []
        
        # Performance comparison
        if 'v7.0' in performance and 'v9.1' in performance:
            v7_quality = performance['v7.0']['avg_move_quality']
            v91_quality = performance['v9.1']['avg_move_quality']
            quality_diff = v91_quality - v7_quality
            
            if quality_diff > 5:
                findings.append(f"v9.1 shows significant improvement in move quality (+{quality_diff:.1f} points vs v7.0)")
            elif quality_diff < -5:
                findings.append(f"v9.1 shows regression in move quality ({quality_diff:.1f} points vs v7.0)")
            else:
                findings.append(f"v9.1 move quality similar to v7.0 (±{abs(quality_diff):.1f} points)")
            
            # Time analysis
            v7_time = performance['v7.0']['avg_time']
            v91_time = performance['v9.1']['avg_time']
            if v7_time > 0:
                time_ratio = v91_time / v7_time
                if time_ratio > 1.5:
                    findings.append(f"v9.1 is {time_ratio:.1f}x slower than v7.0")
                elif time_ratio < 0.7:
                    findings.append(f"v9.1 is {1/time_ratio:.1f}x faster than v7.0")
        
        # Consistency analysis
        if 'v7.0' in consistency and 'v9.1' in consistency.get('v7.0', {}):
            consistency_rate = consistency['v7.0']['v9.1']
            findings.append(f"v7.0 and v9.1 agree on {consistency_rate*100:.1f}% of moves")
        
        # Regression summary
        for engine, flags in regressions.items():
            if flags:
                findings.append(f"{engine}: {len(flags)} potential regressions detected")
        
        return findings
    
    def _generate_recommendations(self, performance: Dict, regressions: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Based on regressions
        if regressions.get('v9.1'):
            recommendations.append("Investigate v9.1 regressions: focus on move quality and time efficiency")
            recommendations.append("Consider reverting problematic changes or improving confidence calculations")
        
        # Based on performance
        for engine, stats in performance.items():
            if stats['avg_move_quality'] < 60:
                recommendations.append(f"Improve {engine} evaluation accuracy (current quality: {stats['avg_move_quality']:.1f})")
            
            if stats['avg_time'] > 3.0:
                recommendations.append(f"Optimize {engine} search speed (current avg: {stats['avg_time']:.1f}s)")
        
        return recommendations

def main():
    """Main execution function"""
    # Configuration
    config = {
        'engines': {
            'v7.0': {'path': 'path/to/v7p3r_v7.0.exe'},  # Will be updated based on available engines
            'v9.1': {'path': 's:/Maker Stuff/Programming/Chess Engines/V7P3R Chess Engine/v7p3r-chess-engine/src/v7p3r_uci.py'}
        },
        'analysis_time_per_position': 2.0,  # seconds
        'max_positions': 25,
        'stockfish_depth': 12
    }
    
    # Find available engines
    engine_dir = Path("s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-tester/engines")
    if engine_dir.exists():
        for engine_file in engine_dir.glob("V7P3R*.exe"):
            version = "unknown"
            if "v7" in engine_file.name.lower():
                version = "v7.0"
            elif "v8" in engine_file.name.lower():
                version = "v8.0"
            elif "v9" in engine_file.name.lower():
                version = "v9.0"
            
            if version != "unknown":
                config['engines'][version] = {'path': str(engine_file)}
    
    # Select PGN file for analysis
    pgn_file = "s:/Maker Stuff/Programming/Chess Engines/Chess Engine Playground/engine-metrics/game_records/Engine Battle 20250829/Engine Regression Battle 20250829.pgn"
    output_file = f"v7p3r_positional_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Run analysis
    analyzer = PositionalAnalyzer(config)
    report = analyzer.analyze_game(pgn_file, output_file)
    
    # Print summary
    print("\n" + "="*60)
    print("POSITIONAL ANALYSIS SUMMARY")
    print("="*60)
    
    for finding in report.key_findings:
        print(f"• {finding}")
    
    print(f"\nRECOMMENDATIONS:")
    for rec in report.recommendations:
        print(f"• {rec}")
    
    print(f"\nDetailed report saved to: {output_file}")

if __name__ == "__main__":
    main()
