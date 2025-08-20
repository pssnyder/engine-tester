#!/usr/bin/env python3
"""
Data Quality Checker for Chess Engine Analytics

Performs comprehensive data quality checks on:
- Behavioral analysis consistency
- Metric correlation validation
- Empty category identification
- Decisiveness score validation
- Engine family consistency checks
"""

import json
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any
import os

class DataQualityChecker:
    def __init__(self, results_dir='results'):
        self.results_dir = results_dir
        self.behavioral_data = self.load_behavioral_data()
        self.unified_data = self.load_unified_data()
        self.issues = []
        
    def load_behavioral_data(self) -> Dict:
        """Load behavioral analysis data"""
        try:
            with open(os.path.join(self.results_dir, 'behavioral_analysis.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: No behavioral analysis data found")
            return {}
    
    def load_unified_data(self) -> Dict:
        """Load unified tournament data"""
        try:
            with open(os.path.join(self.results_dir, 'unified_tournament_analysis.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: No unified tournament data found")
            return {}
    
    def check_behavioral_data_completeness(self) -> Dict[str, Any]:
        """Check for missing or incomplete behavioral data"""
        print("=== Behavioral Data Completeness Check ===")
        
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            self.issues.append("No behavioral profiles found")
            return {"status": "failed", "reason": "No behavioral data"}
        
        profiles = self.behavioral_data['behavioral_profiles']
        categories = self.behavioral_data.get('engine_categories', {})
        
        results = {
            "total_engines": len(profiles),
            "empty_profiles": 0,
            "missing_scores": 0,
            "missing_performance": 0,
            "missing_patterns": 0,
            "category_stats": {},
            "incomplete_engines": []
        }
        
        for engine, profile in profiles.items():
            if not profile:
                results["empty_profiles"] += 1
                results["incomplete_engines"].append(f"{engine}: Empty profile")
                continue
            
            # Check required sections
            if 'behavioral_scores' not in profile or not profile['behavioral_scores']:
                results["missing_scores"] += 1
                results["incomplete_engines"].append(f"{engine}: Missing behavioral scores")
            
            if 'performance_metrics' not in profile or not profile['performance_metrics']:
                results["missing_performance"] += 1
                results["incomplete_engines"].append(f"{engine}: Missing performance metrics")
            
            if 'signature_patterns' not in profile or not profile['signature_patterns']:
                results["missing_patterns"] += 1
                results["incomplete_engines"].append(f"{engine}: Missing signature patterns")
        
        # Check categories
        for category, engines in categories.items():
            results["category_stats"][category] = len(engines)
            if len(engines) == 0:
                self.issues.append(f"Empty category: {category}")
        
        print(f"Total engines: {results['total_engines']}")
        print(f"Empty profiles: {results['empty_profiles']}")
        print(f"Missing scores: {results['missing_scores']}")
        print(f"Missing performance: {results['missing_performance']}")
        print(f"Missing patterns: {results['missing_patterns']}")
        
        return results
    
    def validate_decisiveness_scores(self) -> Dict[str, Any]:
        """Validate that decisiveness scores correlate with actual game outcomes"""
        print("\n=== Decisiveness Score Validation ===")
        
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return {"status": "failed", "reason": "No behavioral data"}
        
        profiles = self.behavioral_data['behavioral_profiles']
        validation_results = {
            "engines_checked": 0,
            "correlation_issues": [],
            "high_decisiveness_low_checkmates": [],
            "low_decisiveness_high_checkmates": [],
            "score_distribution": defaultdict(int)
        }
        
        for engine, profile in profiles.items():
            if not profile or 'behavioral_scores' not in profile:
                continue
                
            validation_results["engines_checked"] += 1
            scores = profile.get('behavioral_scores', {})
            perf = profile.get('performance_metrics', {})
            patterns = profile.get('signature_patterns', {})
            
            decisiveness = scores.get('decisiveness', 0)
            win_rate = perf.get('win_rate', 0)
            
            # Categorize decisiveness scores
            if decisiveness < 20:
                validation_results["score_distribution"]["low"] += 1
            elif decisiveness < 50:
                validation_results["score_distribution"]["medium"] += 1
            else:
                validation_results["score_distribution"]["high"] += 1
            
            # Check for correlation issues
            if decisiveness > 70 and win_rate < 30:
                validation_results["high_decisiveness_low_checkmates"].append({
                    "engine": engine,
                    "decisiveness": decisiveness,
                    "win_rate": win_rate
                })
            
            if decisiveness < 30 and win_rate > 70:
                validation_results["low_decisiveness_high_checkmates"].append({
                    "engine": engine,
                    "decisiveness": decisiveness,
                    "win_rate": win_rate
                })
        
        print(f"Engines checked: {validation_results['engines_checked']}")
        print(f"Score distribution: {dict(validation_results['score_distribution'])}")
        print(f"Correlation issues found: {len(validation_results['correlation_issues'])}")
        
        return validation_results
    
    def analyze_cece_family(self) -> Dict[str, Any]:
        """Deep analysis of Cece and Cecilia engine families"""
        print("\n=== Cece/Cecilia Family Analysis ===")
        
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return {"status": "failed", "reason": "No behavioral data"}
        
        profiles = self.behavioral_data['behavioral_profiles']
        
        # Find Cece and Cecilia engines
        cece_engines = {}
        cecilia_engines = {}
        
        for engine, profile in profiles.items():
            if not profile:
                continue
                
            engine_lower = engine.lower()
            if 'cece' in engine_lower and 'cecilia' not in engine_lower:
                cece_engines[engine] = profile
            elif 'cecilia' in engine_lower:
                cecilia_engines[engine] = profile
        
        analysis = {
            "cece_variants": len(cece_engines),
            "cecilia_variants": len(cecilia_engines),
            "cece_analysis": {},
            "cecilia_analysis": {},
            "family_comparison": {}
        }
        
        # Analyze Cece engines
        for engine, profile in cece_engines.items():
            scores = profile.get('behavioral_scores', {})
            perf = profile.get('performance_metrics', {})
            patterns = profile.get('signature_patterns', {})
            
            analysis["cece_analysis"][engine] = {
                "aggression": scores.get('aggression', 0),
                "decisiveness": scores.get('decisiveness', 0),
                "piece_diversity": scores.get('piece_diversity', 0),
                "win_rate": perf.get('win_rate', 0),
                "avg_game_length": perf.get('avg_game_length', 0),
                "capture_rate": perf.get('capture_rate', 0),
                "primary_style": profile.get('playing_style', {}).get('primary_style', 'unknown'),
                "favorite_pieces": patterns.get('favorite_pieces', {}),
                "total_games": profile.get('total_games', 0)
            }
        
        # Analyze Cecilia engines
        for engine, profile in cecilia_engines.items():
            scores = profile.get('behavioral_scores', {})
            perf = profile.get('performance_metrics', {})
            patterns = profile.get('signature_patterns', {})
            
            analysis["cecilia_analysis"][engine] = {
                "aggression": scores.get('aggression', 0),
                "decisiveness": scores.get('decisiveness', 0),
                "piece_diversity": scores.get('piece_diversity', 0),
                "win_rate": perf.get('win_rate', 0),
                "avg_game_length": perf.get('avg_game_length', 0),
                "capture_rate": perf.get('capture_rate', 0),
                "primary_style": profile.get('playing_style', {}).get('primary_style', 'unknown'),
                "favorite_pieces": patterns.get('favorite_pieces', {}),
                "total_games": profile.get('total_games', 0)
            }
        
        # Compare families
        if cece_engines and cecilia_engines:
            cece_avg_aggression = np.mean([data['aggression'] for data in analysis["cece_analysis"].values()])
            cecilia_avg_aggression = np.mean([data['aggression'] for data in analysis["cecilia_analysis"].values()])
            
            cece_avg_winrate = np.mean([data['win_rate'] for data in analysis["cece_analysis"].values()])
            cecilia_avg_winrate = np.mean([data['win_rate'] for data in analysis["cecilia_analysis"].values()])
            
            analysis["family_comparison"] = {
                "cece_avg_aggression": cece_avg_aggression,
                "cecilia_avg_aggression": cecilia_avg_aggression,
                "cece_avg_winrate": cece_avg_winrate,
                "cecilia_avg_winrate": cecilia_avg_winrate,
                "aggression_difference": cece_avg_aggression - cecilia_avg_aggression,
                "winrate_difference": cece_avg_winrate - cecilia_avg_winrate
            }
        
        print(f"Cece variants found: {len(cece_engines)}")
        print(f"Cecilia variants found: {len(cecilia_engines)}")
        
        if analysis["family_comparison"]:
            comp = analysis["family_comparison"]
            print(f"Average aggression - Cece: {comp['cece_avg_aggression']:.1f}, Cecilia: {comp['cecilia_avg_aggression']:.1f}")
            print(f"Average win rate - Cece: {comp['cece_avg_winrate']:.1f}%, Cecilia: {comp['cecilia_avg_winrate']:.1f}%")
        
        return analysis
    
    def check_metric_correlations(self) -> Dict[str, Any]:
        """Check for logical correlations between metrics"""
        print("\n=== Metric Correlation Check ===")
        
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return {"status": "failed", "reason": "No behavioral data"}
        
        profiles = self.behavioral_data['behavioral_profiles']
        
        # Extract metrics for correlation analysis
        metrics_data = []
        for engine, profile in profiles.items():
            if not profile:
                continue
                
            scores = profile.get('behavioral_scores', {})
            perf = profile.get('performance_metrics', {})
            
            metrics_data.append({
                'engine': engine,
                'aggression': scores.get('aggression', 0),
                'decisiveness': scores.get('decisiveness', 0),
                'piece_diversity': scores.get('piece_diversity', 0),
                'win_rate': perf.get('win_rate', 0),
                'capture_rate': perf.get('capture_rate', 0),
                'check_rate': perf.get('check_rate', 0),
                'avg_game_length': perf.get('avg_game_length', 0)
            })
        
        if not metrics_data:
            return {"status": "failed", "reason": "No metrics data"}
        
        df = pd.DataFrame(metrics_data)
        
        # Calculate correlations
        correlation_matrix = df[['aggression', 'decisiveness', 'piece_diversity', 
                               'win_rate', 'capture_rate', 'check_rate']].corr()
        
        # Check for expected correlations
        expected_correlations = [
            ('aggression', 'capture_rate', 0.3, "Aggressive engines should capture more"),
            ('aggression', 'check_rate', 0.2, "Aggressive engines should give more checks"),
            ('decisiveness', 'win_rate', 0.3, "Decisive engines should win more"),
            ('piece_diversity', 'win_rate', 0.2, "More diverse engines might be stronger")
        ]
        
        correlation_results = {
            "correlations_found": {},
            "weak_correlations": [],
            "strong_unexpected": []
        }
        
        for var1, var2, expected_min, description in expected_correlations:
            if var1 in correlation_matrix.columns and var2 in correlation_matrix.columns:
                actual_corr = correlation_matrix.loc[var1, var2]
                
                # Handle potential nan or non-numeric values
                try:
                    if pd.isna(actual_corr):
                        actual_corr_float = 0.0
                    else:
                        actual_corr_float = float(str(actual_corr))
                except (ValueError, TypeError):
                    actual_corr_float = 0.0
                    
                correlation_results["correlations_found"][f"{var1}_vs_{var2}"] = {
                    "actual": actual_corr_float,
                    "expected_min": expected_min,
                    "description": description,
                    "meets_expectation": actual_corr_float >= expected_min
                }
                
                if actual_corr_float < expected_min:
                    correlation_results["weak_correlations"].append({
                        "pair": f"{var1} vs {var2}",
                        "actual": actual_corr_float,
                        "expected": expected_min,
                        "description": description
                    })
        
        print(f"Correlations checked: {len(correlation_results['correlations_found'])}")
        print(f"Weak correlations found: {len(correlation_results['weak_correlations'])}")
        
        return correlation_results
    
    def generate_quality_report(self) -> str:
        """Generate a comprehensive data quality report"""
        print("\n" + "="*50)
        print("GENERATING COMPREHENSIVE DATA QUALITY REPORT")
        print("="*50)
        
        # Run all checks
        completeness = self.check_behavioral_data_completeness()
        decisiveness = self.validate_decisiveness_scores()
        cece_analysis = self.analyze_cece_family()
        correlations = self.check_metric_correlations()
        
        # Generate report
        report = []
        report.append("# Chess Engine Analytics - Data Quality Report")
        report.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Completeness section
        report.append("## Data Completeness")
        report.append(f"- Total engines: {completeness.get('total_engines', 0)}")
        report.append(f"- Empty profiles: {completeness.get('empty_profiles', 0)}")
        report.append(f"- Missing behavioral scores: {completeness.get('missing_scores', 0)}")
        report.append(f"- Missing performance metrics: {completeness.get('missing_performance', 0)}")
        report.append("")
        
        # Cece/Cecilia analysis
        report.append("## Cece/Cecilia Family Analysis")
        report.append(f"- Cece variants: {cece_analysis.get('cece_variants', 0)}")
        report.append(f"- Cecilia variants: {cece_analysis.get('cecilia_variants', 0)}")
        
        if 'family_comparison' in cece_analysis and cece_analysis['family_comparison']:
            comp = cece_analysis['family_comparison']
            report.append(f"- Average aggression difference: {comp.get('aggression_difference', 0):.1f}")
            report.append(f"- Average win rate difference: {comp.get('winrate_difference', 0):.1f}%")
        
        report.append("")
        
        # Issues found
        if self.issues:
            report.append("## Issues Identified")
            for issue in self.issues:
                report.append(f"- {issue}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        if completeness.get('empty_profiles', 0) > 0:
            report.append("- Re-run behavioral analysis to fill empty profiles")
        if decisiveness.get('correlation_issues', []):
            report.append("- Review decisiveness calculation methodology")
        if correlations.get('weak_correlations', []):
            report.append("- Investigate weak metric correlations")
        
        return '\n'.join(report)

def main():
    """Run data quality checks and generate report"""
    checker = DataQualityChecker()
    
    # Generate and save report
    quality_report = checker.generate_quality_report()
    
    report_path = "results/data_quality_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(quality_report)
    
    print(f"\nData quality report saved to: {report_path}")
    
    # Also print summary to console
    print("\n" + "="*50)
    print("SUMMARY OF FINDINGS")
    print("="*50)
    
    if checker.issues:
        print("ISSUES FOUND:")
        for issue in checker.issues:
            print(f"  - {issue}")
    else:
        print("No major issues found.")
    
    print("\nDetailed report saved for review.")

if __name__ == "__main__":
    main()
