#!/usr/bin/env python3
"""
Tactical Head-to-Head Engine Comparison with Stockfish Verification
Compare two engines on challenging tactical positions, using Stockfish as truth control
"""

import chess
import chess.engine
import subprocess
import sys
import time
import json
from datetime import datetime
import os

def verify_with_stockfish(fen, stockfish_path=r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe", depth=15):
    """Verify the best move using Stockfish as ground truth"""
    try:
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            board = chess.Board(fen)
            result = engine.analyse(board, chess.engine.Limit(depth=depth))
            
            best_move = result["pv"][0] if result.get("pv") else None
            score = result.get("score")
            
            return {
                "move": str(best_move) if best_move else None,
                "score": score.relative.score() if score and score.relative.score() is not None else None,
                "mate": score.relative.mate() if score and score.relative.mate() is not None else None,
                "depth": depth
            }
    except Exception as e:
        print(f"Stockfish verification failed: {e}")
        return None

def run_engine_analysis(engine_path, fen, time_limit=3.0):
    """Run engine analysis on a position and return the best move and evaluation"""
    try:
        # Create a simple UCI interaction
        proc = subprocess.Popen([engine_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, text=True, bufsize=1)
        
        # Send UCI commands
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        
        # Wait for uciok
        while True:
            line = proc.stdout.readline().strip()
            if "uciok" in line:
                break
            if not line:
                break
        
        # Set position
        proc.stdin.write(f"position fen {fen}\n")
        proc.stdin.flush()
        
        # Search
        proc.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
        proc.stdin.flush()
        
        best_move = None
        best_score = None
        nodes = 0
        depth = 0
        
        start_time = time.time()
        timeout = time_limit + 2.0
        
        while time.time() - start_time < timeout:
            line = proc.stdout.readline().strip()
            
            if "bestmove" in line:
                parts = line.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                break
            elif "info" in line and "depth" in line:
                parts = line.split()
                try:
                    if "depth" in parts:
                        depth_idx = parts.index("depth")
                        if depth_idx + 1 < len(parts):
                            depth = max(depth, int(parts[depth_idx + 1]))
                    
                    if "score cp" in line:
                        cp_idx = parts.index("cp")
                        if cp_idx + 1 < len(parts):
                            best_score = int(parts[cp_idx + 1])
                    elif "score mate" in line:
                        mate_idx = parts.index("mate")
                        if mate_idx + 1 < len(parts):
                            mate_moves = int(parts[mate_idx + 1])
                            best_score = 9900 if mate_moves > 0 else -9900
                    
                    if "nodes" in parts:
                        nodes_idx = parts.index("nodes")
                        if nodes_idx + 1 < len(parts):
                            nodes = int(parts[nodes_idx + 1])
                except (ValueError, IndexError):
                    pass
        
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.terminate()
        
        return {
            "move": best_move,
            "score": best_score,
            "depth": depth,
            "nodes": nodes,
            "time": time_limit
        }
        
    except Exception as e:
        print(f"Error running engine: {e}")
        return None

def compare_engines(engine1_path, engine2_path, positions, time_limit=3.0, stockfish_path=r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe"):
    """Compare two engines on a set of tactical positions with Stockfish verification"""
    
    results = {
        "engine1": {"path": engine1_path, "wins": 0, "draws": 0, "better_moves": 0, "stockfish_agreements": 0},
        "engine2": {"path": engine2_path, "wins": 0, "draws": 0, "better_moves": 0, "stockfish_agreements": 0},
        "positions": []
    }
    
    print(f"Comparing {engine1_path.split('/')[-1]} vs {engine2_path.split('/')[-1]}")
    print(f"Time limit: {time_limit}s per position")
    print(f"Using Stockfish verification: {stockfish_path}")
    print("="*80)
    
    for i, pos_data in enumerate(positions):
        fen = pos_data["fen"]
        description = pos_data.get("description", f"Position {i+1}")
        expected_move = pos_data.get("best_move", None)
        
        print(f"\nPosition {i+1}: {description}")
        print(f"FEN: {fen}")
        
        # First, verify with Stockfish what the actual best move should be
        stockfish_result = verify_with_stockfish(fen, stockfish_path)
        if stockfish_result and stockfish_result["move"]:
            stockfish_move = stockfish_result["move"]
            stockfish_score = stockfish_result["score"]
            print(f"🤖 Stockfish best move: {stockfish_move} (score: {stockfish_score})")
            
            # Update expected move to Stockfish's choice if none provided or verify existing
            if not expected_move:
                expected_move = stockfish_move
                print(f"   Using Stockfish move as ground truth")
            elif expected_move != stockfish_move:
                print(f"⚠️  Original expected move {expected_move} differs from Stockfish {stockfish_move}")
                print(f"   Using Stockfish move as ground truth")
                expected_move = stockfish_move
        else:
            print("❌ Stockfish verification failed")
            if not expected_move:
                print("   No ground truth available, skipping position")
                continue
        
        # Analyze with both engines
        result1 = run_engine_analysis(engine1_path, fen, time_limit)
        result2 = run_engine_analysis(engine2_path, fen, time_limit)
        
        if not result1 or not result2:
            print("❌ Error analyzing position")
            continue
        
        pos_result = {
            "fen": fen,
            "description": description,
            "expected_move": expected_move,
            "stockfish_move": stockfish_result["move"] if stockfish_result else None,
            "stockfish_score": stockfish_result["score"] if stockfish_result else None,
            "engine1": result1,
            "engine2": result2
        }
        
        print(f"Engine 1: {result1['move']} (score: {result1['score']}, depth: {result1['depth']}, nodes: {result1['nodes']})")
        print(f"Engine 2: {result2['move']} (score: {result2['score']}, depth: {result2['depth']}, nodes: {result2['nodes']})")
        
        # Compare results against Stockfish ground truth
        if expected_move:
            eng1_correct = result1['move'] == expected_move
            eng2_correct = result2['move'] == expected_move
            
            if eng1_correct:
                results["engine1"]["stockfish_agreements"] += 1
            if eng2_correct:
                results["engine2"]["stockfish_agreements"] += 1
            
            if eng1_correct and not eng2_correct:
                results["engine1"]["better_moves"] += 1
                print("✅ Engine 1 agrees with Stockfish!")
            elif eng2_correct and not eng1_correct:
                results["engine2"]["better_moves"] += 1
                print("✅ Engine 2 agrees with Stockfish!")
            elif eng1_correct and eng2_correct:
                print("✅ Both engines agree with Stockfish!")
            else:
                print("❌ Neither engine agrees with Stockfish")
                # In case of disagreement, check which is closer to Stockfish evaluation
                if stockfish_result and stockfish_result["score"] and result1['score'] and result2['score']:
                    diff1 = abs(result1['score'] - stockfish_result["score"])
                    diff2 = abs(result2['score'] - stockfish_result["score"])
                    if diff1 < diff2:
                        print(f"   Engine 1 evaluation closer to Stockfish (diff: {diff1} vs {diff2})")
                    elif diff2 < diff1:
                        print(f"   Engine 2 evaluation closer to Stockfish (diff: {diff2} vs {diff1})")
        
        # Compare by evaluation if available
        if result1['score'] is not None and result2['score'] is not None:
            score_diff = abs(result1['score'] - result2['score'])
            if score_diff > 50:  # Significant difference
                if result1['score'] > result2['score']:
                    print(f"📊 Engine 1 evaluates position better (+{score_diff} cp)")
                else:
                    print(f"📊 Engine 2 evaluates position better (+{score_diff} cp)")
        
        # Compare by depth
        if result1['depth'] > result2['depth']:
            print(f"🔍 Engine 1 searched deeper (depth {result1['depth']} vs {result2['depth']})")
        elif result2['depth'] > result1['depth']:
            print(f"🔍 Engine 2 searched deeper (depth {result2['depth']} vs {result1['depth']})")
        
        results["positions"].append(pos_result)
    
    return results

def main():
    # Define challenging tactical positions - let Stockfish determine the best moves
    tactical_positions = [
        {
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            "description": "Italian Game - Sharp tactical position"
        },
        {
            "fen": "rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5",
            "description": "Center pawn tension - tactical motifs available"
        },
        {
            "fen": "r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQ - 2 6",
            "description": "Pin tactics and piece coordination"
        },
        {
            "fen": "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
            "description": "Complex tactical puzzle position"
        },
        {
            "fen": "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
            "description": "Mutual tactical threats"
        },
        {
            "fen": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "description": "King and pawn endgame - precise play required"
        },
        {
            "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
            "description": "Opening position - strategic choices"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 b kq - 6 5",
            "description": "Development and tactical awareness test"
        },
        {
            "fen": "8/8/4k3/4p3/4K3/8/8/8 w - - 0 1",
            "description": "Basic king and pawn endgame"
        },
        {
            "fen": "r1bq1rk1/pp1nbppp/2p2n2/3p2B1/3P4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
            "description": "Middlegame position with multiple candidate moves"
        }
    ]
    
    # Engine paths
    engine1_path = "./engines/V7P3R/V7P3R_v10.6.exe"
    engine2_path = "./engines/V7P3R/V7P3R_v10.8.exe"
    
    # Try to find Stockfish
    stockfish_paths = [
        r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe",
        "stockfish",
        "./stockfish",
        "./stockfish.exe",
        "../../V7P3R Chess AI/v7p3r-chess-ai/stockfish.exe",
        "../../../V7P3R Chess AI/v7p3r-chess-ai/stockfish.exe", 
        "s:/Maker Stuff/Programming/Chess Engines/V7P3R Chess AI/v7p3r-chess-ai/stockfish.exe",
        "C:/stockfish/stockfish.exe"
    ]
    
    stockfish_path = None
    for path in stockfish_paths:
        if os.path.exists(path):
            stockfish_path = path
            break
    
    if not stockfish_path:
        # Use the primary Stockfish path as default
        stockfish_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe"
    
    print("V7P3R V10.6 vs V10.8 Tactical Head-to-Head Analysis")
    print("With Stockfish Verification Control")
    print("="*60)
    
    # Run comparison
    results = compare_engines(engine1_path, engine2_path, tactical_positions, 
                            time_limit=3.0, stockfish_path=stockfish_path)
    
    # Summary
    print("\n" + "="*80)
    print("TACTICAL COMPARISON SUMMARY")
    print("="*80)
    print(f"Engine 1 (V10.6) Stockfish agreements: {results['engine1']['stockfish_agreements']}")
    print(f"Engine 2 (V10.8) Stockfish agreements: {results['engine2']['stockfish_agreements']}")
    print(f"Engine 1 (V10.6) better moves: {results['engine1']['better_moves']}")
    print(f"Engine 2 (V10.8) better moves: {results['engine2']['better_moves']}")
    
    total_positions = len([p for p in results['positions'] if p.get('stockfish_move')])
    if total_positions > 0:
        eng1_accuracy = (results['engine1']['stockfish_agreements'] / total_positions) * 100
        eng2_accuracy = (results['engine2']['stockfish_agreements'] / total_positions) * 100
        print(f"\nStockfish Agreement Rates:")
        print(f"V10.6: {eng1_accuracy:.1f}% ({results['engine1']['stockfish_agreements']}/{total_positions})")
        print(f"V10.8: {eng2_accuracy:.1f}% ({results['engine2']['stockfish_agreements']}/{total_positions})")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v10_6_vs_v10_8_tactical_comparison_stockfish_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {filename}")

if __name__ == "__main__":
    main()