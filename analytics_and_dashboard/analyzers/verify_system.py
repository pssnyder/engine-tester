#!/usr/bin/env python3
"""
System Verification Test

This script verifies that the version comparison system is properly set up
and can access the required data and engines.
"""

import os
import sys
import json
import datetime
from pathlib import Path

def check_stockfish():
    """Check if Stockfish is available"""
    stockfish_path = "../../engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
    
    if os.path.exists(stockfish_path):
        print("✅ Stockfish found")
        return True
    else:
        print("❌ Stockfish not found at expected path")
        print(f"   Expected: {os.path.abspath(stockfish_path)}")
        
        # Try to find Stockfish elsewhere
        alt_paths = [
            "../../engines/Stockfish/stockfish.exe",
            "../../engines/stockfish.exe",
            "stockfish.exe"
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                print(f"   Found alternative: {os.path.abspath(alt_path)}")
                return alt_path
        
        return False

def check_engines():
    """Check if engine versions are available"""
    engines_dir = "../../engines"
    required_engines = {
        "SlowMate": ["Slowmate_v1.0.exe", "SlowMate_v2.0.exe"],
        "V7P3R": ["V7P3R_v4.1.exe", "V7P3R_v4.3.exe"],
        "Cece": ["Cece_v2.0.exe", "Cece_v2.3.exe"],
        "C0BR4": ["C0BR4_v1.0.exe", "C0BR4_v2.0.exe"]
    }
    
    found_engines = {}
    
    for engine_family, versions in required_engines.items():
        engine_dir = os.path.join(engines_dir, engine_family)
        if os.path.exists(engine_dir):
            available_files = os.listdir(engine_dir)
            found_versions = []
            missing_versions = []
            
            for version in versions:
                if version in available_files:
                    found_versions.append(version)
                else:
                    missing_versions.append(version)
            
            if found_versions:
                print(f"✅ {engine_family}: Found {len(found_versions)}/{len(versions)} versions")
                for v in found_versions:
                    print(f"   ✓ {v}")
                if missing_versions:
                    for v in missing_versions:
                        print(f"   ❌ {v} (missing)")
            else:
                print(f"❌ {engine_family}: No required versions found")
            
            found_engines[engine_family] = {
                "found": found_versions,
                "missing": missing_versions,
                "available": available_files
            }
        else:
            print(f"❌ {engine_family}: Directory not found")
            found_engines[engine_family] = {"found": [], "missing": versions, "available": []}
    
    return found_engines

def check_game_data():
    """Check if game data is available"""
    results_dir = "../../results"
    
    if not os.path.exists(results_dir):
        print("❌ Results directory not found")
        return False
    
    # Look for tournament directories and PGN files
    pgn_files = []
    tournament_dirs = []
    
    for item in os.listdir(results_dir):
        item_path = os.path.join(results_dir, item)
        if os.path.isdir(item_path):
            tournament_dirs.append(item)
            # Check for PGN files in tournament directory
            try:
                for file in os.listdir(item_path):
                    if file.endswith('.pgn'):
                        pgn_files.append(os.path.join(item_path, file))
            except:
                pass
        elif item.endswith('.pgn'):
            pgn_files.append(item_path)
    
    print(f"✅ Found {len(tournament_dirs)} tournament directories")
    print(f"✅ Found {len(pgn_files)} PGN files")
    
    if pgn_files:
        # Check a sample PGN file
        try:
            with open(pgn_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
                if '[White' in content and '[Black' in content:
                    print("✅ PGN files appear to be valid")
                else:
                    print("⚠️  PGN files may be malformed")
        except Exception as e:
            print(f"⚠️  Error reading PGN file: {e}")
    
    return len(pgn_files) > 0

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ['chess', 'asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} package available")
        except ImportError:
            print(f"❌ {package} package missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def main():
    """Run all verification checks"""
    print("🔍 Chess Engine Version Comparison System - Verification")
    print("=" * 60)
    
    print("\n📦 Checking Dependencies...")
    deps_ok = check_dependencies()
    
    print("\n🏗️ Checking Stockfish Engine...")
    stockfish_ok = check_stockfish()
    
    print("\n🎯 Checking Engine Versions...")
    engines_data = check_engines()
    
    print("\n📊 Checking Game Data...")
    data_ok = check_game_data()
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if deps_ok:
        print("✅ Dependencies: Ready")
    else:
        print("❌ Dependencies: Missing packages")
        print("   Run: pip install -r ../../requirements.txt")
    
    if stockfish_ok:
        print("✅ Stockfish: Ready")
    else:
        print("❌ Stockfish: Not available")
        print("   Download from: https://stockfishchess.org/download/")
    
    # Check engine readiness
    ready_engines = []
    for engine, data in engines_data.items():
        if len(data["found"]) >= 1:  # At least one version found
            ready_engines.append(engine)
    
    if ready_engines:
        print(f"✅ Engines: {len(ready_engines)}/4 ready ({', '.join(ready_engines)})")
    else:
        print("❌ Engines: No engines ready for analysis")
    
    if data_ok:
        print("✅ Game Data: Available")
    else:
        print("❌ Game Data: No PGN files found")
    
    # Overall assessment
    all_ready = deps_ok and stockfish_ok and len(ready_engines) > 0 and data_ok
    
    print("\n" + "🎯 OVERALL STATUS")
    if all_ready:
        print("✅ System is ready for version comparison analysis!")
        print("\nNext steps:")
        print("  1. Run: python run_version_comparison.py")
        print("  2. Or: python batch_version_comparison.py")
    else:
        print("⚠️  System needs setup before analysis can run")
        print("\nRequired fixes:")
        if not deps_ok:
            print("  • Install missing Python packages")
        if not stockfish_ok:
            print("  • Install Stockfish engine")
        if len(ready_engines) == 0:
            print("  • Ensure engine executables are available")
        if not data_ok:
            print("  • Ensure tournament PGN files are in results directory")
    
    # Save verification results
    verification_report = {
        "timestamp": str(datetime.datetime.now()),
        "dependencies": deps_ok,
        "stockfish": stockfish_ok,
        "engines": engines_data,
        "game_data": data_ok,
        "ready_engines": ready_engines,
        "overall_ready": all_ready
    }
    
    try:
        with open("system_verification.json", "w") as f:
            json.dump(verification_report, f, indent=2, default=str)
        print(f"\n📄 Verification report saved to: system_verification.json")
    except:
        pass

if __name__ == "__main__":
    main()
