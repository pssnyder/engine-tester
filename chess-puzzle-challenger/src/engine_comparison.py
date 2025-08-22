"""
Enhanced Puzzle Comparison Tool for Engine-Tester Integration
Focuses on V7P3R vs SlowMate competition with detailed tactical analysis
"""

import os
import json
import time
import chess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from src.database import PuzzleDatabase, Puzzle
from src.solver import PuzzleSolver
from src.visualization import create_performance_charts

@dataclass
class EngineComparisonResult:
    """Results from comparing two engines on puzzle solving"""
    engine_1_name: str
    engine_1_path: str
    engine_1_results: Dict[str, Any]
    engine_2_name: str  
    engine_2_path: str
    engine_2_results: Dict[str, Any]
    puzzle_set_info: Dict[str, Any]
    comparison_metrics: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]
    timestamp: str

class EnginePuzzleComparison:
    """Enhanced puzzle comparison tool for engine analysis"""
    
    def __init__(self, dashboard_data_dir: Optional[str] = None):
        """Initialize with optional custom dashboard data directory"""
        if dashboard_data_dir:
            self.dashboard_data_dir = Path(dashboard_data_dir)
        else:
            # Default to analytics dashboard data directory
            base_dir = Path(__file__).parent.parent.parent
            self.dashboard_data_dir = base_dir / "analytics_and_dashboard" / "dashboard" / "data"
        
        self.dashboard_data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_puzzle_set(self, themes: List[str], quantity: int, 
                      min_rating: int = 400, max_rating: int = 1200,
                      db_path: str = "puzzles.db") -> List[Puzzle]:
        """Get a specific set of puzzles for consistent testing"""
        print(f"Loading puzzle set: {quantity} puzzles, themes: {themes}, rating: {min_rating}-{max_rating}")
        
        puzzle_db = PuzzleDatabase(db_path)
        puzzles = puzzle_db.query_puzzles(
            themes=themes,
            min_rating=min_rating,
            max_rating=max_rating,
            quantity=quantity,
            strict_themes=False  # Use loose matching for variety
        )
        
        print(f"Found {len(puzzles)} puzzles matching criteria")
        return puzzles
    
    def test_engine_on_puzzles(self, engine_path: str, puzzles: List[Puzzle], 
                              think_time_ms: int = 2000, verbose: bool = True) -> Dict[str, Any]:
        """Test a single engine on a puzzle set and return detailed results"""
        engine_name = Path(engine_path).stem
        print(f"\n{'='*60}")
        print(f"Testing Engine: {engine_name}")
        print(f"Engine Path: {engine_path}")
        print(f"Puzzle Count: {len(puzzles)}")
        print(f"Think Time: {think_time_ms}ms")
        print(f"{'='*60}")
        
        solver = PuzzleSolver(engine_path)
        detailed_results = []
        
        try:
            start_time = time.time()
            
            for i, puzzle in enumerate(puzzles):
                puzzle_start = time.time()
                
                if verbose:
                    print(f"\n[{i+1}/{len(puzzles)}] Testing puzzle {puzzle.id}")
                    print(f"Rating: {puzzle.rating}, Themes: {puzzle.themes}")
                
                # Solve the puzzle and get detailed timing with error handling
                try:
                    solved = solver.solve_puzzle(puzzle, think_time_ms, verbose=False)
                    puzzle_time = time.time() - puzzle_start
                    error_type = None
                except TimeoutError as e:
                    solved = False
                    puzzle_time = time.time() - puzzle_start
                    error_type = "timeout"
                    if verbose:
                        print(f"⏰ TIMEOUT after {puzzle_time:.1f}s")
                except Exception as e:
                    solved = False
                    puzzle_time = time.time() - puzzle_start
                    error_type = f"error: {str(e)}"
                    if verbose:
                        print(f"❌ ERROR: {e}")
                
                # Record detailed result
                result_detail = {
                    'puzzle_id': puzzle.id,
                    'puzzle_rating': puzzle.rating,
                    'puzzle_themes': puzzle.themes,
                    'puzzle_fen': puzzle.fen,
                    'puzzle_moves': puzzle.moves,
                    'solved': solved,
                    'time_taken': puzzle_time,
                    'engine_name': engine_name,
                    'error_type': error_type
                }
                detailed_results.append(result_detail)
                
                if verbose:
                    status = "✓ SOLVED" if solved else "✗ FAILED"
                    print(f"{status} in {puzzle_time:.2f}s")
            
            total_time = time.time() - start_time
            
            # Get the solver's comprehensive results
            solver_results = solver.results.copy()
            solver_results['total_test_time'] = total_time
            solver_results['engine_name'] = engine_name
            solver_results['engine_path'] = engine_path
            solver_results['detailed_puzzles'] = detailed_results
            
            print(f"\nEngine {engine_name} completed {len(puzzles)} puzzles in {total_time:.2f}s")
            print(f"Success Rate: {solver_results['solved']}/{solver_results['total']} ({solver_results['solved']/solver_results['total']*100:.1f}%)")
            
            return solver_results
            
        finally:
            solver.close()
    
    def test_single_engine(self, engine_path: str, themes: List[str], quantity: int = 100,
                          min_rating: int = 400, max_rating: int = 1200,
                          think_time_ms: int = 2000, db_path: str = "puzzles.db"):
        """Test a single engine on puzzles and return results in a format compatible with comparison"""
        # Get puzzle set
        puzzles = self.get_puzzle_set(themes, quantity, min_rating, max_rating, db_path)
        
        # Test the engine
        results = self.test_engine_on_puzzles(engine_path, puzzles, think_time_ms)
        
        # Create a simple result object that matches what we need
        from collections import namedtuple
        SingleEngineResult = namedtuple('SingleEngineResult', [
            'engine_name', 'total', 'solved', 'time_taken', 'detailed_results'
        ])
        
        return SingleEngineResult(
            engine_name=results['engine_name'],
            total=results['total'],
            solved=results['solved'],
            time_taken=results['time_taken'],
            detailed_results=results['detailed_results']
        )
    
    def compare_engines(self, engine_1_path: str, engine_2_path: str,
                       themes: List[str], quantity: int = 1000,
                       min_rating: int = 400, max_rating: int = 1200,
                       think_time_ms: int = 2000, db_path: str = "puzzles.db") -> EngineComparisonResult:
        """Compare two engines on the same puzzle set"""
        
        # Get consistent puzzle set
        puzzles = self.get_puzzle_set(themes, quantity, min_rating, max_rating, db_path)
        
        if not puzzles:
            raise ValueError("No puzzles found matching the criteria")
        
        # Get engine names
        engine_1_name = Path(engine_1_path).stem
        engine_2_name = Path(engine_2_path).stem
        
        print(f"\n🏆 ENGINE COMPARISON: {engine_1_name} vs {engine_2_name}")
        print(f"Puzzle Set: {len(puzzles)} puzzles")
        print(f"Themes: {', '.join(themes) if themes else 'Any'}")
        print(f"Rating Range: {min_rating}-{max_rating}")
        
        # Test first engine
        print(f"\n⚔️  ROUND 1: Testing {engine_1_name}")
        engine_1_results = self.test_engine_on_puzzles(engine_1_path, puzzles, think_time_ms)
        
        # Test second engine  
        print(f"\n⚔️  ROUND 2: Testing {engine_2_name}")
        engine_2_results = self.test_engine_on_puzzles(engine_2_path, puzzles, think_time_ms)
        
        # Calculate comparison metrics
        comparison_metrics = self._calculate_comparison_metrics(engine_1_results, engine_2_results)
        
        # Merge detailed results for analysis
        detailed_results = self._merge_detailed_results(
            engine_1_results['detailed_puzzles'], 
            engine_2_results['detailed_puzzles']
        )
        
        # Create puzzle set info
        puzzle_set_info = {
            'total_puzzles': len(puzzles),
            'themes': themes,
            'min_rating': min_rating,
            'max_rating': max_rating,
            'think_time_ms': think_time_ms,
            'theme_distribution': self._analyze_theme_distribution(puzzles),
            'rating_distribution': self._analyze_rating_distribution(puzzles)
        }
        
        # Create comparison result
        result = EngineComparisonResult(
            engine_1_name=engine_1_name,
            engine_1_path=engine_1_path,
            engine_1_results=engine_1_results,
            engine_2_name=engine_2_name,
            engine_2_path=engine_2_path,
            engine_2_results=engine_2_results,
            puzzle_set_info=puzzle_set_info,
            comparison_metrics=comparison_metrics,
            detailed_results=detailed_results,
            timestamp=datetime.now().isoformat()
        )
        
        # Print comparison summary
        self._print_comparison_summary(result)
        
        return result
    
    def _calculate_comparison_metrics(self, results_1: Dict, results_2: Dict) -> Dict[str, Any]:
        """Calculate detailed comparison metrics between two engines"""
        metrics = {
            'overall_winner': None,
            'success_rate_difference': 0,
            'time_efficiency': {},
            'theme_performance': {},
            'rating_performance': {},
            'head_to_head': {
                'both_solved': 0,
                'engine_1_only': 0, 
                'engine_2_only': 0,
                'both_failed': 0
            }
        }
        
        # Overall success rates
        rate_1 = results_1['solved'] / results_1['total'] if results_1['total'] > 0 else 0
        rate_2 = results_2['solved'] / results_2['total'] if results_2['total'] > 0 else 0
        
        metrics['success_rate_difference'] = rate_1 - rate_2
        metrics['overall_winner'] = results_1['engine_name'] if rate_1 > rate_2 else results_2['engine_name']
        
        # Time efficiency (puzzles solved per second)
        time_1 = results_1.get('total_test_time', 1)
        time_2 = results_2.get('total_test_time', 1)
        
        metrics['time_efficiency'] = {
            results_1['engine_name']: results_1['solved'] / time_1,
            results_2['engine_name']: results_2['solved'] / time_2
        }
        
        # Theme performance comparison
        for theme in set(list(results_1['by_theme'].keys()) + list(results_2['by_theme'].keys())):
            theme_1 = results_1['by_theme'].get(theme, {'solved': 0, 'total': 0})
            theme_2 = results_2['by_theme'].get(theme, {'solved': 0, 'total': 0})
            
            rate_1 = theme_1['solved'] / theme_1['total'] if theme_1['total'] > 0 else 0
            rate_2 = theme_2['solved'] / theme_2['total'] if theme_2['total'] > 0 else 0
            
            metrics['theme_performance'][theme] = {
                results_1['engine_name']: rate_1,
                results_2['engine_name']: rate_2,
                'difference': rate_1 - rate_2,
                'winner': results_1['engine_name'] if rate_1 > rate_2 else results_2['engine_name']
            }
        
        # Rating performance comparison  
        for rating_range in set(list(results_1['by_rating'].keys()) + list(results_2['by_rating'].keys())):
            rating_1 = results_1['by_rating'].get(rating_range, {'solved': 0, 'total': 0})
            rating_2 = results_2['by_rating'].get(rating_range, {'solved': 0, 'total': 0})
            
            rate_1 = rating_1['solved'] / rating_1['total'] if rating_1['total'] > 0 else 0
            rate_2 = rating_2['solved'] / rating_2['total'] if rating_2['total'] > 0 else 0
            
            metrics['rating_performance'][rating_range] = {
                results_1['engine_name']: rate_1,
                results_2['engine_name']: rate_2,
                'difference': rate_1 - rate_2,
                'winner': results_1['engine_name'] if rate_1 > rate_2 else results_2['engine_name']
            }
        
        return metrics
    
    def _merge_detailed_results(self, results_1: List[Dict], results_2: List[Dict]) -> List[Dict]:
        """Merge detailed results from both engines for puzzle-by-puzzle analysis"""
        merged = []
        
        # Create a map for easy lookup
        results_2_map = {r['puzzle_id']: r for r in results_2}
        
        for r1 in results_1:
            puzzle_id = r1['puzzle_id']
            r2 = results_2_map.get(puzzle_id, {})
            
            merged_result = {
                'puzzle_id': puzzle_id,
                'puzzle_rating': r1['puzzle_rating'],
                'puzzle_themes': r1['puzzle_themes'],
                'puzzle_fen': r1['puzzle_fen'],
                'puzzle_moves': r1['puzzle_moves'],
                'engine_1_solved': r1['solved'],
                'engine_1_time': r1['time_taken'],
                'engine_2_solved': r2.get('solved', False),
                'engine_2_time': r2.get('time_taken', 0),
                'outcome': self._determine_puzzle_outcome(r1['solved'], r2.get('solved', False))
            }
            merged.append(merged_result)
        
        return merged
    
    def _determine_puzzle_outcome(self, engine_1_solved: bool, engine_2_solved: bool) -> str:
        """Determine the outcome of a puzzle comparison"""
        if engine_1_solved and engine_2_solved:
            return "both_solved"
        elif engine_1_solved and not engine_2_solved:
            return "engine_1_only"
        elif not engine_1_solved and engine_2_solved:
            return "engine_2_only"
        else:
            return "both_failed"
    
    def _analyze_theme_distribution(self, puzzles: List[Puzzle]) -> Dict[str, int]:
        """Analyze the distribution of themes in the puzzle set"""
        theme_counts = {}
        for puzzle in puzzles:
            if puzzle.themes:
                for theme in puzzle.themes.split():
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        return dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_rating_distribution(self, puzzles: List[Puzzle]) -> Dict[str, int]:
        """Analyze the rating distribution of puzzles"""
        rating_ranges = {}
        for puzzle in puzzles:
            range_key = f"{(puzzle.rating // 200) * 200}-{(puzzle.rating // 200 + 1) * 200}"
            rating_ranges[range_key] = rating_ranges.get(range_key, 0) + 1
        return dict(sorted(rating_ranges.items()))
    
    def _print_comparison_summary(self, result: EngineComparisonResult):
        """Print a comprehensive comparison summary"""
        print(f"\n{'='*80}")
        print(f"🏆 PUZZLE SOLVING COMPETITION RESULTS")
        print(f"{'='*80}")
        
        e1_name = result.engine_1_name
        e2_name = result.engine_2_name
        e1_results = result.engine_1_results
        e2_results = result.engine_2_results
        
        # Overall performance
        e1_rate = e1_results['solved'] / e1_results['total'] * 100
        e2_rate = e2_results['solved'] / e2_results['total'] * 100
        
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"  {e1_name}: {e1_results['solved']}/{e1_results['total']} ({e1_rate:.1f}%)")
        print(f"  {e2_name}: {e2_results['solved']}/{e2_results['total']} ({e2_rate:.1f}%)")
        
        winner = e1_name if e1_rate > e2_rate else e2_name
        margin = abs(e1_rate - e2_rate)
        print(f"  🏆 WINNER: {winner} (+{margin:.1f}%)")
        
        # Time efficiency
        print(f"\n⏱️  TIME EFFICIENCY:")
        e1_time = e1_results.get('total_test_time', 0)
        e2_time = e2_results.get('total_test_time', 0)
        print(f"  {e1_name}: {e1_time:.1f}s total, {e1_time/e1_results['total']:.2f}s per puzzle")
        print(f"  {e2_name}: {e2_time:.1f}s total, {e2_time/e2_results['total']:.2f}s per puzzle")
        
        # Top themes performance
        print(f"\n🎯 TOP THEME PERFORMANCE:")
        metrics = result.comparison_metrics
        top_themes = sorted(metrics['theme_performance'].items(), 
                           key=lambda x: max(x[1][e1_name], x[1][e2_name]), reverse=True)[:5]
        
        for theme, perf in top_themes:
            print(f"  {theme}: {e1_name} {perf[e1_name]*100:.1f}% vs {e2_name} {perf[e2_name]*100:.1f}%")
    
    def save_results(self, result: EngineComparisonResult, filename: Optional[str] = None) -> str:
        """Save comparison results to the dashboard data directory"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"puzzle_comparison_{result.engine_1_name}_vs_{result.engine_2_name}_{timestamp}.json"
        
        output_path = self.dashboard_data_dir / filename
        
        # Convert to dictionary for JSON serialization
        result_dict = asdict(result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")
        return str(output_path)
    
    def generate_tactical_skills_report(self, result: EngineComparisonResult) -> Dict[str, Any]:
        """Generate a detailed tactical skills analysis report"""
        report = {
            'summary': {
                'engine_1': result.engine_1_name,
                'engine_2': result.engine_2_name,
                'total_puzzles': result.puzzle_set_info['total_puzzles'],
                'timestamp': result.timestamp
            },
            'tactical_strengths': {},
            'tactical_weaknesses': {},
            'rating_analysis': {},
            'puzzle_difficulty_performance': {},
            'recommendations': []
        }
        
        # Analyze tactical strengths and weaknesses
        theme_perf = result.comparison_metrics['theme_performance']
        
        for engine_name in [result.engine_1_name, result.engine_2_name]:
            strengths = []
            weaknesses = []
            
            for theme, perf in theme_perf.items():
                engine_rate = perf[engine_name]
                if engine_rate >= 0.8:  # 80%+ success rate
                    strengths.append((theme, engine_rate))
                elif engine_rate <= 0.3:  # 30% or less success rate
                    weaknesses.append((theme, engine_rate))
            
            report['tactical_strengths'][engine_name] = sorted(strengths, key=lambda x: x[1], reverse=True)
            report['tactical_weaknesses'][engine_name] = sorted(weaknesses, key=lambda x: x[1])
        
        # Rating analysis
        rating_perf = result.comparison_metrics['rating_performance']
        for engine_name in [result.engine_1_name, result.engine_2_name]:
            report['rating_analysis'][engine_name] = {
                'best_rating_range': max(rating_perf.items(), key=lambda x: x[1][engine_name]),
                'worst_rating_range': min(rating_perf.items(), key=lambda x: x[1][engine_name]),
                'rating_consistency': self._calculate_rating_consistency(rating_perf, engine_name)
            }
        
        return report
    
    def _calculate_rating_consistency(self, rating_perf: Dict, engine_name: str) -> float:
        """Calculate consistency of engine performance across rating ranges"""
        rates = [perf[engine_name] for perf in rating_perf.values()]
        if not rates:
            return 0.0
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_rate = sum(rates) / len(rates)
        if mean_rate == 0:
            return 0.0
        
        variance = sum((rate - mean_rate) ** 2 for rate in rates) / len(rates)
        std_dev = variance ** 0.5
        return 1.0 - (std_dev / mean_rate)  # Return inverted CV as consistency score

def main():
    """Example usage of the engine comparison tool"""
    # Configuration
    engine_tester_base = Path(__file__).parent.parent.parent
    v7p3r_path = engine_tester_base / "engines" / "V7P3R" / "V7P3R_v5.1.exe"
    slowmate_path = engine_tester_base / "engines" / "SlowMate" / "SlowMate_v3.0.exe"
    db_path = str(Path(__file__).parent.parent / "puzzles.db")
    
    # Initialize comparison tool
    comparer = EnginePuzzleComparison()
    
    # Test parameters - as requested
    themes = ["middlegame", "endgame", "mate", "mateIn2", "mateIn3", "pin", "fork", "skewer"]
    quantity = 1000
    min_rating = 400
    max_rating = 1200
    
    print("🏁 Starting V7P3R vs SlowMate Tactical Skills Competition")
    print(f"Target Engines:")
    print(f"  🤖 V7P3R v5.1: {v7p3r_path}")
    print(f"  🧠 SlowMate v3.0: {slowmate_path}")
    
    # Verify engines exist
    if not v7p3r_path.exists():
        print(f"❌ V7P3R engine not found: {v7p3r_path}")
        return
    
    if not slowmate_path.exists():
        print(f"❌ SlowMate engine not found: {slowmate_path}")
        return
    
    try:
        # Run the comparison
        result = comparer.compare_engines(
            engine_1_path=str(v7p3r_path),
            engine_2_path=str(slowmate_path),
            themes=themes,
            quantity=quantity,
            min_rating=min_rating,
            max_rating=max_rating,
            think_time_ms=2000,  # 2 seconds thinking time
            db_path=db_path
        )
        
        # Save results to dashboard
        results_file = comparer.save_results(result)
        
        # Generate tactical skills report
        tactical_report = comparer.generate_tactical_skills_report(result)
        
        # Save tactical report
        report_filename = f"tactical_skills_report_{result.engine_1_name}_vs_{result.engine_2_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = comparer.dashboard_data_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(tactical_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Tactical skills report saved to: {report_path}")
        print(f"\n🎉 Competition completed successfully!")
        print(f"📁 All results saved to dashboard data directory")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        raise

if __name__ == "__main__":
    main()
