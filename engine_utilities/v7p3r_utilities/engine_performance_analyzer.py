#!/usr/bin/env python3
"""
V7P3R Engine Performance Analyzer
Performs comprehensive performance testing on historical V7P3R engine versions
to establish baselines for v11 development. Tests include perft, search speed,
tactical accuracy, and time management analysis.

Author: Pat Snyder
Created: September 7, 2025
"""

import os
import sys
import time
import json
import subprocess
import chess
import chess.engine
import threading
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path


@dataclass
class PerftResult:
    """Results from perft testing"""
    depth: int
    nodes: int
    time_ms: int
    nps: float  # Nodes per second


@dataclass
class SearchPerformance:
    """Search performance metrics"""
    position_fen: str
    depth_achieved: int
    time_ms: int
    nodes: int
    nps: float
    best_move: str
    evaluation: float


@dataclass
class EnginePerformance:
    """Complete engine performance profile"""
    engine_version: str
    engine_path: str
    test_date: str
    uci_info: Dict
    perft_results: List[PerftResult]
    search_performance: List[SearchPerformance]
    tactical_accuracy: Dict
    time_management: Dict
    overall_score: float


class V7P3RPerformanceAnalyzer:
    """
    Comprehensive performance analyzer for V7P3R engine versions.
    
    Tests include:
    1. Perft testing for move generation speed
    2. Search performance on standard positions
    3. Tactical puzzle solving
    4. Time management evaluation
    5. UCI compliance and stability
    """
    
    def __init__(self, engine_directory: str, timeout_seconds: int = 30):
        self.engine_directory = engine_directory
        self.timeout_seconds = timeout_seconds
        self.test_positions = self.load_test_positions()
        self.tactical_puzzles = self.load_tactical_puzzles()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for performance analysis"""
        log_file = f"v7p3r_performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_test_positions(self) -> List[Dict]:
        """Load standard test positions for performance evaluation"""
        return [
            {
                'name': 'Starting Position',
                'fen': chess.STARTING_FEN,
                'expected_depth': 6,
                'description': 'Standard opening position'
            },
            {
                'name': 'Kiwipete',
                'fen': 'r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1',
                'expected_depth': 5,
                'description': 'Complex tactical position'
            },
            {
                'name': 'Position 3',
                'fen': '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
                'expected_depth': 7,
                'description': 'Endgame position'
            },
            {
                'name': 'Position 4',
                'fen': 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
                'expected_depth': 5,
                'description': 'Middlegame position'
            },
            {
                'name': 'Position 5',
                'fen': 'rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8',
                'expected_depth': 5,
                'description': 'Sharp tactical position'
            }
        ]
    
    def load_tactical_puzzles(self) -> List[Dict]:
        """Load tactical puzzles for accuracy testing"""
        return [
            {
                'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4',
                'best_move': 'Ng5',
                'description': 'Knight fork opportunity'
            },
            {
                'fen': 'rnbqkb1r/pp1ppppp/5n2/2p5/2PP4/8/PP2PPPP/RNBQKBNR w KQkq c6 0 3',
                'best_move': 'd5',
                'description': 'Central pawn breakthrough'
            },
            {
                'fen': 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 6 5',
                'best_move': 'Bxf7+',
                'description': 'Bishop sacrifice'
            },
            {
                'fen': 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2',
                'best_move': 'Nf3',
                'description': 'Development'
            },
            {
                'fen': 'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3',
                'best_move': 'Bb5',
                'description': 'Pin the knight'
            }
        ]
    
    def find_v7p3r_engines(self) -> List[str]:
        """Find all V7P3R engine executables in the directory"""
        engines = []
        
        for root, dirs, files in os.walk(self.engine_directory):
            for file in files:
                if (file.startswith('V7P3R_') and file.endswith('.exe')):
                    engine_path = os.path.join(root, file)
                    engines.append(engine_path)
        
        # Sort by version (attempt to extract version numbers)
        def version_key(path):
            filename = os.path.basename(path)
            try:
                # Extract version from filename like V7P3R_v10.2.exe
                version_part = filename.split('_v')[1].split('.exe')[0]
                version_nums = version_part.split('.')
                return tuple(int(x) for x in version_nums)
            except:
                return (0, 0)
        
        engines.sort(key=version_key)
        return engines
    
    def run_perft_test(self, engine_path: str, depth: int = 6) -> Optional[PerftResult]:
        """Run perft test on an engine"""
        try:
            self.logger.info(f"Running perft depth {depth} on {os.path.basename(engine_path)}")
            
            # Start engine
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Send UCI commands
            commands = [
                'uci',
                'isready',
                'ucinewgame',
                'isready',
                f'go perft {depth}',
                'quit'
            ]
            
            start_time = time.time()
            
            for cmd in commands:
                process.stdin.write(cmd + '\n')
                process.stdin.flush()
            
            # Read output with timeout
            output_lines = []
            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                output_lines = stdout.split('\n')
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"Perft test timed out for {os.path.basename(engine_path)}")
                return None
            
            end_time = time.time()
            time_ms = int((end_time - start_time) * 1000)
            
            # Parse perft results
            nodes = 0
            for line in output_lines:
                if 'Nodes searched:' in line or 'nodes' in line.lower():
                    try:
                        # Try to extract number from various formats
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            nodes = int(numbers[-1])  # Take the last number found
                            break
                    except:
                        continue
            
            if nodes > 0:
                nps = nodes / (time_ms / 1000.0) if time_ms > 0 else 0
                return PerftResult(depth=depth, nodes=nodes, time_ms=time_ms, nps=nps)
            
        except Exception as e:
            self.logger.error(f"Perft test failed for {os.path.basename(engine_path)}: {e}")
        
        return None
    
    def run_search_performance_test(self, engine_path: str, position: Dict) -> Optional[SearchPerformance]:
        """Test search performance on a specific position"""
        try:
            self.logger.info(f"Testing search performance on {position['name']} for {os.path.basename(engine_path)}")
            
            # Start engine
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Send UCI commands
            commands = [
                'uci',
                'isready',
                'ucinewgame',
                'isready',
                f'position fen {position["fen"]}',
                'go movetime 2000'  # 2 second search
            ]
            
            start_time = time.time()
            
            for cmd in commands:
                process.stdin.write(cmd + '\n')
                process.stdin.flush()
            
            # Read output with timeout
            output_lines = []
            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                output_lines = stdout.split('\n')
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"Search test timed out for {os.path.basename(engine_path)}")
                return None
            
            end_time = time.time()
            time_ms = int((end_time - start_time) * 1000)
            
            # Parse search results
            best_move = ""
            depth_achieved = 0
            nodes = 0
            evaluation = 0.0
            
            for line in output_lines:
                if line.startswith('bestmove'):
                    parts = line.split()
                    if len(parts) > 1:
                        best_move = parts[1]
                elif line.startswith('info depth'):
                    try:
                        # Parse info lines to get depth, nodes, score
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'depth' and i + 1 < len(parts):
                                depth_achieved = max(depth_achieved, int(parts[i + 1]))
                            elif part == 'nodes' and i + 1 < len(parts):
                                nodes = max(nodes, int(parts[i + 1]))
                            elif part == 'cp' and i + 1 < len(parts):
                                evaluation = int(parts[i + 1]) / 100.0
                            elif part == 'mate' and i + 1 < len(parts):
                                mate_moves = int(parts[i + 1])
                                evaluation = 1000 if mate_moves > 0 else -1000
                    except:
                        continue
            
            if best_move:
                nps = nodes / (time_ms / 1000.0) if time_ms > 0 else 0
                return SearchPerformance(
                    position_fen=position['fen'],
                    depth_achieved=depth_achieved,
                    time_ms=time_ms,
                    nodes=nodes,
                    nps=nps,
                    best_move=best_move,
                    evaluation=evaluation
                )
            
        except Exception as e:
            self.logger.error(f"Search performance test failed for {os.path.basename(engine_path)}: {e}")
        
        return None
    
    def run_tactical_accuracy_test(self, engine_path: str) -> Dict:
        """Test tactical puzzle solving accuracy"""
        self.logger.info(f"Testing tactical accuracy for {os.path.basename(engine_path)}")
        
        correct_moves = 0
        total_puzzles = len(self.tactical_puzzles)
        puzzle_results = []
        
        for i, puzzle in enumerate(self.tactical_puzzles):
            try:
                # Test puzzle solving
                result = self.run_search_performance_test(engine_path, {
                    'name': f'Tactical Puzzle {i+1}',
                    'fen': puzzle['fen']
                })
                
                if result:
                    # Check if the best move matches expected
                    is_correct = result.best_move.lower() == puzzle['best_move'].lower()
                    if is_correct:
                        correct_moves += 1
                    
                    puzzle_results.append({
                        'puzzle_id': i + 1,
                        'expected_move': puzzle['best_move'],
                        'engine_move': result.best_move,
                        'correct': is_correct,
                        'depth': result.depth_achieved,
                        'evaluation': result.evaluation,
                        'description': puzzle['description']
                    })
                
            except Exception as e:
                self.logger.warning(f"Tactical puzzle {i+1} failed: {e}")
        
        accuracy = (correct_moves / total_puzzles) * 100 if total_puzzles > 0 else 0
        
        return {
            'accuracy_percentage': accuracy,
            'correct_moves': correct_moves,
            'total_puzzles': total_puzzles,
            'puzzle_results': puzzle_results
        }
    
    def test_time_management(self, engine_path: str) -> Dict:
        """Test time management capabilities"""
        self.logger.info(f"Testing time management for {os.path.basename(engine_path)}")
        
        time_tests = [
            {'name': 'Quick Move', 'time_ms': 500, 'expected_depth': 3},
            {'name': 'Normal Move', 'time_ms': 2000, 'expected_depth': 5},
            {'name': 'Deep Think', 'time_ms': 5000, 'expected_depth': 7}
        ]
        
        results = []
        
        for test in time_tests:
            position = self.test_positions[0]  # Use starting position
            
            try:
                # Start engine
                process = subprocess.Popen(
                    [engine_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=0
                )
                
                # Send UCI commands
                commands = [
                    'uci',
                    'isready',
                    'ucinewgame',
                    'isready',
                    f'position fen {position["fen"]}',
                    f'go movetime {test["time_ms"]}'
                ]
                
                start_time = time.time()
                
                for cmd in commands:
                    process.stdin.write(cmd + '\n')
                    process.stdin.flush()
                
                # Read output with timeout
                try:
                    stdout, stderr = process.communicate(timeout=test["time_ms"] / 1000 + 5)
                    output_lines = stdout.split('\n')
                except subprocess.TimeoutExpired:
                    process.kill()
                    continue
                
                end_time = time.time()
                actual_time_ms = int((end_time - start_time) * 1000)
                
                # Parse results
                depth_achieved = 0
                best_move = ""
                
                for line in output_lines:
                    if line.startswith('bestmove'):
                        parts = line.split()
                        if len(parts) > 1:
                            best_move = parts[1]
                    elif line.startswith('info depth'):
                        try:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'depth' and i + 1 < len(parts):
                                    depth_achieved = max(depth_achieved, int(parts[i + 1]))
                        except:
                            continue
                
                # Calculate time efficiency
                time_efficiency = test['time_ms'] / actual_time_ms if actual_time_ms > 0 else 0
                depth_efficiency = depth_achieved / test['expected_depth'] if test['expected_depth'] > 0 else 0
                
                results.append({
                    'test_name': test['name'],
                    'allocated_time_ms': test['time_ms'],
                    'actual_time_ms': actual_time_ms,
                    'expected_depth': test['expected_depth'],
                    'achieved_depth': depth_achieved,
                    'time_efficiency': time_efficiency,
                    'depth_efficiency': depth_efficiency,
                    'best_move': best_move
                })
                
            except Exception as e:
                self.logger.warning(f"Time management test '{test['name']}' failed: {e}")
        
        # Calculate overall time management score
        avg_time_efficiency = sum(r['time_efficiency'] for r in results) / len(results) if results else 0
        avg_depth_efficiency = sum(r['depth_efficiency'] for r in results) / len(results) if results else 0
        
        return {
            'time_efficiency_avg': avg_time_efficiency,
            'depth_efficiency_avg': avg_depth_efficiency,
            'overall_score': (avg_time_efficiency + avg_depth_efficiency) / 2,
            'test_results': results
        }
    
    def get_uci_info(self, engine_path: str) -> Dict:
        """Get UCI engine information"""
        try:
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            process.stdin.write('uci\n')
            process.stdin.flush()
            
            try:
                stdout, stderr = process.communicate(timeout=10)
                output_lines = stdout.split('\n')
            except subprocess.TimeoutExpired:
                process.kill()
                return {}
            
            info = {}
            for line in output_lines:
                if line.startswith('id name'):
                    info['name'] = line.split('id name ', 1)[1]
                elif line.startswith('id author'):
                    info['author'] = line.split('id author ', 1)[1]
                elif line.startswith('option name'):
                    if 'options' not in info:
                        info['options'] = []
                    info['options'].append(line)
            
            return info
            
        except Exception as e:
            self.logger.warning(f"Failed to get UCI info for {os.path.basename(engine_path)}: {e}")
            return {}
    
    def analyze_engine(self, engine_path: str) -> Optional[EnginePerformance]:
        """Perform comprehensive analysis of a single engine"""
        engine_name = os.path.basename(engine_path)
        self.logger.info(f"Starting comprehensive analysis of {engine_name}")
        
        try:
            # Get UCI information
            uci_info = self.get_uci_info(engine_path)
            
            # Run perft tests
            perft_results = []
            for depth in [4, 5, 6]:
                result = self.run_perft_test(engine_path, depth)
                if result:
                    perft_results.append(result)
            
            # Run search performance tests
            search_performance = []
            for position in self.test_positions:
                result = self.run_search_performance_test(engine_path, position)
                if result:
                    search_performance.append(result)
            
            # Test tactical accuracy
            tactical_accuracy = self.run_tactical_accuracy_test(engine_path)
            
            # Test time management
            time_management = self.test_time_management(engine_path)
            
            # Calculate overall performance score
            overall_score = self.calculate_overall_score(
                perft_results, search_performance, tactical_accuracy, time_management
            )
            
            return EnginePerformance(
                engine_version=engine_name,
                engine_path=engine_path,
                test_date=datetime.now().isoformat(),
                uci_info=uci_info,
                perft_results=perft_results,
                search_performance=search_performance,
                tactical_accuracy=tactical_accuracy,
                time_management=time_management,
                overall_score=overall_score
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze {engine_name}: {e}")
            return None
    
    def calculate_overall_score(self, perft_results, search_performance, tactical_accuracy, time_management) -> float:
        """Calculate overall performance score (0-100)"""
        score = 0.0
        components = 0
        
        # Perft performance (25% weight)
        if perft_results:
            avg_nps = sum(r.nps for r in perft_results) / len(perft_results)
            perft_score = min(100, (avg_nps / 10000) * 25)  # Normalize to 10k NPS = 25 points
            score += perft_score
            components += 1
        
        # Search performance (25% weight)
        if search_performance:
            avg_depth = sum(r.depth_achieved for r in search_performance) / len(search_performance)
            avg_nps = sum(r.nps for r in search_performance) / len(search_performance)
            search_score = min(25, (avg_depth / 6) * 12.5 + (avg_nps / 5000) * 12.5)
            score += search_score
            components += 1
        
        # Tactical accuracy (30% weight)
        if tactical_accuracy:
            tactical_score = (tactical_accuracy['accuracy_percentage'] / 100) * 30
            score += tactical_score
            components += 1
        
        # Time management (20% weight)
        if time_management:
            time_score = time_management['overall_score'] * 20
            score += time_score
            components += 1
        
        return score / components if components > 0 else 0.0
    
    def analyze_all_engines(self) -> Dict[str, EnginePerformance]:
        """Analyze all V7P3R engines in the directory"""
        engines = self.find_v7p3r_engines()
        self.logger.info(f"Found {len(engines)} V7P3R engines to analyze")
        
        results = {}
        
        for engine_path in engines:
            engine_name = os.path.basename(engine_path)
            self.logger.info(f"Analyzing {engine_name} ({engines.index(engine_path) + 1}/{len(engines)})")
            
            result = self.analyze_engine(engine_path)
            if result:
                results[engine_name] = result
            
            # Small delay between tests
            time.sleep(1)
        
        return results
    
    def save_results(self, results: Dict[str, EnginePerformance], output_directory: str):
        """Save analysis results to files"""
        os.makedirs(output_directory, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete results
        results_file = os.path.join(output_directory, f'v7p3r_performance_analysis_{timestamp}.json')
        with open(results_file, 'w') as f:
            results_data = {name: asdict(perf) for name, perf in results.items()}
            json.dump(results_data, f, indent=2)
        
        # Create performance comparison report
        comparison_file = os.path.join(output_directory, f'v7p3r_performance_comparison_{timestamp}.md')
        self.create_comparison_report(results, comparison_file)
        
        # Save baseline data for v11 development
        baseline_file = os.path.join(output_directory, f'v7p3r_baseline_metrics_{timestamp}.json')
        baseline_data = self.create_baseline_metrics(results)
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        self.logger.info(f"Results saved to {output_directory}")
        return results_file, comparison_file, baseline_file
    
    def create_comparison_report(self, results: Dict[str, EnginePerformance], output_file: str):
        """Create markdown comparison report"""
        with open(output_file, 'w') as f:
            f.write("# V7P3R Engine Performance Comparison Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall scores table
            f.write("## Overall Performance Scores\n\n")
            f.write("| Engine Version | Overall Score | Tactical Accuracy | Avg Search Depth | Avg NPS | Time Management |\n")
            f.write("|---|---|---|---|---|---|\n")
            
            sorted_results = sorted(results.items(), key=lambda x: x[1].overall_score, reverse=True)
            
            for name, perf in sorted_results:
                tactical_acc = perf.tactical_accuracy.get('accuracy_percentage', 0)
                avg_depth = sum(r.depth_achieved for r in perf.search_performance) / len(perf.search_performance) if perf.search_performance else 0
                avg_nps = sum(r.nps for r in perf.search_performance) / len(perf.search_performance) if perf.search_performance else 0
                time_score = perf.time_management.get('overall_score', 0)
                
                f.write(f"| {name} | {perf.overall_score:.1f} | {tactical_acc:.1f}% | {avg_depth:.1f} | {avg_nps:.0f} | {time_score:.2f} |\n")
            
            # Detailed analysis sections
            f.write("\n## Detailed Analysis\n\n")
            
            for name, perf in sorted_results:
                f.write(f"### {name}\n\n")
                f.write(f"- **Overall Score**: {perf.overall_score:.1f}/100\n")
                f.write(f"- **UCI Name**: {perf.uci_info.get('name', 'Unknown')}\n")
                f.write(f"- **Test Date**: {perf.test_date}\n\n")
                
                # Perft results
                if perf.perft_results:
                    f.write("**Perft Results:**\n")
                    for result in perf.perft_results:
                        f.write(f"- Depth {result.depth}: {result.nodes:,} nodes in {result.time_ms}ms ({result.nps:.0f} NPS)\n")
                    f.write("\n")
                
                # Tactical accuracy
                f.write(f"**Tactical Accuracy**: {perf.tactical_accuracy.get('accuracy_percentage', 0):.1f}% ")
                f.write(f"({perf.tactical_accuracy.get('correct_moves', 0)}/{perf.tactical_accuracy.get('total_puzzles', 0)})\n\n")
                
                # Time management
                f.write(f"**Time Management Score**: {perf.time_management.get('overall_score', 0):.2f}\n\n")
                
                f.write("---\n\n")
    
    def create_baseline_metrics(self, results: Dict[str, EnginePerformance]) -> Dict:
        """Create baseline metrics for v11 development tracking"""
        if not results:
            return {}
        
        # Get the latest version (assume highest scoring or most recent)
        latest_engine = max(results.values(), key=lambda x: x.overall_score)
        
        baseline = {
            'baseline_engine': latest_engine.engine_version,
            'baseline_date': datetime.now().isoformat(),
            'performance_targets': {
                'overall_score': latest_engine.overall_score,
                'tactical_accuracy': latest_engine.tactical_accuracy.get('accuracy_percentage', 0),
                'time_management': latest_engine.time_management.get('overall_score', 0)
            },
            'search_metrics': {},
            'perft_metrics': {},
            'improvement_goals': {
                'target_overall_score': min(100, latest_engine.overall_score + 10),
                'target_tactical_accuracy': min(100, latest_engine.tactical_accuracy.get('accuracy_percentage', 0) + 5),
                'target_search_depth': 10,  # Goal from v11 plan
                'target_nps': 15000
            }
        }
        
        # Add search metrics
        if latest_engine.search_performance:
            baseline['search_metrics'] = {
                'avg_depth': sum(r.depth_achieved for r in latest_engine.search_performance) / len(latest_engine.search_performance),
                'avg_nps': sum(r.nps for r in latest_engine.search_performance) / len(latest_engine.search_performance),
                'avg_nodes': sum(r.nodes for r in latest_engine.search_performance) / len(latest_engine.search_performance)
            }
        
        # Add perft metrics
        if latest_engine.perft_results:
            baseline['perft_metrics'] = {
                f'depth_{r.depth}': {'nodes': r.nodes, 'nps': r.nps, 'time_ms': r.time_ms}
                for r in latest_engine.perft_results
            }
        
        # Add version progression data
        baseline['version_progression'] = {}
        for name, perf in results.items():
            baseline['version_progression'][name] = {
                'overall_score': perf.overall_score,
                'tactical_accuracy': perf.tactical_accuracy.get('accuracy_percentage', 0),
                'avg_search_depth': sum(r.depth_achieved for r in perf.search_performance) / len(perf.search_performance) if perf.search_performance else 0
            }
        
        return baseline


def main():
    """Main function for running the performance analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='V7P3R Engine Performance Analyzer')
    parser.add_argument('--engine-dir', required=True, help='Directory containing V7P3R engine executables')
    parser.add_argument('--output-dir', default='performance_analysis', help='Output directory for results')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds for each test')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = V7P3RPerformanceAnalyzer(
        engine_directory=args.engine_dir,
        timeout_seconds=args.timeout
    )
    
    try:
        # Run analysis
        print("Starting V7P3R Engine Performance Analysis...")
        print("="*50)
        
        results = analyzer.analyze_all_engines()
        
        if results:
            # Save results
            results_file, comparison_file, baseline_file = analyzer.save_results(results, args.output_dir)
            
            # Print summary
            print("\n" + "="*50)
            print("V7P3R ENGINE PERFORMANCE ANALYSIS COMPLETE")
            print("="*50)
            print(f"Engines analyzed: {len(results)}")
            print(f"Results saved to: {args.output_dir}")
            print(f"\nFiles created:")
            print(f"- Complete results: {os.path.basename(results_file)}")
            print(f"- Comparison report: {os.path.basename(comparison_file)}")
            print(f"- Baseline metrics: {os.path.basename(baseline_file)}")
            
            # Show top performers
            print(f"\n🏆 TOP PERFORMING ENGINES:")
            sorted_results = sorted(results.items(), key=lambda x: x[1].overall_score, reverse=True)
            for i, (name, perf) in enumerate(sorted_results[:5]):
                print(f"{i+1}. {name}: {perf.overall_score:.1f}/100")
        
        else:
            print("No engines could be analyzed. Check engine directory and paths.")
    
    except Exception as e:
        print(f"Analysis failed: {e}")
        logging.error(f"Analysis failed: {e}")


if __name__ == "__main__":
    main()
