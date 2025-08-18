#!/usr/bin/env python3
"""
Chess Engine Performance Testing Suite v1.0

Comprehensive testing to validate efficiency gains from:
1. Base search (minimax only)
2. Alpha-Beta pruning
3. Alpha-Beta + Move ordering

This will help us quantify the performance improvements from each optimization.
"""

import chess
import time
import json
import chess_ai
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import threading

@dataclass
class PerformanceResult:
    """Results from a single performance test"""
    configuration: str
    position_name: str
    fen: str
    depth: int
    best_move: str
    total_nodes: int
    search_time: float
    nodes_per_second: int
    final_score: int
    search_completed: bool

class PerformanceTestSuite:
    """Comprehensive performance testing for chess engine optimizations"""
    
    def __init__(self):
        self.test_positions = [
            ("Starting Position", chess.STARTING_FEN),
            ("Tactical Puzzle", "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
            ("Complex Middle Game", "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w Q - 0 7"),
            ("Endgame Position", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
            ("Sharp Opening", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
            ("Queen's Gambit", "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2")
        ]
        
        self.test_depths = [3, 4, 5]  # Test at multiple depths
        
        self.configurations = [
            ("Base Search", "base"),
            ("Alpha-Beta", "alphabeta"), 
            ("AB + Move Ordering", "full")
        ]
        
        self.results: List[PerformanceResult] = []
        
    def run_single_test(self, config_name: str, config_type: str, position_name: str, 
                       fen: str, depth: int) -> PerformanceResult:
        """Run a single performance test"""
        
        print(f"\\nTesting: {config_name} | {position_name} | Depth {depth}")
        print("-" * 70)
        
        board = chess.Board(fen)
        
        # Capture search metrics
        search_metrics = []
        nodes_searched = 0
        
        def capture_info(**info):
            nonlocal nodes_searched
            search_metrics.append(info.copy())
            nodes_searched = info.get('nodes', 0)
            
            # Print live progress
            depth_info = info.get('depth', '?')
            score = info.get('score', '?')
            nodes = info.get('nodes', '?')
            time_ms = info.get('time_ms', '?')
            nps = info.get('nps', '?')
            pv = info.get('pv', [])
            
            pv_str = ' '.join(pv[:3]) if pv else "..."
            time_str = f"{time_ms/1000:.3f}s" if isinstance(time_ms, (int, float)) else str(time_ms)
            print(f"    Depth {depth_info:2} | Score: {score:6} | Nodes: {nodes:8} | Time: {time_str:8} | NPS: {nps:8} | PV: {pv_str}")
        
        # Time the search
        start_time = time.time()
        
        try:
            # Use the config parameter to test different search variants
            best_move = chess_ai.search(
                board=board.copy(),
                depth=depth,
                time_limit=None,
                info_callback=capture_info,
                stop_event=None,
                config=config_type
            )
                
            search_time = time.time() - start_time
            
            # Get final metrics
            final_metrics = search_metrics[-1] if search_metrics else {}
            final_score = final_metrics.get('score', 0)
            total_nodes = final_metrics.get('nodes', nodes_searched)
            nps = int(total_nodes / max(search_time, 0.001))
            
            result = PerformanceResult(
                configuration=config_name,
                position_name=position_name,
                fen=fen,
                depth=depth,
                best_move=best_move or "none",
                total_nodes=total_nodes,
                search_time=search_time,
                nodes_per_second=nps,
                final_score=final_score,
                search_completed=True
            )
            
            print(f"✓ Completed: {best_move} | {total_nodes} nodes | {search_time:.3f}s | {nps:,} nps | Score: {final_score:+}")
            return result
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return PerformanceResult(
                configuration=config_name,
                position_name=position_name,
                fen=fen,
                depth=depth,
                best_move="error",
                total_nodes=0,
                search_time=0.0,
                nodes_per_second=0,
                final_score=0,
                search_completed=False
            )
    
    def run_comprehensive_test(self):
        """Run the complete performance test suite"""
        
        print("=" * 80)
        print("CHESS ENGINE PERFORMANCE TESTING SUITE v1.0")
        print("=" * 80)
        print(f"Testing {len(self.configurations)} configurations across {len(self.test_positions)} positions")
        print(f"Depths: {', '.join(map(str, self.test_depths))}")
        print()
        
        total_tests = len(self.configurations) * len(self.test_positions) * len(self.test_depths)
        current_test = 0
        
        for config_name, config_type in self.configurations:
            print(f"\\n{'='*20} {config_name.upper()} {'='*20}")
            
            for position_name, fen in self.test_positions:
                print(f"\\n--- {position_name} ---")
                
                for depth in self.test_depths:
                    current_test += 1
                    print(f"\\nTest {current_test}/{total_tests}")
                    
                    result = self.run_single_test(
                        config_name=config_name,
                        config_type=config_type,
                        position_name=position_name,
                        fen=fen,
                        depth=depth
                    )
                    
                    self.results.append(result)
        
        print("\\n" + "=" * 80)
        print("PERFORMANCE TESTING COMPLETED")
        print("=" * 80)
        
        self.analyze_results()
        self.export_results()
    
    def analyze_results(self):
        """Analyze and compare performance results"""
        
        print("\\nPERFORMANCE ANALYSIS")
        print("=" * 60)
        
        # Group results by configuration and depth
        config_stats = {}
        
        for result in self.results:
            if not result.search_completed:
                continue
                
            config = result.configuration
            depth = result.depth
            
            key = f"{config}_depth_{depth}"
            if key not in config_stats:
                config_stats[key] = {
                    'total_nodes': 0,
                    'total_time': 0.0,
                    'test_count': 0,
                    'avg_nps': []
                }
            
            stats = config_stats[key]
            stats['total_nodes'] += result.total_nodes
            stats['total_time'] += result.search_time
            stats['test_count'] += 1
            stats['avg_nps'].append(result.nodes_per_second)
        
        # Calculate averages and print comparison
        print("\\nConfiguration Comparison (Average per test):")
        print(f"{'Configuration':<20} {'Depth':<6} {'Avg Nodes':<12} {'Avg Time':<10} {'Avg NPS':<12} {'Tests':<6}")
        print("-" * 75)
        
        for config_name, _ in self.configurations:
            for depth in self.test_depths:
                key = f"{config_name}_depth_{depth}"
                if key in config_stats:
                    stats = config_stats[key]
                    avg_nodes = stats['total_nodes'] / stats['test_count']
                    avg_time = stats['total_time'] / stats['test_count']
                    avg_nps = sum(stats['avg_nps']) / len(stats['avg_nps'])
                    
                    print(f"{config_name:<20} {depth:<6} {avg_nodes:<12,.0f} {avg_time:<10.3f} {avg_nps:<12,.0f} {stats['test_count']:<6}")
        
        # Calculate efficiency gains
        print("\\nEfficiency Gains Analysis:")
        print("-" * 40)
        
        for depth in self.test_depths:
            print(f"\\nDepth {depth}:")
            
            base_key = f"Base Search_depth_{depth}"
            ab_key = f"Alpha-Beta_depth_{depth}"
            full_key = f"AB + Move Ordering_depth_{depth}"
            
            if all(key in config_stats for key in [base_key, ab_key, full_key]):
                base_nodes = config_stats[base_key]['total_nodes'] / config_stats[base_key]['test_count']
                ab_nodes = config_stats[ab_key]['total_nodes'] / config_stats[ab_key]['test_count']
                full_nodes = config_stats[full_key]['total_nodes'] / config_stats[full_key]['test_count']
                
                ab_reduction = (base_nodes - ab_nodes) / base_nodes * 100
                full_reduction = (base_nodes - full_nodes) / base_nodes * 100
                ordering_improvement = (ab_nodes - full_nodes) / ab_nodes * 100
                
                print(f"  Alpha-Beta vs Base: {ab_reduction:+.1f}% node reduction")
                print(f"  Full vs Base: {full_reduction:+.1f}% node reduction")
                print(f"  Move Ordering benefit: {ordering_improvement:+.1f}% additional reduction")
    
    def export_results(self):
        """Export detailed results to JSON"""
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"performance_test_results_{timestamp}.json"
        
        export_data = {
            "metadata": {
                "test_suite": "Chess Engine Performance Testing v1.0",
                "timestamp": timestamp,
                "total_tests": len(self.results),
                "configurations": [config[0] for config in self.configurations],
                "test_positions": [pos[0] for pos in self.test_positions],
                "test_depths": self.test_depths
            },
            "results": []
        }
        
        for result in self.results:
            export_data["results"].append({
                "configuration": result.configuration,
                "position_name": result.position_name,
                "fen": result.fen,
                "depth": result.depth,
                "best_move": result.best_move,
                "total_nodes": result.total_nodes,
                "search_time": result.search_time,
                "nodes_per_second": result.nodes_per_second,
                "final_score": result.final_score,
                "search_completed": result.search_completed
            })
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"\\nDetailed results exported to: {filename}")
        except Exception as e:
            print(f"Error exporting results: {e}")
    
    def print_position_comparison(self, position_name: str):
        """Print detailed comparison for a specific position"""
        
        print(f"\\nDetailed Analysis: {position_name}")
        print("-" * 60)
        print(f"{'Config':<20} {'Depth':<6} {'Nodes':<10} {'Time':<8} {'NPS':<10} {'Move':<8} {'Score':<8}")
        print("-" * 60)
        
        position_results = [r for r in self.results if r.position_name == position_name and r.search_completed]
        position_results.sort(key=lambda x: (x.depth, x.configuration))
        
        for result in position_results:
            print(f"{result.configuration:<20} {result.depth:<6} {result.total_nodes:<10,} {result.search_time:<8.3f} {result.nodes_per_second:<10,} {result.best_move:<8} {result.final_score:<8:+}")

def main():
    """Run the performance testing suite"""
    
    print("Starting Chess Engine Performance Testing...")
    print("This will test search efficiency improvements from optimizations.")
    print()
    
    suite = PerformanceTestSuite()
    suite.run_comprehensive_test()
    
    # Print detailed analysis for a few key positions
    print("\\n" + "=" * 80)
    print("DETAILED POSITION ANALYSIS")
    print("=" * 80)
    
    for position_name in ["Starting Position", "Tactical Puzzle", "Complex Middle Game"]:
        suite.print_position_comparison(position_name)

if __name__ == "__main__":
    main()
