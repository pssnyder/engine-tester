#!/usr/bin/env python3
"""
Results Appendix Analyzer

Programmatically identifies data anomalies, version regressions, and performance
inconsistencies in tournament results. Combines automated analysis with manual
insights from results_appendix.json for comprehensive data interpretation.
"""

import json
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class VersionInfo:
    engine_name: str
    major: int
    minor: int
    patch: int
    suffix: str
    full_name: str

class AnomalyDetector:
    def __init__(self, tournament_data_path: str, engine_test_path: str, appendix_path: str):
        # Load data files
        with open(tournament_data_path, 'r') as f:
            self.tournament_data = json.load(f)
        
        with open(engine_test_path, 'r') as f:
            self.engine_test_data = json.load(f)
            
        with open(appendix_path, 'r') as f:
            self.appendix = json.load(f)
    
    def parse_version(self, engine_name: str) -> VersionInfo:
        """Parse engine name into version components for comparison"""
        # Handle different naming patterns
        patterns = [
            r'SlowMate_v(\d+)\.(\d+)\.(\d+)_(.+)',     # v0.1.02_Feature
            r'SlowMate_v(\d+)\.(\d+)\.(\d+)\.(\d+)_(.+)',  # v0.1.0.1_Feature  
            r'SlowMate_v(\d+)\.(\d+)\.(\d+)',         # v0.1.0
            r'SlowMate_v(\d+)\.(\d+)_(.+)',           # v0.2_BETA
            r'Cece_v(\d+)\.(\d+)',                    # Cece_v1.0
            r'Cecilia_v(\d+)\.(\d+)\.(\d+)_(.+)'      # Cecilia_v0.1.0_Basic
        ]
        
        for pattern in patterns:
            match = re.match(pattern, engine_name)
            if match:
                groups = match.groups()
                if 'SlowMate' in engine_name:
                    if len(groups) == 4 and '.' not in groups[2]:  # v0.1.02_Feature
                        return VersionInfo(engine_name, int(groups[0]), int(groups[1]), int(groups[2]), groups[3], engine_name)
                    elif len(groups) == 5:  # v0.1.0.1_Feature
                        return VersionInfo(engine_name, int(groups[0]), int(groups[1]), int(groups[2]) * 10 + int(groups[3]), groups[4], engine_name)
                    elif len(groups) == 3 and groups[2]:  # v0.2_BETA
                        return VersionInfo(engine_name, int(groups[0]), int(groups[1]), 0, groups[2], engine_name)
                elif 'Cece' in engine_name:
                    return VersionInfo(engine_name, int(groups[0]), int(groups[1]), 0, '', engine_name)
                elif 'Cecilia' in engine_name:
                    return VersionInfo(engine_name, int(groups[0]), int(groups[1]), int(groups[2]), groups[3], engine_name)
        
        # Fallback for unparseable names
        return VersionInfo(engine_name, 0, 0, 0, '', engine_name)
    
    def detect_version_regressions(self) -> List[Dict[str, Any]]:
        """Find cases where newer versions perform worse than older ones"""
        regressions = []
        
        # Group engines by family (SlowMate, Cece, Cecilia)
        families = {}
        for engine_data in self.tournament_data['all_engines'].values():
            engine_name = engine_data['name']
            family = engine_name.split('_')[0]
            if family not in families:
                families[family] = []
            families[family].append(engine_data)
        
        for family_name, engines in families.items():
            # Sort by version
            versioned_engines = []
            for engine in engines:
                version_info = self.parse_version(engine['name'])
                versioned_engines.append((version_info, engine))
            
            # Sort by major.minor.patch
            versioned_engines.sort(key=lambda x: (x[0].major, x[0].minor, x[0].patch))
            
            # Look for regressions
            for i in range(1, len(versioned_engines)):
                prev_version, prev_engine = versioned_engines[i-1]
                curr_version, curr_engine = versioned_engines[i]
                
                # Skip if not sequential versions or different major versions with large gaps
                if curr_version.major - prev_version.major > 1:
                    continue
                
                # Calculate regression metrics
                win_rate_drop = prev_engine['win_rate'] - curr_engine['win_rate']
                points_drop = prev_engine['points'] - curr_engine['points']
                
                if win_rate_drop > 15.0 or points_drop > 5.0:  # Significant regression thresholds
                    regressions.append({
                        'type': 'version_regression',
                        'severity': 'high' if win_rate_drop > 30.0 else 'medium',
                        'previous_version': prev_engine['name'],
                        'current_version': curr_engine['name'],
                        'win_rate_drop': round(win_rate_drop, 1),
                        'points_drop': round(points_drop, 1),
                        'analysis': f"Version {curr_version.major}.{curr_version.minor}.{curr_version.patch} shows {win_rate_drop:.1f}% win rate drop from previous version"
                    })
        
        return regressions
    
    def detect_feature_mismatches(self) -> List[Dict[str, Any]]:
        """Find engines whose performance doesn't match their stated features"""
        mismatches = []
        
        # Define feature expectations
        feature_expectations = {
            'Tactical': {'min_decisive_rate': 20.0, 'context': 'should excel at finding checkmates'},
            'Endgame': {'min_decisive_rate': 25.0, 'context': 'should be superior at endgame checkmates'},
            'Intelligence': {'min_win_rate': 60.0, 'context': 'should show improved overall play'},
            'Enhanced': {'min_win_rate': 55.0, 'context': 'should outperform basic versions'},
            'Time_Management': {'min_win_rate': 50.0, 'context': 'should play more efficiently'},
            'Stable': {'min_win_rate': 45.0, 'context': 'should be reliable performer'}
        }
        
        for engine_data in self.tournament_data['all_engines'].values():
            engine_name = engine_data['name']
            
            for feature, expectations in feature_expectations.items():
                if feature in engine_name or feature.lower() in engine_name.lower():
                    failed_expectations = []
                    
                    if 'min_decisive_rate' in expectations:
                        if engine_data['decisive_win_rate'] < expectations['min_decisive_rate']:
                            failed_expectations.append(f"decisive win rate {engine_data['decisive_win_rate']:.1f}% < expected {expectations['min_decisive_rate']:.1f}%")
                    
                    if 'min_win_rate' in expectations:
                        if engine_data['win_rate'] < expectations['min_win_rate']:
                            failed_expectations.append(f"win rate {engine_data['win_rate']:.1f}% < expected {expectations['min_win_rate']:.1f}%")
                    
                    if failed_expectations:
                        mismatches.append({
                            'type': 'feature_mismatch',
                            'engine': engine_name,
                            'claimed_feature': feature,
                            'expectation': expectations['context'],
                            'failures': failed_expectations,
                            'analysis': f"Engine claiming '{feature}' feature underperforms expectations"
                        })
        
        return mismatches
    
    def detect_data_quality_issues(self) -> List[Dict[str, Any]]:
        """Identify data quality problems like inflated performance from broken opponents"""
        issues = []
        
        # Find engines with 0% win rate (completely broken)
        broken_engines = [
            engine_data['name'] for engine_data in self.tournament_data['all_engines'].values()
            if engine_data['win_rate'] == 0.0
        ]
        
        # Find engines with suspiciously high performance that might be inflated
        for engine_data in self.tournament_data['all_engines'].values():
            engine_name = engine_data['name']
            
            # Random-move engines shouldn't have high win rates
            if 'DELTA' in engine_name and 'v0.0' in engine_name:
                if engine_data['win_rate'] > 30.0:
                    issues.append({
                        'type': 'inflated_performance',
                        'engine': engine_name,
                        'win_rate': engine_data['win_rate'],
                        'analysis': f"Random-move engine has {engine_data['win_rate']:.1f}% win rate, likely inflated by broken opponents",
                        'recommendation': 'Filter games against 0% win rate opponents'
                    })
            
            # Very early versions shouldn't outperform later ones significantly
            if 'v0.0' in engine_name and engine_data['win_rate'] > 65.0:
                issues.append({
                    'type': 'version_inversion',
                    'engine': engine_name,
                    'win_rate': engine_data['win_rate'],
                    'analysis': f"Very early version achieving {engine_data['win_rate']:.1f}% win rate suggests opponent quality issues"
                })
        
        return issues
    
    def cross_reference_uci_failures(self) -> List[Dict[str, Any]]:
        """Cross-reference tournament performance with UCI test failures"""
        correlations = []
        
        # Create lookup for UCI test results
        uci_results = {}
        for engine_test in self.engine_test_data:
            engine_name = engine_test['engine']
            uci_results[engine_name] = engine_test['critical_pass']
        
        for engine_data in self.tournament_data['all_engines'].values():
            engine_name = engine_data['name']
            
            # Check if we have UCI test data for this engine
            if engine_name in uci_results:
                uci_pass = uci_results[engine_name]
                tournament_win_rate = engine_data['win_rate']
                
                # Look for mismatches
                if not uci_pass and tournament_win_rate > 5.0:
                    correlations.append({
                        'type': 'uci_tournament_mismatch',
                        'engine': engine_name,
                        'uci_status': 'FAIL',
                        'tournament_win_rate': tournament_win_rate,
                        'analysis': f"Failed UCI tests but has {tournament_win_rate:.1f}% tournament win rate - data inconsistency"
                    })
                elif uci_pass and tournament_win_rate < 10.0:
                    correlations.append({
                        'type': 'uci_tournament_mismatch',
                        'engine': engine_name,
                        'uci_status': 'PASS',
                        'tournament_win_rate': tournament_win_rate,
                        'analysis': f"Passed UCI tests but only {tournament_win_rate:.1f}% tournament win rate - investigate gameplay issues"
                    })
        
        return correlations
    
    def generate_enhanced_appendix(self, output_path: str):
        """Generate enhanced appendix with automated anomaly detection"""
        
        # Run all detection methods
        regressions = self.detect_version_regressions()
        mismatches = self.detect_feature_mismatches()
        quality_issues = self.detect_data_quality_issues()
        uci_correlations = self.cross_reference_uci_failures()
        
        # Enhance existing appendix with automated findings
        enhanced_appendix = self.appendix.copy()
        
        enhanced_appendix['automated_analysis'] = {
            'generated': '2025-08-08',
            'version_regressions': regressions,
            'feature_mismatches': mismatches, 
            'data_quality_issues': quality_issues,
            'uci_tournament_correlations': uci_correlations
        }
        
        # Add summary statistics
        enhanced_appendix['analysis_summary'] = {
            'total_regressions_found': len(regressions),
            'total_feature_mismatches': len(mismatches),
            'total_quality_issues': len(quality_issues),
            'total_uci_mismatches': len(uci_correlations),
            'high_severity_regressions': len([r for r in regressions if r.get('severity') == 'high']),
            'key_insights': [
                f"Found {len(regressions)} version regressions across engine families",
                f"Identified {len(mismatches)} engines with performance not matching claimed features",
                f"Detected {len(quality_issues)} data quality issues from broken opponents",
                f"Found {len(uci_correlations)} mismatches between UCI tests and tournament performance"
            ]
        }
        
        # Save enhanced appendix
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_appendix, f, indent=2)
        
        print(f"Enhanced appendix saved to {output_path}")
        print(f"Summary: {len(regressions)} regressions, {len(mismatches)} feature mismatches, {len(quality_issues)} quality issues")


def main():
    detector = AnomalyDetector(
        'results/tournament_analysis.json',
        'results/engine_test_report.json', 
        'results/results_appendix.json'
    )
    
    detector.generate_enhanced_appendix('results/results_appendix_enhanced.json')


if __name__ == '__main__':
    main()
