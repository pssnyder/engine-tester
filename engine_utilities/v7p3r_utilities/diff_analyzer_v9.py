#!/usr/bin/env python3
"""
V7P3R v9.0 vs v9.1 Diff Analysis Tool
Identifies specific code changes that may have caused tactical regressions
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

class V7P3RDiffAnalyzer:
    """Analyze differences between v9.0 and v9.1 to find regression causes"""
    
    def __init__(self, v7p3r_engine_path: str):
        self.engine_path = Path(v7p3r_engine_path)
        self.build_path = self.engine_path / "build"
        
    def find_version_files(self) -> Dict[str, Any]:
        """Find v9.0 and v9.1 related files"""
        
        files = {
            'v9.0_exe': None,
            'v9.1_exe': None,
            'v9.0_source': None,
            'v9.1_source': None,
            'confidence_system': None
        }
        
        # Look for executables
        for exe_file in self.engine_path.glob("V7P3R_v*.exe"):
            if "v9.0" in exe_file.name:
                files['v9.0_exe'] = exe_file
            elif "v9.1" in exe_file.name:
                files['v9.1_exe'] = exe_file
        
        # Look for source files
        src_path = self.engine_path / "src"
        if src_path.exists():
            for src_file in src_path.glob("*.py"):
                if "confidence" in src_file.name.lower():
                    files['confidence_system'] = src_file
        
        # Look for build/spec files
        for build_file in self.build_path.glob("*v9*"):
            if "v9.0" in build_file.name:
                files['v9.0_source'] = build_file
            elif "v9.1" in build_file.name:
                files['v9.1_source'] = build_file
        
        return files
    
    def analyze_confidence_system_changes(self) -> List[str]:
        """Identify confidence system related changes"""
        
        confidence_indicators = [
            "confidence",
            "risk",
            "safety",
            "conservative",
            "aggressive", 
            "threshold",
            "evaluation",
            "depth",
            "pruning",
            "time_management"
        ]
        
        changes = []
        
        # Check for confidence-related files
        src_path = self.engine_path / "src"
        if src_path.exists():
            for py_file in src_path.glob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                    for indicator in confidence_indicators:
                        if indicator in content:
                            changes.append(f"Found '{indicator}' in {py_file.name}")
                except:
                    continue
        
        return changes
    
    def find_recent_git_changes(self) -> List[str]:
        """Find recent git changes that might relate to v9.1"""
        
        changes = []
        
        try:
            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=self.engine_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                for commit in commits:
                    if any(keyword in commit.lower() for keyword in 
                          ['confidence', 'v9.1', 'tactical', 'evaluation', 'risk']):
                        changes.append(f"Recent commit: {commit}")
        except:
            changes.append("Git analysis not available")
        
        return changes
    
    def analyze_file_timestamps(self) -> Dict[str, Any]:
        """Analyze when files were last modified to identify v9.1 changes"""
        
        file_analysis = {
            'recent_modifications': [],
            'engine_files': [],
            'config_files': []
        }
        
        # Check main engine files
        for py_file in self.engine_path.glob("*.py"):
            try:
                mtime = py_file.stat().st_mtime
                file_analysis['engine_files'].append({
                    'file': py_file.name,
                    'modified': mtime
                })
            except:
                continue
        
        # Check config files
        for config_file in self.engine_path.glob("*config*.json"):
            try:
                mtime = config_file.stat().st_mtime
                file_analysis['config_files'].append({
                    'file': config_file.name,
                    'modified': mtime
                })
            except:
                continue
        
        return file_analysis
    
    def generate_diff_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive diff analysis report"""
        
        print("=" * 80)
        print("V7P3R v9.0 vs v9.1 DIFF ANALYSIS")
        print("=" * 80)
        
        # Find version files
        files = self.find_version_files()
        
        # Analyze confidence system changes
        confidence_changes = self.analyze_confidence_system_changes()
        
        # Find git changes
        git_changes = self.find_recent_git_changes()
        
        # Analyze file timestamps
        file_analysis = self.analyze_file_timestamps()
        
        report = {
            'version_files': files,
            'confidence_changes': confidence_changes,
            'git_changes': git_changes,
            'file_analysis': file_analysis,
            'recommendations': self.generate_recommendations(files, confidence_changes)
        }
        
        self.print_diff_summary(report)
        
        return report
    
    def generate_recommendations(self, files: Dict[str, Path], 
                               confidence_changes: List[str]) -> List[str]:
        """Generate specific recommendations for fixing regressions"""
        
        recommendations = []
        
        if files['confidence_system']:
            recommendations.append(
                f"Review confidence system in {files['confidence_system']}"
            )
        
        if confidence_changes:
            recommendations.append(
                "Analyze confidence-related code changes for tactical impact"
            )
        
        recommendations.extend([
            "Compare evaluation function differences between v9.0 and v9.1",
            "Check if search depth or pruning algorithms changed",
            "Validate time management changes didn't affect tactical calculation",
            "Test v9.0 with v9.1 time management (hybrid approach)",
            "Create regression test suite from the 4 identified tactical positions"
        ])
        
        return recommendations
    
    def print_diff_summary(self, report: Dict[str, Any]):
        """Print formatted diff analysis summary"""
        
        print(f"\n📁 VERSION FILES ANALYSIS:")
        for file_type, file_path in report['version_files'].items():
            if file_path:
                print(f"  {file_type}: {file_path}")
            else:
                print(f"  {file_type}: Not found")
        
        print(f"\n🔍 CONFIDENCE SYSTEM ANALYSIS:")
        if report['confidence_changes']:
            for change in report['confidence_changes']:
                print(f"  • {change}")
        else:
            print("  No obvious confidence system indicators found in source")
        
        print(f"\n📝 GIT CHANGES ANALYSIS:")
        if report['git_changes']:
            for change in report['git_changes']:
                print(f"  • {change}")
        else:
            print("  No relevant git changes identified")
        
        print(f"\n📊 FILE MODIFICATION ANALYSIS:")
        recent_files = sorted(report['file_analysis']['engine_files'], 
                            key=lambda x: x['modified'], reverse=True)[:5]
        print("  Most recently modified engine files:")
        for file_info in recent_files:
            print(f"    {file_info['file']}")
        
        print(f"\n🛠️ SPECIFIC RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n🎯 PRIORITY ACTIONS:")
        print("  1. Identify v9.1 confidence system implementation")
        print("  2. Compare tactical search patterns between v9.0 and v9.1")
        print("  3. Test hybrid approach: v9.0 tactics + v9.1 time management")
        print("  4. Validate evaluation function consistency")

def main():
    """Run V7P3R diff analysis"""
    
    # Default to current v7p3r engine path
    v7p3r_path = "../../V7P3R Chess Engine/v7p3r-chess-engine"
    
    if len(sys.argv) > 1:
        v7p3r_path = sys.argv[1]
    
    analyzer = V7P3RDiffAnalyzer(v7p3r_path)
    report = analyzer.generate_diff_analysis_report()
    
    # Save detailed report
    output_file = "v7p3r_diff_analysis_v9.0_vs_v9.1.json"
    import json
    with open(output_file, 'w') as f:
        # Convert Path objects to strings for JSON serialization
        json_report = {}
        for key, value in report.items():
            if key == 'version_files':
                json_report[key] = {k: str(v) if v else None for k, v in value.items()}
            else:
                json_report[key] = value
        json.dump(json_report, f, indent=2)
    
    print(f"\n💾 Detailed diff analysis saved to: {output_file}")

if __name__ == "__main__":
    main()
