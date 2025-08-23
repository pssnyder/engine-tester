#!/usr/bin/env python3
"""
Dashboard Launcher Menu

Quick launcher for both the main analytics dashboard and 
the specialized Man vs Machine scoreboard.
"""

import subprocess
import sys
import os
from pathlib import Path

def show_menu():
    """Display the dashboard selection menu"""
    print("🚀 Chess Engine Dashboard Launcher")
    print("=" * 40)
    print("1. 📊 Main Analytics Dashboard (General engine analysis)")
    print("2. ⚔️ Man vs Machine Scoreboard (V7P3R vs SlowMate)")
    print("3. 🚀 Launch Both Dashboards")
    print("4. ❌ Exit")
    print("=" * 40)

def launch_main_dashboard():
    """Launch the main analytics dashboard"""
    print("📊 Launching Main Analytics Dashboard...")
    analytics_dir = Path(__file__).parent / "analytics_and_dashboard"
    launcher_script = analytics_dir / "launch_dashboard.py"
    
    if launcher_script.exists():
        subprocess.run([sys.executable, str(launcher_script)])
    else:
        print("❌ Main analytics dashboard not found")

def launch_mvm_dashboard():
    """Launch the Man vs Machine dashboard"""
    print("⚔️ Launching Man vs Machine Scoreboard...")
    mvm_dir = Path(__file__).parent / "man_vs_machine_scoreboard"
    launcher_script = mvm_dir / "launch_mvm_dashboard.py"
    
    if launcher_script.exists():
        subprocess.run([sys.executable, str(launcher_script)])
    else:
        print("❌ Man vs Machine dashboard not found")

def launch_both():
    """Launch both dashboards in parallel"""
    print("🚀 Launching both dashboards...")
    print("📊 Main dashboard will be on: http://localhost:8501")
    print("⚔️ MvM dashboard will be on: http://localhost:8502")
    
    # Launch main dashboard in background
    analytics_dir = Path(__file__).parent / "analytics_and_dashboard"
    main_launcher = analytics_dir / "launch_dashboard.py"
    
    # Launch MvM dashboard in background
    mvm_dir = Path(__file__).parent / "man_vs_machine_scoreboard"
    mvm_launcher = mvm_dir / "launch_mvm_dashboard.py"
    
    processes = []
    
    if main_launcher.exists():
        print("🌐 Starting main analytics dashboard...")
        p1 = subprocess.Popen([sys.executable, str(main_launcher)])
        processes.append(p1)
    
    if mvm_launcher.exists():
        print("🥊 Starting Man vs Machine scoreboard...")
        p2 = subprocess.Popen([sys.executable, str(mvm_launcher)])
        processes.append(p2)
    
    if processes:
        print("✅ Both dashboards launched!")
        print("📊 Main Analytics: http://localhost:8501")
        print("⚔️ Man vs Machine: http://localhost:8502")
        print("⏹️ Press Enter to stop all dashboards...")
        input()
        
        for p in processes:
            p.terminate()
        print("👋 All dashboards stopped")
    else:
        print("❌ No dashboards found to launch")

def main():
    """Main menu loop"""
    while True:
        try:
            show_menu()
            choice = input("Select option (1-4): ").strip()
            
            if choice == "1":
                launch_main_dashboard()
            elif choice == "2":
                launch_mvm_dashboard()
            elif choice == "3":
                launch_both()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
