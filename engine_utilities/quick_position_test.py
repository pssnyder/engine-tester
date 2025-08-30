#!/usr/bin/env python3
"""
Quick Position Tester for V7P3R Engines
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
        'v9.1 Confidence': {
            'command': ['engines/V7P3R_v9.1.exe'],
            'working_dir': '.'
        }
    }
    
    # Add executable engines if they exist
    engine_dir = Path("engines")
    if engine_dir.exists():
        for exe_file in engine_dir.glob("V7P3R*.exe"):
            version = exe_file.stem.replace("V7P3R_", "")
            engines[version] = {
                'command': [str(exe_file)],
                'working_dir': '.'
            }
    
    results = {}
    
    for engine_name, config in engines.items():
        print(f"\nTesting {engine_name}...")
        
        try:
            working_dir = Path(config['working_dir'])
            
            # Start engine process
            process = subprocess.Popen(
                config['command'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir if working_dir.exists() else None
            )
            
            if not process.stdin or not process.stdout:
                print("  Error: Could not communicate with engine")
                continue
            
            # Send UCI commands
            start_time = time.time()
            
            # Initialize
            process.stdin.write("uci\n")
            process.stdin.flush()
            
            # Wait for uciok
            uci_ready = False
            while not uci_ready and time.time() - start_time < 5:
                try:
                    line = process.stdout.readline()
                    if "uciok" in line:
                        uci_ready = True
                except:
                    break
            
            if not uci_ready:
                print("  Error: Engine did not respond to UCI")
                continue
            
            # Set position and search
            process.stdin.write(f"position fen {fen}\n")
            process.stdin.flush()
            
            search_start = time.time()
            process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
            process.stdin.flush()
            
            # Collect results
            best_move = ""
            depth = 0
            evaluation = 0
            nodes = 0
            
            while time.time() - search_start < time_limit + 2:
                try:
                    line = process.stdout.readline().strip()
                    
                    if line.startswith("info"):
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "depth" and i+1 < len(parts):
                                try:
                                    depth = max(depth, int(parts[i+1]))
                                except:
                                    pass
                            elif part == "score" and i+1 < len(parts):
                                if parts[i+1] == "cp" and i+2 < len(parts):
                                    try:
                                        evaluation = int(parts[i+2])
                                    except:
                                        pass
                            elif part == "nodes" and i+1 < len(parts):
                                try:
                                    nodes = int(parts[i+1])
                                except:
                                    pass
                    
                    elif line.startswith("bestmove"):
                        best_move = line.split()[1] if len(line.split()) > 1 else ""
                        break
                        
                except:
                    break
            
            process.stdin.write("quit\n")
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
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    
    moves = set(r.get('move', '') for r in results.values() if 'error' not in r)
    if len(moves) <= 1:
        print("All engines chose the same move (or only one engine worked)")
    else:
        print("Engines chose different moves:")
        for engine, result in results.items():
            if 'error' not in result:
                print(f"  {engine}: {result.get('move', 'N/A')}")
    
    return results

if __name__ == "__main__":
    # Test positions
    test_positions = [
        ("Starting position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("Tactical position", "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"),
        ("Endgame", "8/8/8/8/8/3k4/3P4/3K4 w - - 0 1")
    ]
    
    if len(sys.argv) > 1:
        # Custom FEN provided
        fen = sys.argv[1]
        test_position(fen)
    else:
        # Test default positions
        for i, (name, fen) in enumerate(test_positions):
            print(f"\n{'='*80}")
            print(f"TEST POSITION {i+1}: {name}")
            print(f"{'='*80}")
            test_position(fen)
            
            if i < len(test_positions) - 1:
                input("\nPress Enter to continue to next position...")
