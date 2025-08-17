#!/usr/bin/env python3
"""
Master Analytics Pipeline

Runs the complete chess engine analysis pipeline:
1. Behavioral pattern analysis
2. Landscape visualization generation  
3. Comprehensive report generation
4. Dashboard data preparation
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def main():
    """Run the complete analytics pipeline"""
    print("🚀 Starting Master Chess Engine Analytics Pipeline")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get Python executable path
    python_exe = sys.executable
    
    # Pipeline steps
    steps = [
        {
            'command': f'"{python_exe}" unified_tournament_analyzer.py',
            'description': 'Unified Tournament Analysis',
            'required': True
        },
        {
            'command': f'"{python_exe}" analysis/behavioral_analyzer.py',
            'description': 'Engine Behavioral Pattern Analysis',
            'required': True
        },
        {
            'command': f'"{python_exe}" analysis/landscape_visualizer.py',
            'description': 'Engine Landscape Visualization Generation',
            'required': False
        },
        {
            'command': f'"{python_exe}" analysis/comprehensive_reporter.py',
            'description': 'Comprehensive Analysis Report Generation',
            'required': False
        }
    ]
    
    successful_steps = 0
    failed_steps = 0
    
    for step in steps:
        success = run_command(step['command'], step['description'])
        
        if success:
            successful_steps += 1
        else:
            failed_steps += 1
            if step['required']:
                print(f"💥 Critical step failed: {step['description']}")
                print("   Cannot continue pipeline execution.")
                break
    
    print("=" * 60)
    print("📊 Pipeline Execution Summary")
    print(f"✅ Successful steps: {successful_steps}")
    print(f"❌ Failed steps: {failed_steps}")
    
    if failed_steps == 0:
        print("🎉 All analytics completed successfully!")
        print("\n🎯 Generated Outputs:")
        print("   📄 results/unified_tournament_analysis.json")
        print("   🧠 results/behavioral_analysis.json") 
        print("   📊 results/comprehensive_analysis_report_*.md")
        print("   🌐 Enhanced dashboard at http://localhost:8504")
        print("\n🚀 Ready to explore your engine analytics!")
    else:
        print("⚠️  Some steps failed. Check the output above for details.")
    
    print(f"🏁 Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
