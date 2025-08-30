#!/usr/bin/env python3
"""
Simple Positional Test using V7P3R v9.1 executable
"""

import chess
import chess.pgn
import subprocess
import time
import json
from pathlib import Path

def test_engine_on_position(engine_path: str, fen: str, time_limit: float = 3.0):
    """Test engine on a single position"""
    try:
        # Start engine
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if not process.stdin or not process.stdout:
            return {'error': 'Could not communicate with engine'}
        
        # Initialize UCI
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Wait for uciok
        start_time = time.time()
        while time.time() - start_time < 5:
            line = process.stdout.readline().strip()
            if "uciok" in line:
                break
        else:
            process.terminate()
            return {'error': 'Engine did not respond to UCI'}
        
        # Set position
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        # Start search
        process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
        process.stdin.flush()
        
        # Collect results
        result = {'move': '', 'eval': 0, 'depth': 0, 'nodes': 0}
        search_start = time.time()
        
        while time.time() - search_start < time_limit + 2:
            line = process.stdout.readline().strip()
            
            if line.startswith("info"):
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "depth" and i+1 < len(parts):
                        try:
                            result['depth'] = max(result['depth'], int(parts[i+1]))
                        except:
                            pass
                    elif part == "score" and i+1 < len(parts):
                        if parts[i+1] == "cp" and i+2 < len(parts):
                            try:
                                result['eval'] = int(parts[i+2])
                            except:
                                pass
                        elif parts[i+1] == "mate" and i+2 < len(parts):
                            try:
                                mate_in = int(parts[i+2])
                                # Convert mate score to centipawns equivalent
                                result['eval'] = 900000 if mate_in > 0 else -900000
                            except:
                                pass
                    elif part == "nodes" and i+1 < len(parts):
                        try:
                            result['nodes'] = int(parts[i+1])
                        except:
                            pass
            
            elif line.startswith("bestmove"):
                result['move'] = line.split()[1] if len(line.split()) > 1 else ""
                break
        
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        
        return result
        
    except Exception as e:
        return {'error': str(e)}

def test_historical_positions():
    """Test a few positions from historical games"""
    
    print("=" * 60)
    print("V7P3R v9.1 Positional Analysis Test")
    print("=" * 60)
    
    # Test positions from various game phases
    test_positions = [
        {
            'name': 'Scholar\'s Mate Setup',
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
            'expected': 'Should find Qxf7# (checkmate)',
            'phase': 'tactical'
        },
        {
            'name': 'Opening Development',
            'fen': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
            'expected': 'Should develop pieces or advance center pawns',
            'phase': 'opening'
        },
        {
            'name': 'King and Pawn Endgame',
            'fen': '8/8/8/8/8/3k4/3P4/3K4 w - - 0 1',
            'expected': 'Should advance the pawn',
            'phase': 'endgame'
        },
        {
            'name': 'Pin Tactic',
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4',
            'expected': 'Should break the pin or develop safely',
            'phase': 'tactical'
        }
    ]
    
    engine_path = 'engines/V7P3R_v9.1.exe'
    
    if not Path(engine_path).exists():
        print(f"Error: Engine not found at {engine_path}")
        return
    
    results = []
    
    for i, pos in enumerate(test_positions, 1):
        print(f"\n--- Position {i}: {pos['name']} ---")
        print(f"FEN: {pos['fen']}")
        print(f"Phase: {pos['phase']}")
        print(f"Expected: {pos['expected']}")
        print("Analyzing...")
        
        result = test_engine_on_position(engine_path, pos['fen'], 3.0)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Best move: {result['move']}")
            print(f"Evaluation: {result['eval']:+d} cp")
            print(f"Depth: {result['depth']}")
            print(f"Nodes: {result['nodes']:,}")
            
            # Analysis
            if pos['phase'] == 'tactical' and pos['name'] == 'Scholar\'s Mate Setup':
                if result['move'].lower() in ['h5f7', 'qxf7', 'qf7']:
                    print("✅ EXCELLENT: Found the checkmate!")
                else:
                    print(f"❌ MISSED: Expected checkmate, got {result['move']}")
            
            elif pos['phase'] == 'endgame' and 'd2d3' in result['move'].lower() or 'd2d4' in result['move'].lower():
                print("✅ GOOD: Advancing the pawn")
            
            elif pos['phase'] == 'opening':
                print("✅ Engine made an opening move")
        
        results.append({
            'position': pos,
            'result': result
        })
        
        time.sleep(0.5)  # Brief pause between positions
    
    # Summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    
    tactical_success = 0
    total_tactical = 0
    
    for test in results:
        if test['position']['phase'] == 'tactical':
            total_tactical += 1
            if 'error' not in test['result']:
                if (test['position']['name'] == 'Scholar\'s Mate Setup' and 
                    test['result']['move'].lower() in ['h5f7', 'qxf7', 'qf7']):
                    tactical_success += 1
    
    print(f"Tactical positions solved: {tactical_success}/{total_tactical}")
    print(f"Overall engine responsiveness: {len([r for r in results if 'error' not in r['result']])}/{len(results)}")
    
    # Save results
    with open('v7p3r_v9_1_position_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: v7p3r_v9_1_position_test.json")
    print("✅ V7P3R v9.1 positional testing complete!")

if __name__ == "__main__":
    test_historical_positions()
