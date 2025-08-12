#!/usr/bin/env python3
"""
Focused Engine Analyzer for Chess Engine Analytics

Generates detailed reports for specific engines, families, or versions.
Supports multiple targeting modes:
- Family analysis: "Cece" (all Cece variants)
- Version analysis: "Cece 1.0" (all engines matching consolidated name)
- Exact match: "Cece_v1.3" (exact filename match)
- Flexible matching: "SlowMate 0.1" (version-specific analysis)
"""

import json
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any, Optional
import os
import sys
import argparse
from datetime import datetime

class FocusedEngineAnalyzer:
    def __init__(self, results_dir='results'):
        self.results_dir = results_dir
        self.behavioral_data = self.load_behavioral_data()
        self.unified_data = self.load_unified_data()
        self.name_mapping = self.load_name_mapping()
        
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
    
    def load_name_mapping(self) -> Dict:
        """Load name consolidation mapping"""
        try:
            with open('engine_name_mapping.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: No engine name mapping found")
            return {}
    
    def find_matching_engines(self, target: str) -> Dict[str, Dict]:
        """
        Find engines matching the target specification
        
        Args:
            target: Engine specification (family, version, or exact match)
            
        Returns:
            Dictionary of matching engines with their data
        """
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            return {}
        
        profiles = self.behavioral_data['behavioral_profiles']
        matches = {}
        
        target_lower = target.lower().strip()
        
        print(f"Searching for engines matching: '{target}'")
        print(f"Total engines available: {len(profiles)}")
        
        # Strategy 1: Exact match (case-insensitive)
        exact_match_found = False
        for engine_name, profile in profiles.items():
            if engine_name.lower() == target_lower:
                matches[engine_name] = profile
                exact_match_found = True
                print(f"  + Exact match: {engine_name}")
        
        # Strategy 2: Exact filename match (for .exe specifications)
        if not exact_match_found:
            exe_target = target if target.endswith('.exe') else f"{target}.exe"
            for engine_name, profile in profiles.items():
                if engine_name.lower() == exe_target.lower():
                    matches[engine_name] = profile
                    print(f"  + Exact filename match: {engine_name}")
        
        # Strategy 3: Family name matching (partial) - Continue even if exact match found
        # This allows "Cecilia" to match both "Cecilia" and "Cecilia v0.1", etc.
        for engine_name, profile in profiles.items():
            engine_lower = engine_name.lower()
            # Check if target is a family name contained in engine name
            if target_lower in engine_lower and engine_name not in matches:
                matches[engine_name] = profile
                print(f"  + Family match: {engine_name}")
        
        # Strategy 4: Family/version matching via name mapping
        if self.name_mapping:
            engine_families = self.name_mapping.get('engine_families', {})
            
            # Check if target matches a family name
            for family_name, family_data in engine_families.items():
                if target_lower == family_name.lower():
                    # Target is a family name, get all variants of all versions
                    canonical_name = family_data.get('canonical_name', family_name)
                    for engine_name, profile in profiles.items():
                        if canonical_name.lower() in engine_name.lower() and engine_name not in matches:
                            matches[engine_name] = profile
                            print(f"  + Family match: {engine_name}")
                    break
                
                # Check version-specific matches
                versions = family_data.get('versions', {})
                for version_key, version_data in versions.items():
                    canonical = version_data.get('canonical', '')
                    variants = version_data.get('variants', [])
                    
                    # Check if target matches canonical name or any variant
                    if (target_lower == canonical.lower() or 
                        target_lower in [v.lower() for v in variants]):
                        
                        # Find engines matching this version
                        for engine_name, profile in profiles.items():
                            if ((canonical.lower() in engine_name.lower() or
                                any(v.lower() in engine_name.lower() for v in variants)) and
                                engine_name not in matches):
                                matches[engine_name] = profile
                                print(f"  + Version match: {engine_name} -> {canonical}")
                        break
                
                if matches:
                    break
        
        # Strategy 5: Fuzzy version matching (e.g., "Cece 1.0" matches "Cece_v1.0.exe")
        if not matches:
            # Parse target for family and version
            parts = target_lower.split()
            if len(parts) >= 2:
                family = parts[0]
                version = parts[1]
                
                for engine_name, profile in profiles.items():
                    engine_lower = engine_name.lower()
                    if family in engine_lower and version in engine_lower:
                        matches[engine_name] = profile
                        print(f"  + Version match: {engine_name}")
        
        if not matches:
            print(f"  X No matches found for '{target}'")
            print("  Available engines for reference:")
            for i, engine in enumerate(list(profiles.keys())[:10]):
                print(f"    {engine}")
            if len(profiles) > 10:
                print(f"    ... and {len(profiles) - 10} more")
        
        return matches
    
    def analyze_engine_performance(self, engine_name: str, profile: Dict) -> Dict[str, Any]:
        """Detailed performance analysis for a single engine"""
        if not profile:
            return {"error": "Empty profile"}
        
        behavioral_scores = profile.get('behavioral_scores', {})
        performance_metrics = profile.get('performance_metrics', {})
        signature_patterns = profile.get('signature_patterns', {})
        playing_style = profile.get('playing_style', {})
        
        analysis = {
            "engine_name": engine_name,
            "total_games": profile.get('total_games', 0),
            "behavioral_profile": {
                "aggression": behavioral_scores.get('aggression', 0),
                "decisiveness": behavioral_scores.get('decisiveness', 0),
                "piece_diversity": behavioral_scores.get('piece_diversity', 0),
                "opening_diversity": behavioral_scores.get('opening_diversity', 0)
            },
            "performance_metrics": {
                "win_rate": performance_metrics.get('win_rate', 0),
                "draw_rate": performance_metrics.get('draw_rate', 0),
                "loss_rate": performance_metrics.get('loss_rate', 0),
                "avg_game_length": performance_metrics.get('avg_game_length', 0),
                "capture_rate": performance_metrics.get('capture_rate', 0),
                "check_rate": performance_metrics.get('check_rate', 0),
                "castle_rate": performance_metrics.get('castle_rate', 0),
                "promotion_rate": performance_metrics.get('promotion_rate', 0)
            },
            "playing_style": {
                "primary_style": playing_style.get('primary_style', 'unknown'),
                "style_confidence": playing_style.get('style_confidence', 0),
                "secondary_traits": playing_style.get('secondary_traits', [])
            },
            "signature_patterns": {
                "favorite_pieces": signature_patterns.get('favorite_pieces', {}),
                "preferred_squares": signature_patterns.get('preferred_squares', {}),
                "opening_preferences": signature_patterns.get('opening_preferences', {}),
                "tactical_patterns": signature_patterns.get('tactical_patterns', {})
            }
        }
        
        # Add strength assessment
        unified_engines = self.unified_data.get('engine_ratings', {})
        if engine_name in unified_engines:
            engine_data = unified_engines[engine_name]
            analysis["tournament_performance"] = {
                "elo_rating": engine_data.get('elo_rating', 0),
                "games_played": engine_data.get('games_played', 0),
                "opponents_faced": engine_data.get('opponents_faced', 0),
                "score": engine_data.get('score', 0),
                "performance_rating": engine_data.get('performance_rating', 0)
            }
        
        return analysis
    
    def generate_comparison_analysis(self, matches: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate comparative analysis when multiple engines match"""
        if len(matches) <= 1:
            return {}
        
        comparison = {
            "engine_count": len(matches),
            "engines_analyzed": list(matches.keys()),
            "metrics_comparison": {},
            "progression_analysis": {},
            "strengths_weaknesses": {}
        }
        
        # Extract metrics for comparison
        metrics_data = []
        for engine_name, profile in matches.items():
            behavioral_scores = profile.get('behavioral_scores', {})
            performance_metrics = profile.get('performance_metrics', {})
            
            metrics_data.append({
                'engine': engine_name,
                'aggression': behavioral_scores.get('aggression', 0),
                'decisiveness': behavioral_scores.get('decisiveness', 0),
                'piece_diversity': behavioral_scores.get('piece_diversity', 0),
                'win_rate': performance_metrics.get('win_rate', 0),
                'avg_game_length': performance_metrics.get('avg_game_length', 0),
                'capture_rate': performance_metrics.get('capture_rate', 0),
                'total_games': profile.get('total_games', 0)
            })
        
        if metrics_data:
            df = pd.DataFrame(metrics_data)
            
            # Calculate statistics
            for metric in ['aggression', 'decisiveness', 'piece_diversity', 'win_rate', 'capture_rate']:
                if metric in df.columns:
                    comparison["metrics_comparison"][metric] = {
                        "min": float(df[metric].min()),
                        "max": float(df[metric].max()),
                        "mean": float(df[metric].mean()),
                        "std": float(df[metric].std()),
                        "range": float(df[metric].max() - df[metric].min())
                    }
            
            # Identify best and worst performers
            best_win_rate = df.loc[df['win_rate'].idxmax()]
            worst_win_rate = df.loc[df['win_rate'].idxmin()]
            
            comparison["strengths_weaknesses"] = {
                "highest_win_rate": {
                    "engine": str(best_win_rate['engine']),
                    "win_rate": float(str(best_win_rate['win_rate']))
                },
                "lowest_win_rate": {
                    "engine": str(worst_win_rate['engine']),
                    "win_rate": float(str(worst_win_rate['win_rate']))
                }
            }
        
        return comparison
    
    def generate_focused_report(self, target: str) -> str:
        """Generate a comprehensive focused report"""
        print(f"\n{'='*60}")
        print(f"FOCUSED ENGINE ANALYSIS: {target}")
        print(f"{'='*60}")
        
        # Find matching engines
        matches = self.find_matching_engines(target)
        
        if not matches:
            return self._generate_no_matches_report(target)
        
        # Generate report sections
        report_sections = []
        report_sections.append(f"# Focused Engine Analysis: {target}")
        report_sections.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append("")
        
        # Summary section
        report_sections.append("## Analysis Summary")
        report_sections.append(f"- Target specification: `{target}`")
        report_sections.append(f"- Engines found: {len(matches)}")
        report_sections.append(f"- Engine names: {', '.join(matches.keys())}")
        report_sections.append("")
        
        # Individual engine analyses
        for engine_name, profile in matches.items():
            analysis = self.analyze_engine_performance(engine_name, profile)
            report_sections.extend(self._format_engine_analysis(analysis))
        
        # Comparison analysis (if multiple engines)
        if len(matches) > 1:
            comparison = self.generate_comparison_analysis(matches)
            if comparison:
                report_sections.extend(self._format_comparison_analysis(comparison))
        
        # Recommendations section
        report_sections.append("## Development Recommendations")
        if len(matches) == 1:
            engine_name = list(matches.keys())[0]
            analysis = self.analyze_engine_performance(engine_name, matches[engine_name])
            report_sections.extend(self._generate_recommendations(analysis))
        else:
            report_sections.extend(self._generate_family_recommendations(matches))
        
        return '\n'.join(report_sections)
    
    def _format_engine_analysis(self, analysis: Dict[str, Any]) -> List[str]:
        """Format individual engine analysis for report"""
        if "error" in analysis:
            return [f"## {analysis.get('engine_name', 'Unknown')} - Analysis Error", 
                   f"Error: {analysis['error']}", ""]
        
        sections = []
        engine_name = analysis['engine_name']
        
        sections.append(f"## {engine_name} - Detailed Analysis")
        sections.append("")
        
        # Basic info
        sections.append("### Basic Information")
        sections.append(f"- Total games played: {analysis['total_games']}")
        
        if 'tournament_performance' in analysis:
            tp = analysis['tournament_performance']
            sections.append(f"- ELO rating: {tp['elo_rating']:.0f}")
            sections.append(f"- Tournament games: {tp['games_played']}")
            sections.append(f"- Opponents faced: {tp['opponents_faced']}")
            sections.append(f"- Performance rating: {tp['performance_rating']:.0f}")
        
        sections.append("")
        
        # Behavioral profile
        sections.append("### Behavioral Profile")
        bp = analysis['behavioral_profile']
        sections.append(f"- Aggression: {bp['aggression']:.1f}/100")
        sections.append(f"- Decisiveness: {bp['decisiveness']:.1f}/100")
        sections.append(f"- Piece diversity: {bp['piece_diversity']:.1f}/100")
        sections.append(f"- Opening diversity: {bp['opening_diversity']:.1f}/100")
        sections.append("")
        
        # Performance metrics
        sections.append("### Performance Metrics")
        pm = analysis['performance_metrics']
        sections.append(f"- Win rate: {pm['win_rate']:.1f}%")
        sections.append(f"- Draw rate: {pm['draw_rate']:.1f}%")
        sections.append(f"- Loss rate: {pm['loss_rate']:.1f}%")
        sections.append(f"- Average game length: {pm['avg_game_length']:.1f} moves")
        sections.append(f"- Capture rate: {pm['capture_rate']:.2f} captures/move")
        sections.append(f"- Check rate: {pm['check_rate']:.2f} checks/move")
        sections.append(f"- Castling rate: {pm['castle_rate']:.1f}%")
        sections.append(f"- Promotion rate: {pm['promotion_rate']:.2f}%")
        sections.append("")
        
        # Playing style
        sections.append("### Playing Style")
        ps = analysis['playing_style']
        sections.append(f"- Primary style: {ps['primary_style']}")
        sections.append(f"- Style confidence: {ps['style_confidence']:.1f}%")
        if ps['secondary_traits']:
            sections.append(f"- Secondary traits: {', '.join(ps['secondary_traits'])}")
        sections.append("")
        
        # Signature patterns
        sections.append("### Signature Patterns")
        sp = analysis['signature_patterns']
        
        if sp['favorite_pieces']:
            sections.append("#### Favorite Pieces")
            for piece, usage in list(sp['favorite_pieces'].items())[:3]:
                sections.append(f"- {piece}: {usage:.1f}% usage")
        
        if sp['opening_preferences']:
            sections.append("#### Opening Preferences")
            for opening, frequency in list(sp['opening_preferences'].items())[:3]:
                sections.append(f"- {opening}: {frequency:.1f}% frequency")
        
        sections.append("")
        
        return sections
    
    def _format_comparison_analysis(self, comparison: Dict[str, Any]) -> List[str]:
        """Format comparison analysis for report"""
        sections = []
        sections.append("## Family/Version Comparison")
        sections.append("")
        
        sections.append(f"### Overview")
        sections.append(f"- Engines compared: {comparison['engine_count']}")
        sections.append(f"- Engines: {', '.join(comparison['engines_analyzed'])}")
        sections.append("")
        
        # Metrics comparison
        if 'metrics_comparison' in comparison:
            sections.append("### Metrics Comparison")
            for metric, stats in comparison['metrics_comparison'].items():
                sections.append(f"#### {metric.replace('_', ' ').title()}")
                sections.append(f"- Range: {stats['min']:.1f} - {stats['max']:.1f}")
                sections.append(f"- Average: {stats['mean']:.1f}")
                sections.append(f"- Variation: ±{stats['std']:.1f}")
                sections.append("")
        
        # Strengths and weaknesses
        if 'strengths_weaknesses' in comparison:
            sw = comparison['strengths_weaknesses']
            sections.append("### Performance Highlights")
            sections.append(f"- Best performer: {sw['highest_win_rate']['engine']} ({sw['highest_win_rate']['win_rate']:.1f}% win rate)")
            sections.append(f"- Needs improvement: {sw['lowest_win_rate']['engine']} ({sw['lowest_win_rate']['win_rate']:.1f}% win rate)")
            sections.append("")
        
        return sections
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a single engine"""
        recommendations = []
        
        bp = analysis['behavioral_profile']
        pm = analysis['performance_metrics']
        
        # Performance-based recommendations
        if pm['win_rate'] < 30:
            recommendations.append("- **Low win rate**: Consider improving evaluation function or search depth")
        
        if pm['avg_game_length'] > 80:
            recommendations.append("- **Long games**: Engine may be too cautious; increase aggression parameters")
        
        if bp['aggression'] < 20:
            recommendations.append("- **Low aggression**: Consider more aggressive piece values or tactical bonuses")
        
        if bp['decisiveness'] < 30:
            recommendations.append("- **Low decisiveness**: Improve endgame evaluation to convert advantages")
        
        if pm['capture_rate'] < 0.05:
            recommendations.append("- **Low capture rate**: Review tactical evaluation and piece exchanges")
        
        # Style-based recommendations
        ps = analysis['playing_style']
        if ps['primary_style'] == 'defensive' and pm['win_rate'] < 40:
            recommendations.append("- **Defensive style with low wins**: Balance with more active play")
        
        if not recommendations:
            recommendations.append("- **Strong performance**: Focus on fine-tuning and consistency")
        
        return recommendations
    
    def _generate_family_recommendations(self, matches: Dict[str, Dict]) -> List[str]:
        """Generate recommendations for engine family/versions"""
        recommendations = []
        
        # Analyze progression if versions are detected
        versions = []
        for engine_name in matches.keys():
            # Try to extract version numbers
            import re
            version_match = re.search(r'v?(\d+\.\d+)', engine_name)
            if version_match:
                versions.append((engine_name, float(version_match.group(1))))
        
        if len(versions) > 1:
            versions.sort(key=lambda x: x[1])  # Sort by version number
            recommendations.append("### Version Progression Analysis")
            
            latest_engine = versions[-1][0]
            earliest_engine = versions[0][0]
            
            latest_profile = matches[latest_engine]
            earliest_profile = matches[earliest_engine]
            
            latest_win_rate = latest_profile.get('performance_metrics', {}).get('win_rate', 0)
            earliest_win_rate = earliest_profile.get('performance_metrics', {}).get('win_rate', 0)
            
            if latest_win_rate > earliest_win_rate:
                recommendations.append(f"- **Positive progression**: {latest_engine} shows {latest_win_rate - earliest_win_rate:.1f}% improvement over {earliest_engine}")
            else:
                recommendations.append(f"- **Regression detected**: {latest_engine} performing {earliest_win_rate - latest_win_rate:.1f}% worse than {earliest_engine}")
        
        recommendations.append("- **Family development**: Compare strongest variant features for integration")
        recommendations.append("- **Consistency**: Focus on reducing performance variance between versions")
        
        return recommendations
    
    def _generate_no_matches_report(self, target: str) -> str:
        """Generate report when no matches found"""
        available_engines = list(self.behavioral_data.get('behavioral_profiles', {}).keys())
        
        report = []
        report.append(f"# Focused Engine Analysis: {target}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("## No Matches Found")
        report.append(f"No engines found matching specification: `{target}`")
        report.append("")
        report.append("### Available Engines")
        for engine in available_engines[:20]:
            report.append(f"- {engine}")
        if len(available_engines) > 20:
            report.append(f"- ... and {len(available_engines) - 20} more")
        report.append("")
        report.append("### Search Tips")
        report.append("- Use exact engine names for precise matching")
        report.append("- Use family names (e.g., 'Cece') for all variants")
        report.append("- Use version patterns (e.g., 'Cece 1.0') for version-specific analysis")
        report.append("- Use exact filenames (e.g., 'Cece_v1.3.exe') for strict matching")
        
        return '\n'.join(report)

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Focused Engine Analyzer')
    parser.add_argument('target', help='Engine specification (family, version, or exact name)')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--format', choices=['markdown', 'txt'], default='markdown', 
                       help='Output format (default: markdown)')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = FocusedEngineAnalyzer()
    
    # Generate report
    report = analyzer.generate_focused_report(args.target)
    
    # Save or print report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nFocused analysis report saved to: {args.output}")
    else:
        # Auto-generate filename
        safe_target = "".join(c for c in args.target if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_target = safe_target.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results/focused_analysis_{safe_target}_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nFocused analysis report saved to: {filename}")
    
    # Also print summary to console
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode if no arguments
        print("Focused Engine Analyzer")
        print("Enter engine specification (family, version, or exact name):")
        target = input("> ").strip()
        if target:
            analyzer = FocusedEngineAnalyzer()
            report = analyzer.generate_focused_report(target)
            
            # Save report
            safe_target = "".join(c for c in target if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_target = safe_target.replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"results/focused_analysis_{safe_target}_{timestamp}.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {filename}")
    else:
        main()
