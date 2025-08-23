#!/usr/bin/env python3
"""
Man vs Machine Dashboard Launcher

Launches the specialized V7P3R vs SlowMate competitive scoreboard dashboard.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_data_exists():
    """Check if analysis data exists"""
    data_file = Path(__file__).parent / "dashboard" / "data" / "mvm_analysis.json"
    return data_file.exists()

def run_analyzer():
    """Run the MvM analyzer to generate data"""
    print("📊 Running Man vs Machine analyzer...")
    analyzer_script = Path(__file__).parent / "analyzers" / "mvm_analyzer.py"
    
    try:
        subprocess.run([sys.executable, str(analyzer_script)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running analyzer: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Launch the Man vs Machine dashboard"""
    print("⚔️ Launching Man vs Machine Scoreboard Dashboard...")
    
    # Check if data exists, run analyzer if needed
    if not check_data_exists():
        print("📂 No analysis data found. Running analyzer first...")
        if not run_analyzer():
            print("❌ Failed to generate analysis data. Please check your tournament results.")
            return
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent / "dashboard"
    os.chdir(dashboard_dir)
    
    print(f"📂 Dashboard directory: {dashboard_dir}")
    print("🌐 Starting Man vs Machine Scoreboard...")
    print("📝 Dashboard will open in your default browser")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("🥊 V7P3R vs SlowMate competitive analysis loading...")
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "mvm_dashboard.py",
            "--server.address", "localhost",
            "--server.port", "8502",  # Different port from main dashboard
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Man vs Machine Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching dashboard: {e}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")
        print("💡 Make sure required packages are available: pip install plotly pandas")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
