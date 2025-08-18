#!/usr/bin/env python3
"""
Simplified Analytics Runner

Runs both unified and enhanced tournament analyzers in the correct order
and ensures consistent engine name consolidation throughout.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_analyzer(script_name, description):
    """Run an analyzer script and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=False, text=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Main execution function"""
    print("🏁 Starting Simplified Analytics Pipeline")
    print("📂 Ensuring we're in the analyzers directory...")
    
    # Change to analyzers directory
    analyzers_dir = Path(__file__).parent
    os.chdir(analyzers_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Check if required files exist
    required_files = [
        'unified_tournament_analyzer.py',
        'enhanced_tournament_analyzer.py',
        'name_mapper.py',
        '../dashboard/data/name_consolidation.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files found")
    
    # Run analyzers in order
    success = True
    
    # 1. Run unified tournament analyzer (main rankings and ELO data)
    if not run_analyzer('unified_tournament_analyzer.py', 'Unified Tournament Analyzer'):
        success = False
    
    # 2. Run enhanced tournament analyzer (supplementary behavioral data)
    if not run_analyzer('enhanced_tournament_analyzer.py', 'Enhanced Tournament Analyzer'):
        print("⚠️  Enhanced analyzer failed, but continuing with unified data")
        # Don't set success = False here since unified data is sufficient
    
    if success:
        print(f"\n{'='*60}")
        print("🎉 Analytics Pipeline Completed Successfully!")
        print("📊 Data saved to: ../dashboard/data/")
        print("🌐 Run the dashboard with: streamlit run ../dashboard/dashboard_simplified.py")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("❌ Analytics Pipeline Failed")
        print("Please check the error messages above")
        print(f"{'='*60}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
