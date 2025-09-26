#!/usr/bin/env python3
"""
Historical Game Position Analysis
Extract and analyze positions from the Engine Regression Battle PGN
"""

import chess
import chess.pgn
import subprocess
import time
import json
from pathlib import Path

def extract_key_positions_from_pgn(pgn_file: str, max_positions: int = 10):
    """Extract key positions from the PGN file"""
    positions = []
    
    try:
        with open(pgn_file, 'r') as f:
            while len(positions) < max_positions:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                
                board = game.board()
                moves = list(game.mainline_moves())
                
                # Extract positions at key move numbers
                for i, move in enumerate(moves):
                    board.push(move)
                    move_number = (i + 2) // 2  # Convert to standard move numbering
                    
                    # Extract positions at moves 5, 10, 15, 20, etc.
                    if move_number in [5, 10, 15, 20, 25, 30] and len(positions) < max_positions:
                        phase = 'opening' if move_number <= 10 else 'middlegame' if move_number <= 25 else 'endgame'
                        positions.append({
                            'fen': board.fen(),
                            'move_number': move_number,
                            'phase': phase,
                            'game_info': {
                                'white': game.headers.get('White', 'Unknown'),
                                'black': game.headers.get('Black', 'Unknown'),
                                'result': game.headers.get('Result', 'Unknown')
                            }
                        })
                        
                        if len(positions) >= max_positions:
                            break
    
    except Exception as e:
        print(f"Error reading PGN: {e}")
    
    return positions

def test_engine_on_position(engine_path: str, fen: str, time_limit: float = 2.0):
    """Test engine on a single position"""
    try:
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if not process.stdin or not process.stdout:
            return {'error': 'Could not communicate with engine'}
        
        # UCI handshake
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        start_time = time.time()
        while time.time() - start_time < 3:
            line = process.stdout.readline().strip()
            if "uciok" in line:
                break
        else:
            process.terminate()
            return {'error': 'UCI timeout'}
        
        # Set position and search
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
        process.stdin.flush()
        
        # Collect results
        result = {'move': '', 'eval': 0, 'depth': 0, 'nodes': 0, 'time': 0}
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
                    elif part == "nodes" and i+1 < len(parts):
                        try:
                            result['nodes'] = int(parts[i+1])
                        except:
                            pass
            
            elif line.startswith("bestmove"):
                result['move'] = line.split()[1] if len(line.split()) > 1 else ""
                result['time'] = time.time() - search_start
                break
        
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        
        return result
        
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 70)
    print("HISTORICAL GAME POSITION ANALYSIS - V7P3R v9.1")
    print("=" * 70)
    
    # Locate PGN file
    pgn_file = "../engine-metrics/game_records/Engine Battle 20250829/Engine Regression Battle 20250829.pgn"
    
    if not Path(pgn_file).exists():
        print(f"Error: PGN file not found at {pgn_file}")
        return
    
    # Engine path
    engine_path = 'engines/V7P3R_v9.1.exe'
    
    if not Path(engine_path).exists():
        print(f"Error: Engine not found at {engine_path}")
        return
    
    print(f"PGN file: {pgn_file}")
    print(f"Engine: {engine_path}")
    print(f"Extracting positions...")
    
    # Extract positions
    positions = extract_key_positions_from_pgn(pgn_file, 8)
    
    if not positions:
        print("No positions extracted from PGN file")
        return
    
    print(f"Extracted {len(positions)} positions for analysis")
    print()
    
    # Analyze each position
    results = []
    
    for i, pos in enumerate(positions, 1):
        print(f"--- Position {i}/{len(positions)} ---")
        print(f"Move {pos['move_number']} ({pos['phase']})")
        print(f"Game: {pos['game_info']['white']} vs {pos['game_info']['black']}")
        print(f"FEN: {pos['fen'][:50]}...")
        
        result = test_engine_on_position(engine_path, pos['fen'], 2.0)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Move: {result['move']} | Eval: {result['eval']:+d} cp | Depth: {result['depth']} | Nodes: {result['nodes']:,} | Time: {result['time']:.2f}s")
        
        results.append({
            'position': pos,
            'analysis': result
        })
        
        print()
        time.sleep(0.3)  # Brief pause
    
    # Summary
    print("=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    successful_analyses = [r for r in results if 'error' not in r['analysis']]
    failed_analyses = [r for r in results if 'error' in r['analysis']]
    
    print(f"Successful analyses: {len(successful_analyses)}/{len(results)}")
    print(f"Failed analyses: {len(failed_analyses)}")
    
    if successful_analyses:
        avg_depth = sum(r['analysis']['depth'] for r in successful_analyses) / len(successful_analyses)
        avg_nodes = sum(r['analysis']['nodes'] for r in successful_analyses) / len(successful_analyses)
        avg_time = sum(r['analysis']['time'] for r in successful_analyses) / len(successful_analyses)
        
        print(f"Average search depth: {avg_depth:.1f}")
        print(f"Average nodes searched: {avg_nodes:,.0f}")
        print(f"Average analysis time: {avg_time:.2f}s")
    
    # Save detailed results
    output_file = 'historical_game_analysis_v9_1.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    print("🎉 Historical game analysis complete!")

if __name__ == "__main__":
    main()
