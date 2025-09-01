#!/usr/bin/env python3
"""
Simplified V7P3R Tactical Comparison: v9.2 vs v7.0
Quick analysis of key tactical differences
"""

import subprocess
import time
from pathlib import Path

def test_position(engine_path, fen, time_limit=3.0):
    """Test engine on position and return move."""
    try:
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if not process.stdin or not process.stdout:
            return "", 0, 0
        
        # UCI handshake
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Wait for uciok
        start_time = time.time()
        while time.time() - start_time < 3:
            line = process.stdout.readline().strip()
            if "uciok" in line:
                break
        
        # Set position and search
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
        process.stdin.flush()
        
        best_move = ""
        evaluation = 0
        depth = 0
        
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
                    elif part == "score" and i+2 < len(parts) and parts[i+1] == "cp":
                        try:
                            evaluation = int(parts[i+2])
                        except:
                            pass
                    elif part == "score" and i+2 < len(parts) and parts[i+1] == "mate":
                        try:
                            mate_in = int(parts[i+2])
                            evaluation = 900000 if mate_in > 0 else -900000
                        except:
                            pass
            
            elif line.startswith("bestmove"):
                best_move = line.split()[1] if len(line.split()) > 1 else ""
                break
        
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        
        return best_move, evaluation, depth
        
    except Exception as e:
        return "", 0, 0

def main():
    """Run tactical comparison."""
    print("🔍 V7P3R TACTICAL COMPARISON: v9.2 vs v7.0")
    print("=" * 60)
    
    # Test positions - key tactical themes
    test_positions = [
        # Basic tactics
        ("8/8/8/3r4/8/3R4/3K4/8 w - - 0 1", "d3d5", "Pin: Rook pins rook"),
        ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7", "Mate in 1: Smothered mate"),
        ("8/8/8/3k4/8/8/3N4/3K4 w - - 0 1", "d2c4", "Fork: Knight forks king"),
        ("8/8/8/3kr3/8/8/3R4/3K4 w - - 0 1", "d2d5", "Skewer: Back rank skewer"),
        
        # Advanced tactics  
        ("rnbqkb1r/pppp1ppp/4pn2/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 2 3", "d4d5", "Discovery: Discovery attack"),
        ("r1bqkb1r/pppp1Q1p/2n2np1/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 5", "f7f8", "Mate in 2: Queen sacrifice"),
        
        # Positional tests
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "", "Opening: Starting position"),
        ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "", "Endgame: Rook endgame"),
    ]
    
    engines = {
        "v7.0": "engines/V7P3R/V7P3R_v7.0.exe",
        "v9.2": "engines/V7P3R/V7P3R_v9.2.exe"
    }
    
    # Verify engines
    for name, path in engines.items():
        if not Path(path).exists():
            print(f"❌ {name} not found: {path}")
            return
        print(f"✅ {name}: {path}")
    
    print(f"\n📊 TACTICAL COMPARISON RESULTS:")
    print("=" * 80)
    
    total_positions = len(test_positions)
    v70_correct = 0
    v92_correct = 0
    v70_better_eval = 0
    v92_better_eval = 0
    agreements = 0
    
    for i, (fen, solution, description) in enumerate(test_positions, 1):
        print(f"\n{i}. {description}")
        print(f"   FEN: {fen}")
        if solution:
            print(f"   Expected: {solution}")
        
        # Test both engines
        v70_move, v70_eval, v70_depth = test_position(engines["v7.0"], fen)
        v92_move, v92_eval, v92_depth = test_position(engines["v9.2"], fen)
        
        print(f"   v7.0:  {v70_move:8} eval={v70_eval:+6d} depth={v70_depth}")
        print(f"   v9.2:  {v92_move:8} eval={v92_eval:+6d} depth={v92_depth}")
        
        # Check correctness
        if solution:
            v70_right = v70_move == solution
            v92_right = v92_move == solution
            
            if v70_right:
                v70_correct += 1
            if v92_right:
                v92_correct += 1
                
            if v70_right and v92_right:
                print("   Result: ✅ Both correct")
            elif v70_right:
                print("   Result: 🔴 v7.0 better (correct vs wrong)")
            elif v92_right:
                print("   Result: 🟢 v9.2 better (correct vs wrong)")
            else:
                print("   Result: ❌ Both wrong")
        
        # Check move agreement
        if v70_move == v92_move:
            agreements += 1
            print("   Moves:  ✅ Same move")
        else:
            print("   Moves:  ⚠️  Different moves")
        
        # Check evaluation preference
        if abs(v70_eval - v92_eval) > 100:  # Significant difference
            if v70_eval > v92_eval:
                v70_better_eval += 1
                print(f"   Eval:   🔴 v7.0 more optimistic (+{v70_eval - v92_eval})")
            else:
                v92_better_eval += 1
                print(f"   Eval:   🟢 v9.2 more optimistic (+{v92_eval - v70_eval})")
        else:
            print("   Eval:   ✅ Similar evaluation")
    
    # Final summary
    print(f"\n🏆 FINAL COMPARISON SUMMARY:")
    print("=" * 60)
    
    solvable_positions = len([p for p in test_positions if p[1]])  # Positions with expected solutions
    
    if solvable_positions > 0:
        print(f"Tactical Accuracy:")
        print(f"  v7.0: {v70_correct}/{solvable_positions} ({v70_correct/solvable_positions*100:.1f}%)")
        print(f"  v9.2: {v92_correct}/{solvable_positions} ({v92_correct/solvable_positions*100:.1f}%)")
        
        if v92_correct > v70_correct:
            print(f"  🟢 v9.2 has better tactical accuracy (+{v92_correct - v70_correct} puzzles)")
        elif v70_correct > v92_correct:
            print(f"  🔴 v7.0 has better tactical accuracy (+{v70_correct - v92_correct} puzzles)")
        else:
            print(f"  ✅ Equal tactical accuracy")
    
    print(f"\nMove Agreement: {agreements}/{total_positions} ({agreements/total_positions*100:.1f}%)")
    print(f"Evaluation Preferences:")
    print(f"  v7.0 more optimistic: {v70_better_eval} positions")  
    print(f"  v9.2 more optimistic: {v92_better_eval} positions")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR v9.3:")
    print("=" * 60)
    
    if v70_correct > v92_correct:
        print("❗ v7.0 shows superior tactical calculation")
        print("  → Analyze v7.0 tactical evaluation functions")
        print("  → Restore aggressive tactical pattern recognition")
        print("  → Enhance forcing move prioritization")
    elif v92_correct > v70_correct:
        print("✅ v9.2 shows improved tactical calculation")
        print("  → Current evaluation improvements are working")
        print("  → Focus on maintaining tactical strength")
        print("  → Consider minor optimizations only")
    else:
        print("⚖️  Tactical performance is equivalent")
        print("  → Focus on positional evaluation improvements")
        print("  → Enhance endgame knowledge")
        print("  → Optimize search efficiency")
    
    if agreements < total_positions * 0.7:  # Less than 70% agreement
        print("⚠️  Significant move differences detected")
        print("  → Investigate evaluation function changes")
        print("  → Check piece-square table modifications")
        print("  → Review move ordering improvements")

if __name__ == "__main__":
    main()
