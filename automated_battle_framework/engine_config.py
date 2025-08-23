#!/usr/bin/env python3
"""
🔧 Engine Configuration Helper
============================

Helps set up and validate engine configurations for the battle framework.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

def find_engine_paths() -> Dict[str, str]:
    """Find common engine paths automatically"""
    
    # Base directories to search
    base_dirs = [
        Path("s:/Maker Stuff/Programming/Chess Engines"),
        Path.cwd().parent.parent.parent,  # Go up from automated_battle_framework
    ]
    
    engine_paths = {}
    
    for base_dir in base_dirs:
        if not base_dir.exists():
            continue
        
        # Look for V7P3R
        v7p3r_candidates = [
            base_dir / "V7P3R Chess Engine" / "v7p3r-chess-engine",
            base_dir / "v7p3r-chess-engine",
            base_dir / "V7P3R"
        ]
        
        for candidate in v7p3r_candidates:
            if candidate.exists() and (candidate / "play_chess.py").exists():
                engine_paths["v7p3r"] = str(candidate)
                break
        
        # Look for SlowMate
        slowmate_candidates = [
            base_dir / "SlowMate Chess Engine" / "slowmate-chess-engine" / "src",
            base_dir / "slowmate-chess-engine" / "src",
            base_dir / "SlowMate" / "src"
        ]
        
        for candidate in slowmate_candidates:
            if candidate.exists() and (candidate / "slowmate_uci.py").exists():
                engine_paths["slowmate"] = str(candidate)
                break
        
        # Look for C0BR4 or other executables
        exe_candidates = [
            base_dir / "Chess Engine Playground" / "engine-tester" / "downloaded_engines",
            base_dir / "engine-tester" / "downloaded_engines",
            base_dir / "downloaded_engines"
        ]
        
        for candidate in exe_candidates:
            if candidate.exists():
                cobra_exe = candidate / "C0BR4.exe"
                if cobra_exe.exists():
                    engine_paths["cobra"] = str(cobra_exe)
                break
    
    return engine_paths

def validate_engine(name: str, path: str, executable: str, args: List[str]) -> bool:
    """Validate that an engine can be found and is likely to work"""
    
    engine_path = Path(path)
    
    # Check if path exists
    if not engine_path.exists():
        print(f"❌ {name}: Path does not exist: {path}")
        return False
    
    # Check executable
    if executable == "python":
        # For Python engines, check if the main script exists
        if args:
            main_script = engine_path / args[0]
            if not main_script.exists():
                print(f"❌ {name}: Python script not found: {main_script}")
                return False
        print(f"✅ {name}: Found Python script at {engine_path}")
        return True
    
    else:
        # For executable engines
        exe_path = Path(executable)
        if exe_path.is_absolute():
            if not exe_path.exists():
                print(f"❌ {name}: Executable not found: {executable}")
                return False
        else:
            # Check in the engine path
            exe_in_path = engine_path / executable
            if not exe_in_path.exists():
                print(f"❌ {name}: Executable not found: {exe_in_path}")
                return False
        
        print(f"✅ {name}: Found executable")
        return True

def create_engine_configs():
    """Create and validate engine configurations"""
    from engine_battle_framework import EngineConfig
    
    print("🔍 Searching for engines...")
    engine_paths = find_engine_paths()
    
    configs = []
    
    # V7P3R Configuration
    if "v7p3r" in engine_paths:
        v7p3r_config = EngineConfig(
            name="V7P3R_Current",
            path=engine_paths["v7p3r"],
            executable="python",
            args=["play_chess.py"],
            type="python_v7p3r"
        )
        
        if validate_engine("V7P3R", v7p3r_config.path, v7p3r_config.executable, v7p3r_config.args):
            configs.append(v7p3r_config)
    else:
        print("⚠️  V7P3R engine not found")
    
    # SlowMate Configuration
    if "slowmate" in engine_paths:
        slowmate_config = EngineConfig(
            name="SlowMate_Current",
            path=engine_paths["slowmate"],
            executable="python",
            args=["slowmate_uci.py"],
            type="python_slowmate"
        )
        
        if validate_engine("SlowMate", slowmate_config.path, slowmate_config.executable, slowmate_config.args):
            configs.append(slowmate_config)
    else:
        print("⚠️  SlowMate engine not found")
    
    # C0BR4 Configuration
    if "cobra" in engine_paths:
        cobra_config = EngineConfig(
            name="C0BR4_Control",
            path=str(Path(engine_paths["cobra"]).parent),
            executable=engine_paths["cobra"],
            args=[],
            type="exe_control"
        )
        
        if validate_engine("C0BR4", cobra_config.path, cobra_config.executable, cobra_config.args):
            configs.append(cobra_config)
    else:
        print("⚠️  C0BR4 control engine not found")
    
    return configs

def test_engines_individually():
    """Test each engine individually to make sure they respond to UCI"""
    import asyncio
    from engine_battle_framework import UCIEngine
    
    configs = create_engine_configs()
    
    async def test_single_engine(config):
        print(f"\n🧪 Testing {config.name}...")
        try:
            engine = UCIEngine(config)
            await engine.start()
            
            # Test basic UCI communication
            response = await engine.send_command("uci")
            if "uciok" in response:
                print(f"  ✅ UCI communication working")
            else:
                print(f"  ❌ UCI communication failed")
                return False
            
            # Test ready check
            response = await engine.send_command("isready") 
            if "readyok" in response:
                print(f"  ✅ Engine ready")
            else:
                print(f"  ❌ Engine not ready")
                return False
            
            await engine.stop()
            print(f"  ✅ {config.name} working correctly")
            return True
            
        except Exception as e:
            print(f"  ❌ {config.name} failed: {e}")
            return False
    
    async def test_all():
        working_engines = []
        for config in configs:
            if await test_single_engine(config):
                working_engines.append(config)
        
        print(f"\n📋 Summary:")
        print(f"   Found engines: {len(configs)}")
        print(f"   Working engines: {len(working_engines)}")
        
        if len(working_engines) >= 2:
            print(f"   ✅ Ready for battles!")
        else:
            print(f"   ❌ Need at least 2 working engines for battles")
        
        return working_engines
    
    return asyncio.run(test_all())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Engine Configuration Helper")
    parser.add_argument("--test", action="store_true", help="Test engines individually")
    parser.add_argument("--find", action="store_true", help="Find engine paths")
    args = parser.parse_args()
    
    print("🔧 Engine Configuration Helper")
    print("=" * 40)
    
    if args.find:
        print("🔍 Searching for engines...")
        paths = find_engine_paths()
        for name, path in paths.items():
            print(f"  {name}: {path}")
    
    elif args.test:
        working_engines = test_engines_individually()
        
        if len(working_engines) >= 2:
            print(f"\n🚀 Ready to run battles! Try:")
            print(f"   python battle_runner.py --mode demo")
    
    else:
        # Default: show found configurations
        configs = create_engine_configs()
        
        print(f"\n📋 Engine Configurations:")
        for config in configs:
            print(f"  {config.name}:")
            print(f"    Path: {config.path}")
            print(f"    Type: {config.type}")
            print(f"    Command: {config.executable} {' '.join(config.args)}")
        
        print(f"\n🧪 To test engines: python engine_config.py --test")
        print(f"🔍 To find paths: python engine_config.py --find")
