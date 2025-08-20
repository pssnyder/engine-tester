#!/usr/bin/env python3
"""
Dashboard Launcher

Simple script to launch the simplified chess engine analysis dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the dashboard"""
    print("🚀 Launching Chess Engine Analysis Dashboard...")
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent / "dashboard"
    os.chdir(dashboard_dir)
    
    print(f"📂 Dashboard directory: {dashboard_dir}")
    print("🌐 Starting Streamlit server...")
    print("📝 Dashboard will open in your default browser")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching dashboard: {e}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
