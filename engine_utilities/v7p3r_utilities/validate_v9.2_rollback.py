#!/usr/bin/env python3
"""
V7P3R v9.2 Validation Test
Tests the newly created v9.2 engine against v9.0 to ensure confidence system rollback worked
"""

import chess
import subprocess
import time
import sys
from pathlib import Path

def test_engine(engine_path: str, fen: str, time_limit: float = 3.0):
    """Test a single engine on a position"""
    
    try:
        # Start the engine process
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        if not process.stdin or not process.stdout:
            return {"error": "Could not communicate with engine"}
        
        start_time = time.time()
        
        # UCI handshake
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        uci_start = time.time()
        while time.time() - uci_start < 3:
            line = process.stdout.readline().strip()
            if "uciok" in line:
                break
        else:
            process.terminate()
            return {"error": "UCI timeout"}
        
        # Set position and search
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
        process.stdin.flush()
        
        # Collect results
        best_move = ""
        evaluation = 0
        depth = 0
        nodes = 0
        
        search_start = time.time()
        while time.time() - search_start < time_limit + 2:
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
                        elif parts[i+1] == "mate" and i+2 < len(parts):
                            try:
                                mate_in = int(parts[i+2])
                                evaluation = 900000 if mate_in > 0 else -900000
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
        
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        
        total_time = time.time() - start_time
        
        return {
            "move": best_move,
            "evaluation": evaluation,
            "depth": depth,
            "nodes": nodes,
            "time": total_time,
            "success": bool(best_move and best_move != "(none)")
        }
        
    except Exception as e:
        return {"error": str(e)}

def main():
    """Run V7P3R v9.2 validation tests"""
    
    print("=" * 80)
    print("V7P3R v9.2 VALIDATION TEST")
    print("Testing confidence system rollback success")
    print("=" * 80)
    
    # Test positions designed to identify confidence system interference
    test_positions = [
        {
            "name": "Starting Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "description": "Basic move ordering test"
        },
        {
            "name": "Tactical Position",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            "description": "Should find Qxf7# mate in 1"
        },
        {
            "name": "Complex Middlegame",
            "fen": "r2q1rk1/ppp2ppp/2n1bn2/2b1p3/3pP3/3P1NP1/PPP1NPB1/R1BQ1RK1 b - - 0 9",
            "description": "Position requiring deep calculation"
        },
        {
            "name": "King Safety Critical",
            "fen": "rnbqkb1r/pppp1ppp/4pn2/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 2 3",
            "description": "King safety evaluation test"
        },
        {
            "name": "Endgame Precision",
            "fen": "8/8/3k4/8/3K4/8/8/8 w - - 0 1",
            "description": "King and pawn endgame"
        }
    ]
    
    # Engines to test
    engines = {
        "v9.0": "engines/V7P3R/V7P3R_v9.0.exe",
        "v9.2": "engines/V7P3R/V7P3R_v9.2.exe"
    }
    
    # Validate engines exist
    missing_engines = []
    for name, path in engines.items():
        if not Path(path).exists():
            missing_engines.append(f"{name}: {path}")
    
    if missing_engines:
        print("❌ Missing engines:")
        for missing in missing_engines:
            print(f"  {missing}")
        return
    
    print(f"✓ Testing engines: {list(engines.keys())}")
    print(f"✓ Testing {len(test_positions)} positions")
    
    # Run tests
    results = {}
    
    for pos_idx, position in enumerate(test_positions, 1):
        print(f"\n" + "=" * 80)
        print(f"POSITION {pos_idx}/{len(test_positions)}: {position['name']}")
        print(f"FEN: {position['fen']}")
        print(f"Description: {position['description']}")
        print("=" * 80)
        
        position_results = {}
        
        for engine_name, engine_path in engines.items():
            print(f"\nTesting {engine_name}...")
            
            result = test_engine(engine_path, position['fen'], 3.0)
            position_results[engine_name] = result
            
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  ✓ Move: {result['move']}")
                print(f"    Eval: {result['evaluation']:+d} cp")
                print(f"    Depth: {result['depth']}")
                print(f"    Nodes: {result['nodes']:,}")
                print(f"    Time: {result['time']:.2f}s")
        
        results[position['name']] = position_results
        
        # Compare v9.0 vs v9.2
        if 'v9.0' in position_results and 'v9.2' in position_results:
            v90_result = position_results['v9.0']
            v92_result = position_results['v9.2']
            
            if 'error' not in v90_result and 'error' not in v92_result:
                print(f"\n📊 COMPARISON:")
                
                if v90_result['move'] == v92_result['move']:
                    print(f"  ✓ Same move: {v90_result['move']}")
                else:
                    print(f"  ⚠️  Different moves:")
                    print(f"    v9.0: {v90_result['move']}")
                    print(f"    v9.2: {v92_result['move']}")
                
                eval_diff = abs(v90_result['evaluation'] - v92_result['evaluation'])
                if eval_diff <= 50:  # Within 50 cp
                    print(f"  ✓ Similar evaluation (diff: {eval_diff} cp)")
                else:
                    print(f"  ⚠️  Large evaluation difference: {eval_diff} cp")
                
                depth_diff = abs(v90_result['depth'] - v92_result['depth'])
                if depth_diff <= 1:
                    print(f"  ✓ Similar search depth (diff: {depth_diff})")
                else:
                    print(f"  ⚠️  Depth difference: {depth_diff}")
    
    # Generate summary
    print(f"\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    total_positions = len(test_positions)
    successful_comparisons = 0
    move_agreements = 0
    
    for pos_name, pos_results in results.items():
        if 'v9.0' in pos_results and 'v9.2' in pos_results:
            v90 = pos_results['v9.0']
            v92 = pos_results['v9.2']
            
            if 'error' not in v90 and 'error' not in v92:
                successful_comparisons += 1
                if v90['move'] == v92['move']:
                    move_agreements += 1
    
    print(f"Successful comparisons: {successful_comparisons}/{total_positions}")
    print(f"Move agreements: {move_agreements}/{successful_comparisons}")
    
    if successful_comparisons == total_positions:
        agreement_rate = move_agreements / successful_comparisons if successful_comparisons > 0 else 0
        
        if agreement_rate >= 0.8:  # 80% agreement
            print(f"\n🎉 VALIDATION SUCCESS!")
            print(f"✓ v9.2 shows {agreement_rate:.1%} move agreement with v9.0")
            print(f"✓ Confidence system rollback appears successful")
            print(f"✓ Ready for v7.0 heuristic restoration")
        else:
            print(f"\n⚠️  VALIDATION CONCERNS:")
            print(f"⚠️  Only {agreement_rate:.1%} move agreement with v9.0")
            print(f"⚠️  May need further investigation")
    else:
        print(f"\n❌ VALIDATION INCOMPLETE:")
        print(f"❌ Not all positions could be compared")
        print(f"❌ Check engine functionality")

if __name__ == "__main__":
    main()
