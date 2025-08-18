#!/usr/bin/env python3
"""
Comprehensive Engine Analysis Report Generator

Generates a complete markdown report combining:
- Tournament performance analysis
- Behavioral pattern analysis  
- Engine relationship analysis
- Development recommendations
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import numpy as np

class ComprehensiveAnalysisReporter:
    def __init__(self, results_dir='results'):
        self.results_dir = results_dir
        self.unified_data = self.load_unified_data()
        self.behavioral_data = self.load_behavioral_data()
        
    def load_unified_data(self) -> Dict:
        """Load unified tournament analysis"""
        try:
            with open(os.path.join(self.results_dir, 'unified_tournament_analysis.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Unified tournament data not found")
            return {}
    
    def load_behavioral_data(self) -> Dict:
        """Load behavioral analysis data"""
        try:
            with open(os.path.join(self.results_dir, 'behavioral_analysis.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Behavioral analysis data not found")
            return {}
    
    def generate_comprehensive_report(self) -> str:
        """Generate the complete analysis report"""
        report_lines = []
        
        # Header
        report_lines.extend(self.generate_header())
        
        # Executive Summary
        report_lines.extend(self.generate_executive_summary())
        
        # Performance Analysis
        report_lines.extend(self.generate_performance_analysis())
        
        # Behavioral Analysis
        report_lines.extend(self.generate_behavioral_analysis())
        
        # Engine Family Analysis
        report_lines.extend(self.generate_family_analysis())
        
        # Recommendations
        report_lines.extend(self.generate_recommendations())
        
        # Appendix
        report_lines.extend(self.generate_appendix())
        
        return '\n'.join(report_lines)
    
    def generate_header(self) -> List[str]:
        """Generate report header"""
        analysis_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return [
            "# 🏆 Comprehensive Chess Engine Analysis Report",
            "",
            f"**Generated:** {analysis_date}",
            f"**Analysis Period:** Tournament data from multiple sessions",
            "",
            "## 📋 Report Overview",
            "",
            "This comprehensive report analyzes chess engine performance across multiple dimensions:",
            "- **Performance Analysis**: ELO ratings, win rates, tournament results",
            "- **Behavioral Analysis**: Playing styles, move patterns, tactical preferences", 
            "- **Family Evolution**: Development progression within engine families",
            "- **Strategic Recommendations**: Targeted improvement suggestions",
            "",
            "---",
            ""
        ]
    
    def generate_executive_summary(self) -> List[str]:
        """Generate executive summary"""
        lines = [
            "## 🎯 Executive Summary",
            ""
        ]
        
        if self.unified_data and 'unified_rankings' in self.unified_data:
            rankings = self.unified_data['unified_rankings']
            top_engine = rankings[0] if rankings else None
            
            if top_engine:
                lines.extend([
                    f"### 🥇 Top Performer: {top_engine['name']}",
                    f"- **Rating:** {top_engine['estimated_rating']:.0f} ELO",
                    f"- **Games:** {top_engine['games']} played",
                    f"- **Win Rate:** {top_engine['win_rate']:.1f}%",
                    ""
                ])
        
        if self.behavioral_data and 'behavioral_profiles' in self.behavioral_data:
            profiles = self.behavioral_data['behavioral_profiles']
            categories = self.behavioral_data.get('engine_categories', {})
            
            lines.extend([
                f"### 🧠 Behavioral Insights",
                f"- **Engines Analyzed:** {len(profiles)}",
                f"- **Playing Styles Identified:** {len(categories)}",
                ""
            ])
            
            # Find most aggressive and defensive engines
            if profiles:
                most_aggressive = max(profiles.items(), 
                                    key=lambda x: x[1].get('behavioral_scores', {}).get('aggression', 0))
                
                most_defensive = min(profiles.items(),
                                   key=lambda x: x[1].get('behavioral_scores', {}).get('aggression', 100))
                
                if most_aggressive and most_aggressive[1]:
                    aggression_score = most_aggressive[1].get('behavioral_scores', {}).get('aggression', 0)
                    lines.append(f"- **Most Aggressive:** {most_aggressive[0]} (Score: {aggression_score:.1f})")
                
                if most_defensive and most_defensive[1]:
                    defensive_score = most_defensive[1].get('behavioral_scores', {}).get('aggression', 0)
                    lines.append(f"- **Most Defensive:** {most_defensive[0]} (Score: {defensive_score:.1f})")
            
            lines.append("")
        
        return lines
    
    def generate_performance_analysis(self) -> List[str]:
        """Generate performance analysis section"""
        lines = [
            "## 📊 Performance Analysis",
            ""
        ]
        
        if not self.unified_data or 'unified_rankings' not in self.unified_data:
            lines.extend([
                "⚠️ No unified ranking data available.",
                ""
            ])
            return lines
        
        rankings = self.unified_data['unified_rankings']
        
        # Top performers table
        lines.extend([
            "### 🏅 Top 10 Performers",
            "",
            "| Rank | Engine | ELO | Games | Win Rate | Tournaments |",
            "|------|--------|-----|-------|----------|-------------|"
        ])
        
        for i, engine in enumerate(rankings[:10], 1):
            lines.append(
                f"| {i} | {engine['name']} | {engine['estimated_rating']:.0f} | "
                f"{engine['games']} | {engine['win_rate']:.1f}% | {engine['tournaments']} |"
            )
        
        lines.extend(["", "### 📈 Performance Metrics Summary", ""])
        
        # Calculate statistics
        total_games = sum(e['games'] for e in rankings)
        avg_rating = np.mean([e['estimated_rating'] for e in rankings])
        avg_win_rate = np.mean([e['win_rate'] for e in rankings])
        
        lines.extend([
            f"- **Total Games Analyzed:** {total_games:,}",
            f"- **Average Engine Rating:** {avg_rating:.0f} ELO",
            f"- **Average Win Rate:** {avg_win_rate:.1f}%",
            f"- **Total Engines:** {len(rankings)}",
            ""
        ])
        
        return lines
    
    def generate_behavioral_analysis(self) -> List[str]:
        """Generate behavioral analysis section"""
        lines = [
            "## 🧠 Behavioral Analysis",
            ""
        ]
        
        if not self.behavioral_data or 'behavioral_profiles' not in self.behavioral_data:
            lines.extend([
                "⚠️ No behavioral analysis data available.",
                "Run `analysis/behavioral_analyzer.py` to generate behavioral insights.",
                ""
            ])
            return lines
        
        profiles = self.behavioral_data['behavioral_profiles']
        categories = self.behavioral_data.get('engine_categories', {})
        
        # Style categories
        lines.extend([
            "### 🎭 Playing Style Categories",
            ""
        ])
        
        for category, engines in categories.items():
            if engines:
                lines.extend([
                    f"#### {category.replace('_', ' ').title()} ({len(engines)} engines)",
                    ""
                ])
                
                for engine in engines[:5]:  # Show top 5 in each category
                    if engine in profiles:
                        profile = profiles[engine]
                        aggression = profile.get('behavioral_scores', {}).get('aggression', 0)
                        win_rate = profile.get('performance_metrics', {}).get('win_rate', 0)
                        lines.append(f"- **{engine}**: Aggression {aggression:.1f}, Win Rate {win_rate:.1f}%")
                
                if len(engines) > 5:
                    lines.append(f"- ... and {len(engines) - 5} more")
                
                lines.append("")
        
        # Signature patterns
        lines.extend([
            "### 🔄 Notable Engine Signatures",
            ""
        ])
        
        for engine, profile in list(profiles.items())[:5]:  # Top 5 engines
            patterns = profile.get('signature_patterns', {})
            favorite_pieces = patterns.get('favorite_pieces', {})
            
            if favorite_pieces:
                top_piece = max(favorite_pieces.items(), key=lambda x: x[1])
                piece_names = {'K': 'King', 'Q': 'Queen', 'R': 'Rook', 
                              'B': 'Bishop', 'N': 'Knight', 'P': 'Pawn'}
                piece_name = piece_names.get(top_piece[0], top_piece[0])
                
                lines.append(f"- **{engine}**: Prefers {piece_name} moves ({top_piece[1]} times)")
        
        lines.append("")
        
        return lines
    
    def generate_family_analysis(self) -> List[str]:
        """Generate engine family analysis"""
        lines = [
            "## 👨‍👩‍👧‍👦 Engine Family Analysis",
            ""
        ]
        
        if not self.unified_data or 'consolidation_summary' not in self.unified_data:
            lines.extend([
                "⚠️ No consolidation data available.",
                ""
            ])
            return lines
        
        consolidation = self.unified_data['consolidation_summary']
        families = consolidation.get('consolidated_groups', {})
        
        lines.extend([
            f"### 📈 Development Trajectories ({len(families)} families)",
            ""
        ])
        
        # Analyze each family's progression
        rankings = {r['name']: r for r in self.unified_data.get('unified_rankings', [])}
        
        for family_name, variants in families.items():
            if len(variants) > 1:  # Only analyze families with multiple versions
                family_ratings = []
                
                for variant in variants:
                    for rank_name, rank_data in rankings.items():
                        if any(v.lower() in rank_name.lower() for v in variants):
                            family_ratings.append((rank_name, rank_data['estimated_rating']))
                            break
                
                if family_ratings:
                    family_ratings.sort(key=lambda x: x[1], reverse=True)
                    best_version = family_ratings[0]
                    
                    lines.extend([
                        f"#### {family_name}",
                        f"- **Variants:** {len(variants)} versions",
                        f"- **Best Version:** {best_version[0]} ({best_version[1]:.0f} ELO)",
                        f"- **Development Status:** {'Improving' if len(family_ratings) > 1 else 'Single version'}",
                        ""
                    ])
        
        return lines
    
    def generate_recommendations(self) -> List[str]:
        """Generate strategic recommendations"""
        lines = [
            "## 🎯 Strategic Recommendations",
            ""
        ]
        
        recommendations = []
        
        # Performance-based recommendations
        if self.unified_data and 'unified_rankings' in self.unified_data:
            rankings = self.unified_data['unified_rankings']
            
            # Find underperforming engines with potential
            for engine_data in rankings:
                if (engine_data['games'] >= 50 and 
                    engine_data['estimated_rating'] < 1200 and 
                    engine_data['win_rate'] > 30):
                    
                    recommendations.append({
                        'type': 'performance',
                        'engine': engine_data['name'],
                        'issue': 'Low rating despite decent win rate',
                        'suggestion': 'Focus on opponent strength and strategic depth'
                    })
        
        # Behavioral-based recommendations  
        if self.behavioral_data and 'behavioral_profiles' in self.behavioral_data:
            profiles = self.behavioral_data['behavioral_profiles']
            
            for engine, profile in profiles.items():
                scores = profile.get('behavioral_scores', {})
                perf = profile.get('performance_metrics', {})
                
                # Low diversity engines
                if scores.get('piece_diversity', 0) < 4:
                    recommendations.append({
                        'type': 'behavioral',
                        'engine': engine,
                        'issue': 'Low piece diversity',
                        'suggestion': 'Expand piece movement patterns and tactical awareness'
                    })
                
                # High aggression, low performance
                if (scores.get('aggression', 0) > 15 and 
                    perf.get('win_rate', 0) < 40):
                    recommendations.append({
                        'type': 'behavioral',
                        'engine': engine,
                        'issue': 'Aggressive but ineffective',
                        'suggestion': 'Balance aggression with positional understanding'
                    })
        
        # Generate recommendation sections
        if recommendations:
            perf_recs = [r for r in recommendations if r['type'] == 'performance']
            behav_recs = [r for r in recommendations if r['type'] == 'behavioral']
            
            if perf_recs:
                lines.extend([
                    "### 📈 Performance Improvements",
                    ""
                ])
                for rec in perf_recs[:5]:
                    lines.extend([
                        f"#### {rec['engine']}",
                        f"**Issue:** {rec['issue']}",
                        f"**Recommendation:** {rec['suggestion']}",
                        ""
                    ])
            
            if behav_recs:
                lines.extend([
                    "### 🧠 Behavioral Enhancements",
                    ""
                ])
                for rec in behav_recs[:5]:
                    lines.extend([
                        f"#### {rec['engine']}",
                        f"**Issue:** {rec['issue']}",
                        f"**Recommendation:** {rec['suggestion']}",
                        ""
                    ])
        else:
            lines.extend([
                "No specific recommendations identified at this time.",
                "All engines appear to be performing within expected parameters.",
                ""
            ])
        
        return lines
    
    def generate_appendix(self) -> List[str]:
        """Generate appendix with technical details"""
        lines = [
            "## 📎 Appendix",
            "",
            "### Data Sources",
            ""
        ]
        
        if self.unified_data:
            analysis_date = self.unified_data.get('analysis_date', 'Unknown')
            lines.extend([
                f"- **Unified Tournament Analysis:** {analysis_date}",
                f"- **Total Tournaments:** {self.unified_data.get('summary', {}).get('total_tournaments', 'Unknown')}",
                f"- **Total Games:** {self.unified_data.get('summary', {}).get('total_games', 'Unknown')}"
            ])
        
        if self.behavioral_data:
            metadata = self.behavioral_data.get('analysis_metadata', {})
            lines.extend([
                f"- **Behavioral Analysis:** {metadata.get('analysis_date', 'Unknown')}",
                f"- **Engines Analyzed:** {metadata.get('engines_analyzed', 'Unknown')}",
                f"- **Total Games (Behavioral):** {metadata.get('total_games', 'Unknown')}"
            ])
        
        lines.extend([
            "",
            "### Methodology",
            "",
            "- **ELO Calculation:** Based on game results with opponent strength adjustment",
            "- **Behavioral Analysis:** Pattern recognition across move sequences and outcomes",
            "- **Style Classification:** Multi-factor analysis including aggression, piece usage, and game length",
            "",
            "---",
            "",
            f"*Report generated by Chess Engine Analysis System v2.0*"
        ])
        
        return lines

def main():
    """Generate and save comprehensive analysis report"""
    reporter = ComprehensiveAnalysisReporter()
    
    print("📊 Generating comprehensive analysis report...")
    report_content = reporter.generate_comprehensive_report()
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"results/comprehensive_analysis_report_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Comprehensive analysis report saved to: {report_path}")
    print(f"📄 Report contains {len(report_content.split())} words")

if __name__ == "__main__":
    main()
