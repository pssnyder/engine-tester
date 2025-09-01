#!/usr/bin/env python3
"""
V7P3R Version Weakness Analyzer
Identifies where v9.1 (newest) is weakest compared to previous versions
and highlights key regression points between versions.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class MoveAnalysis:
    """Analysis of a single move across all engines"""
    position_id: str
    fen: str
    phase: str
    stockfish_best: str
    stockfish_quality: str
    centipawn_loss: int
    engines_moves: Dict[str, str]  # version -> move
    engines_evals: Dict[str, int]  # version -> evaluation
    engines_success: Dict[str, bool]  # version -> success

class VersionWeaknessAnalyzer:
    """Analyze V7P3R version-specific weaknesses and regressions"""
    
    def __init__(self, analysis_file: str):
        with open(analysis_file, 'r') as f:
            self.data = json.load(f)
        
        self.moves_data = []
        self.parse_moves_data()
    
    def parse_moves_data(self):
        """Parse raw JSON into structured move analysis"""
        for result in self.data['detailed_results']:
            engines_moves = {}
            engines_evals = {}
            engines_success = {}
            
            for analysis in result['engine_analyses']:
                version = analysis['engine_name']
                engines_moves[version] = analysis['move']
                engines_evals[version] = analysis['evaluation']
                engines_success[version] = analysis['success']
            
            move_analysis = MoveAnalysis(
                position_id=result['position_id'],
                fen=result['fen'],
                phase=result['phase'],
                stockfish_best=result['stockfish_grade']['best_move'],
                stockfish_quality=result['stockfish_grade']['move_quality'],
                centipawn_loss=result['stockfish_grade']['centipawn_loss'],
                engines_moves=engines_moves,
                engines_evals=engines_evals,
                engines_success=engines_success
            )
            self.moves_data.append(move_analysis)
    
    def analyze_v91_weaknesses(self) -> Dict[str, Any]:
        """Identify where v9.1 is weakest compared to other versions"""
        
        weaknesses = {
            'worse_than_stockfish': [],
            'disagreement_with_older_versions': [],
            'poor_evaluations': [],
            'blunders_and_mistakes': [],
            'tactical_failures': []
        }
        
        for move in self.moves_data:
            v91_move = move.engines_moves.get('v9.1', '')
            v91_success = move.engines_success.get('v9.1', False)
            
            if not v91_success:
                continue
                
            # Check if v9.1 move differs from Stockfish best
            if v91_move != move.stockfish_best:
                if move.stockfish_quality in ['mistake', 'blunder']:
                    weaknesses['worse_than_stockfish'].append({
                        'position': move.position_id,
                        'fen': move.fen[:50] + '...',
                        'v91_move': v91_move,
                        'stockfish_best': move.stockfish_best,
                        'quality': move.stockfish_quality,
                        'centipawn_loss': move.centipawn_loss
                    })
            
            # Check disagreement with successful older versions
            older_versions = ['v7.0', 'v8.0', 'v9.0']
            successful_older_moves = {v: move.engines_moves[v] for v in older_versions 
                                    if move.engines_success.get(v, False) and move.engines_moves.get(v)}
            
            if successful_older_moves:
                # Find most common move among successful older versions
                move_counts = defaultdict(int)
                for old_move in successful_older_moves.values():
                    move_counts[old_move] += 1
                
                if move_counts:
                    consensus_move = max(move_counts.items(), key=lambda x: x[1])[0]
                    
                    if v91_move != consensus_move and move_counts[consensus_move] >= 2:
                        weaknesses['disagreement_with_older_versions'].append({
                            'position': move.position_id,
                            'fen': move.fen[:50] + '...',
                            'v91_move': v91_move,
                            'older_consensus': consensus_move,
                            'supporting_versions': [v for v, m in successful_older_moves.items() if m == consensus_move],
                            'stockfish_quality': move.stockfish_quality
                        })
        
        return weaknesses
    
    def find_regression_points(self) -> Dict[str, List[Dict]]:
        """Find specific version where regressions occurred"""
        
        regressions = {
            'v8.0_vs_v7.0': [],
            'v9.0_vs_v8.0': [],
            'v9.1_vs_v9.0': []
        }
        
        for move in self.moves_data:
            # Check v8.0 vs v7.0 regression
            if (move.engines_success.get('v7.0') and move.engines_success.get('v8.0') and
                move.engines_moves.get('v7.0') and move.engines_moves.get('v8.0')):
                
                v7_move = move.engines_moves['v7.0']
                v8_move = move.engines_moves['v8.0']
                
                if v7_move == move.stockfish_best and v8_move != move.stockfish_best:
                    regressions['v8.0_vs_v7.0'].append({
                        'position': move.position_id,
                        'fen': move.fen[:50] + '...',
                        'v7_move': v7_move,
                        'v8_move': v8_move,
                        'stockfish_best': move.stockfish_best,
                        'regression': 'v8.0 abandoned correct v7.0 move'
                    })
            
            # Check v9.0 vs v8.0 regression
            if (move.engines_success.get('v8.0') and move.engines_success.get('v9.0') and
                move.engines_moves.get('v8.0') and move.engines_moves.get('v9.0')):
                
                v8_move = move.engines_moves['v8.0']
                v9_move = move.engines_moves['v9.0']
                
                if v8_move == move.stockfish_best and v9_move != move.stockfish_best:
                    regressions['v9.0_vs_v8.0'].append({
                        'position': move.position_id,
                        'fen': move.fen[:50] + '...',
                        'v8_move': v8_move,
                        'v9_move': v9_move,
                        'stockfish_best': move.stockfish_best,
                        'regression': 'v9.0 abandoned correct v8.0 move'
                    })
            
            # Check v9.1 vs v9.0 regression
            if (move.engines_success.get('v9.0') and move.engines_success.get('v9.1') and
                move.engines_moves.get('v9.0') and move.engines_moves.get('v9.1')):
                
                v9_move = move.engines_moves['v9.0']
                v91_move = move.engines_moves['v9.1']
                
                if v9_move == move.stockfish_best and v91_move != move.stockfish_best:
                    regressions['v9.1_vs_v9.0'].append({
                        'position': move.position_id,
                        'fen': move.fen[:50] + '...',
                        'v9_move': v9_move,
                        'v91_move': v91_move,
                        'stockfish_best': move.stockfish_best,
                        'regression': 'v9.1 abandoned correct v9.0 move'
                    })
        
        return regressions
    
    def analyze_evaluation_patterns(self) -> Dict[str, Any]:
        """Analyze evaluation patterns and confidence issues"""
        
        patterns = {
            'evaluation_swings': [],
            'overconfidence': [],
            'underconfidence': [],
            'version_comparison': {}
        }
        
        # Compare evaluation patterns across versions
        for move in self.moves_data:
            successful_engines = {v: eval_val for v, eval_val in move.engines_evals.items() 
                                if move.engines_success.get(v, False)}
            
            if len(successful_engines) >= 3:
                evals = list(successful_engines.values())
                eval_range = max(evals) - min(evals)
                
                if eval_range > 50000:  # Large evaluation swings
                    patterns['evaluation_swings'].append({
                        'position': move.position_id,
                        'fen': move.fen[:50] + '...',
                        'evaluations': successful_engines,
                        'range': eval_range,
                        'stockfish_quality': move.stockfish_quality
                    })
        
        return patterns
    
    def generate_weakness_report(self) -> Dict[str, Any]:
        """Generate comprehensive weakness analysis report"""
        
        print("=" * 80)
        print("V7P3R VERSION WEAKNESS ANALYSIS")
        print("=" * 80)
        
        weaknesses = self.analyze_v91_weaknesses()
        regressions = self.find_regression_points()
        eval_patterns = self.analyze_evaluation_patterns()
        
        report = {
            'v91_weaknesses': weaknesses,
            'version_regressions': regressions,
            'evaluation_patterns': eval_patterns,
            'summary': {
                'total_positions': len(self.moves_data),
                'v91_disagreements': len(weaknesses['disagreement_with_older_versions']),
                'stockfish_mismatches': len(weaknesses['worse_than_stockfish']),
                'major_regressions': sum(len(r) for r in regressions.values())
            }
        }
        
        self.print_weakness_summary(report)
        
        return report
    
    def print_weakness_summary(self, report: Dict[str, Any]):
        """Print formatted weakness analysis summary"""
        
        print(f"\n🎯 V9.1 WEAKNESS ANALYSIS")
        print(f"📊 Total Positions: {report['summary']['total_positions']}")
        print(f"⚠️  V9.1 Disagreements with Older Versions: {report['summary']['v91_disagreements']}")
        print(f"❌ Stockfish Mismatches: {report['summary']['stockfish_mismatches']}")
        print(f"📉 Major Regressions: {report['summary']['major_regressions']}")
        
        # V9.1 vs Older Versions Disagreements
        if report['v91_weaknesses']['disagreement_with_older_versions']:
            print(f"\n🔍 V9.1 DISAGREES WITH OLDER VERSIONS:")
            for disagree in report['v91_weaknesses']['disagreement_with_older_versions']:
                print(f"  Position: {disagree['position']}")
                print(f"  FEN: {disagree['fen']}")
                print(f"  v9.1 chose: {disagree['v91_move']}")
                print(f"  Older consensus: {disagree['older_consensus']}")
                print(f"  Supporting: {', '.join(disagree['supporting_versions'])}")
                print(f"  Stockfish quality: {disagree['stockfish_quality']}")
                print()
        
        # Version Regressions
        for version_pair, regressions in report['version_regressions'].items():
            if regressions:
                print(f"\n📉 {version_pair.upper()} REGRESSIONS:")
                for reg in regressions:
                    print(f"  Position: {reg['position']}")
                    print(f"  FEN: {reg['fen']}")
                    print(f"  Regression: {reg['regression']}")
                    print(f"  Stockfish best: {reg['stockfish_best']}")
                    print()
        
        # Evaluation Patterns
        if report['evaluation_patterns']['evaluation_swings']:
            print(f"\n⚡ LARGE EVALUATION SWINGS:")
            for swing in report['evaluation_patterns']['evaluation_swings']:
                print(f"  Position: {swing['position']}")
                print(f"  FEN: {swing['fen']}")
                print(f"  Eval range: {swing['range']:,} cp")
                print(f"  Quality: {swing['stockfish_quality']}")
                print()

def main():
    """Run V7P3R weakness analysis"""
    
    # Find most recent analysis file
    analysis_files = list(Path('.').glob('v7p3r_regression_analysis_*.json'))
    if not analysis_files:
        print("No regression analysis files found!")
        print("Run historical_game_regression_tester.py first.")
        return
    
    latest_file = max(analysis_files, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing: {latest_file}")
    
    analyzer = VersionWeaknessAnalyzer(str(latest_file))
    report = analyzer.generate_weakness_report()
    
    # Save detailed report
    output_file = f"v7p3r_weakness_analysis_{latest_file.stem.split('_')[-1]}.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed weakness analysis saved to: {output_file}")
    print("\n🔍 KEY INSIGHTS:")
    print("  • Look for patterns where v9.1 differs from successful older versions")
    print("  • Check regressions between major version releases")
    print("  • Identify evaluation confidence issues")
    print("  • Focus on tactical vs positional disagreements")

if __name__ == "__main__":
    main()
