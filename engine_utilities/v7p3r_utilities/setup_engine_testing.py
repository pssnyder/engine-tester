#!/usr/bin/env python3
"""
V7P3R Engine Batch Tester Generator
===================================

This utility generates batch files to run different V7P3R engine versions
with the same UCI interface for easy comparison testing.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

def create_engine_batch_files():
    """Create batch files for different engine versions"""
    
    # Define engine configurations
    engines = {
        'v7p3r_v7.0': {
            'description': 'V7P3R v7.0 Baseline',
            'executable': 'V7P3R_v7.0.exe',
            'working_dir': 'engines',
            'notes': 'Original high-performance baseline'
        },
        'v7p3r_v8.0': {
            'description': 'V7P3R v8.0 Enhanced',
            'executable': 'V7P3R_v8.0.exe', 
            'working_dir': 'engines',
            'notes': 'Enhanced version with regressions'
        },
        'v7p3r_v9.0': {
            'description': 'V7P3R v9.0 Memory Optimized',
            'executable': 'V7P3R_v9.0.exe',
            'working_dir': 'engines',
            'notes': 'Memory optimization improvements'
        },
        'v7p3r_v9.1_confidence': {
            'description': 'V7P3R v9.1 Confidence System',
            'executable': 'python',
            'args': ['src/v7p3r_uci.py'],
            'working_dir': '../V7P3R Chess Engine/v7p3r-chess-engine',
            'notes': 'New confidence-based multithreaded evaluation'
        }
    }
    
    batch_dir = Path("engine_batch_files")
    batch_dir.mkdir(exist_ok=True)
    
    print("Creating engine batch files...")
    
    for engine_name, config in engines.items():
        batch_file = batch_dir / f"{engine_name}.bat"
        
        # Create batch file content
        batch_content = f"""@echo off
REM {config['description']}
REM {config['notes']}

cd /d "%~dp0{config['working_dir']}"

REM Check if engine exists
"""
        
        if config['executable'] == 'python':
            # Python-based engine
            batch_content += f"""if not exist "{config['args'][0]}" (
    echo Error: {config['args'][0]} not found!
    echo Please ensure the V7P3R source is available.
    pause
    exit /b 1
)

echo Starting {config['description']}...
python {config['args'][0]}
"""
        else:
            # Executable engine
            batch_content += f"""if not exist "{config['executable']}" (
    echo Error: {config['executable']} not found!
    echo Please place the engine executable in the engines directory.
    pause
    exit /b 1
)

echo Starting {config['description']}...
{config['executable']}
"""
        
        # Write batch file
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        print(f"Created: {batch_file}")
    
    # Create master comparison batch file
    create_comparison_batch(batch_dir, engines)
    
    print(f"\nBatch files created in: {batch_dir}")
    print("\nUsage:")
    print("1. Run individual engines: double-click any .bat file")
    print("2. Run comparisons: use run_position_comparison.bat")

def create_comparison_batch(batch_dir: Path, engines: Dict):
    """Create a batch file that can run position comparisons"""
    
    comparison_file = batch_dir / "run_position_comparison.bat"
    
    content = f"""@echo off
REM V7P3R Engine Positional Comparison Tool
REM Runs the positional analyzer with all available engines

echo ================================
echo V7P3R Positional Analysis Tool
echo ================================
echo.

cd /d "%~dp0.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found! Please install Python 3.7+ and add to PATH.
    pause
    exit /b 1
)

REM Check if positional analyzer exists
if not exist "v7p3r_positional_analyzer.py" (
    echo Error: v7p3r_positional_analyzer.py not found!
    echo Please ensure you're running this from the engine-tester directory.
    pause
    exit /b 1
)

echo Running positional analysis...
echo This will compare engine performance across historical game positions.
echo.

python v7p3r_positional_analyzer.py

echo.
echo Analysis complete! Check the generated JSON report for detailed results.
pause
"""
    
    with open(comparison_file, 'w') as f:
        f.write(content)
    
    print(f"Created comparison tool: {comparison_file}")

def create_quick_position_tester():
    """Create a simple position tester for quick comparisons"""
    
    tester_file = Path("quick_position_test.py")
    
    content = '''#!/usr/bin/env python3
"""
Quick Position Tester
====================
Simple tool to test a single position with multiple engine versions
"""

import chess
import subprocess
import time
import sys
from pathlib import Path

def test_position(fen: str, time_limit: float = 2.0):
    """Test a position with available engines"""
    
    print(f"Testing position: {fen}")
    print(f"Time limit: {time_limit}s per engine")
    print("=" * 60)
    
    # Available engines (update paths as needed)
    engines = {
        'v9.1 Confidence': ['python', 'src/v7p3r_uci.py'],
    }
    
    # Add executable engines if they exist
    engine_dir = Path("engines")
    if engine_dir.exists():
        for exe_file in engine_dir.glob("V7P3R*.exe"):
            version = exe_file.stem.replace("V7P3R_", "")
            engines[version] = [str(exe_file)]
    
    results = {}
    
    for engine_name, command in engines.items():
        print(f"\\nTesting {engine_name}...")
        
        try:
            # Start engine process
            if command[0] == 'python':
                # Python engine - need to change directory
                working_dir = Path("../V7P3R Chess Engine/v7p3r-chess-engine")
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir if working_dir.exists() else None
                )
            else:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            # Send UCI commands
            commands = [
                "uci",
                f"position fen {fen}",
                f"go movetime {int(time_limit * 1000)}"
            ]
            
            start_time = time.time()
            
            for cmd in commands:
                process.stdin.write(cmd + "\\n")
                process.stdin.flush()
                
                if cmd == "uci":
                    # Wait for uciok
                    while True:
                        line = process.stdout.readline()
                        if "uciok" in line:
                            break
                        if time.time() - start_time > 5:  # Timeout
                            break
                
                elif cmd.startswith("go"):
                    # Collect analysis output
                    best_move = ""
                    depth = 0
                    evaluation = 0
                    nodes = 0
                    
                    while True:
                        line = process.stdout.readline().strip()
                        
                        if line.startswith("info"):
                            # Parse analysis info
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "depth" and i+1 < len(parts):
                                    depth = max(depth, int(parts[i+1]))
                                elif part == "score" and i+1 < len(parts):
                                    if parts[i+1] == "cp" and i+2 < len(parts):
                                        evaluation = int(parts[i+2])
                                elif part == "nodes" and i+1 < len(parts):
                                    nodes = int(parts[i+1])
                        
                        elif line.startswith("bestmove"):
                            best_move = line.split()[1] if len(line.split()) > 1 else ""
                            break
                        
                        if time.time() - start_time > time_limit + 2:  # Timeout with buffer
                            break
            
            process.stdin.write("quit\\n")
            process.stdin.flush()
            process.terminate()
            
            analysis_time = time.time() - start_time
            
            results[engine_name] = {
                'move': best_move,
                'evaluation': evaluation,
                'depth': depth,
                'nodes': nodes,
                'time': analysis_time
            }
            
            print(f"  Move: {best_move}")
            print(f"  Eval: {evaluation:+d} cp")
            print(f"  Depth: {depth}")
            print(f"  Nodes: {nodes:,}")
            print(f"  Time: {analysis_time:.2f}s")
            
        except Exception as e:
            print(f"  Error: {e}")
            results[engine_name] = {'error': str(e)}
    
    # Summary
    print("\\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    
    moves = set(r.get('move', '') for r in results.values())
    if len(moves) == 1:
        print("All engines chose the same move")
    else:
        print("⚠ Engines chose different moves:")
        for engine, result in results.items():
            print(f"  {engine}: {result.get('move', 'N/A')}")
    
    return results

if __name__ == "__main__":
    # Test positions
    test_positions = [
        # Starting position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        
        # Tactical position
        "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
        
        # Endgame
        "8/8/8/8/8/3k4/3P4/3K4 w - - 0 1"
    ]
    
    if len(sys.argv) > 1:
        # Custom FEN provided
        fen = sys.argv[1]
        test_position(fen)
    else:
        # Test default positions
        for i, fen in enumerate(test_positions):
            print(f"\\n{'='*80}")
            print(f"TEST POSITION {i+1}")
            print(f"{'='*80}")
            test_position(fen)
            
            if i < len(test_positions) - 1:
                input("\\nPress Enter to continue to next position...")
'''
    
    with open(tester_file, 'w') as f:
        f.write(content)
    
    print(f"Created quick tester: {tester_file}")

def main():
    """Main execution"""
    print("V7P3R Engine Testing Setup")
    print("=" * 40)
    
    create_engine_batch_files()
    create_quick_position_tester()
    
    print(f"""
Setup Complete!

Files created:
1. engine_batch_files/*.bat - Individual engine launchers
2. engine_batch_files/run_position_comparison.bat - Full positional analysis
3. quick_position_test.py - Simple position testing

Next steps:
1. Place engine executables in the 'engines' directory
2. Ensure V7P3R v9.1 source is available in the specified path
3. Run position tests to compare engine performance

Example usage:
    python quick_position_test.py
    python v7p3r_positional_analyzer.py
""")

if __name__ == "__main__":
    main()
