#!/usr/bin/env python3
"""
V7P3R Refined Stockfish Comparison - Debug and Focused Analysis
"""

import subprocess
import time
import chess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

class RefinedStockfishComparator:
    """Refined comparison with better engine communication."""
    
    def __init__(self):
        self.engines = {
            "v7.0": "engines/V7P3R/V7P3R_v7.0.exe",
            "v9.2": "engines/V7P3R/V7P3R_v9.2.exe",
            "stockfish": "engines/Stockfish/stockfish-windows-x86-64-avx2.exe"
        }
        
        # Simpler, more reliable test positions
        self.test_positions = [
            {
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "description": "Starting position",
                "phase": "opening",
                "expected_moves": ["e2e4", "d2d4", "g1f3", "c2c4"]
            },
            {
                "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
                "description": "King's pawn game",
                "phase": "opening",
                "expected_moves": ["g1f3", "f1c4", "d2d3"]
            },
            {
                "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
                "description": "Italian Game",
                "phase": "opening",
                "expected_moves": ["d2d3", "c4d5", "e1g1"]
            },
            {
                "fen": "r2q1rk1/ppp2ppp/2n1bn2/2bpP3/3P4/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 10",
                "description": "Complex middlegame",
                "phase": "middlegame",
                "expected_moves": ["e5f6", "f3g5", "h2h4"]
            },
            {
                "fen": "r3r1k1/pppq1ppp/3p1n2/4p3/4P3/2NP1Q2/PPP2PPP/R4RK1 w - - 0 12",
                "description": "Heavy piece coordination",
                "phase": "middlegame",
                "expected_moves": ["f3f4", "f3e3", "c3d5"]
            },
            {
                "fen": "8/4kp2/6p1/4K3/6P1/8/5P2/8 w - - 0 40",
                "description": "King and pawn endgame",
                "phase": "endgame",
                "expected_moves": ["g4g5", "f2f4", "e5f5"]
            }
        ]
    
    def test_engine_simple(self, engine_path: str, fen: str, time_ms: int = 3000) -> Dict:
        """Simplified engine test with better error handling."""
        engine_name = Path(engine_path).stem
        result = {
            "engine": engine_name,
            "move": "",
            "eval": 0,
            "depth": 0,
            "time": 0.0,
            "success": False,
            "error": ""
        }
        
        try:
            process = subprocess.Popen(
                [engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            start_time = time.time()
            
            # Send UCI commands with timeouts
            commands = [
                "uci",
                "isready",
                f"position fen {fen}",
                f"go movetime {time_ms}"
            ]
            
            for cmd in commands:
                if not process.stdin:
                    result["error"] = "stdin unavailable"
                    return result
                    
                process.stdin.write(cmd + "\n")
                process.stdin.flush()
                
                if cmd == "uci":
                    # Wait for uciok
                    timeout = time.time() + 5
                    while time.time() < timeout:
                        if not process.stdout:
                            break
                        line = process.stdout.readline().strip()
                        if "uciok" in line:
                            break
                        if not line:
                            time.sleep(0.1)
                    else:
                        result["error"] = "uciok timeout"
                        process.terminate()
                        return result
                        
                elif cmd == "isready":
                    # Wait for readyok
                    timeout = time.time() + 3
                    while time.time() < timeout:
                        if not process.stdout:
                            break
                        line = process.stdout.readline().strip()
                        if "readyok" in line:
                            break
                        if not line:
                            time.sleep(0.1)
                    else:
                        result["error"] = "readyok timeout"
                        process.terminate()
                        return result
            
            # Read search results
            search_timeout = time.time() + (time_ms / 1000) + 3
            best_move = ""
            evaluation = 0
            depth = 0
            
            while time.time() < search_timeout:
                if not process.stdout:
                    break
                    
                line = process.stdout.readline().strip()
                if not line:
                    time.sleep(0.1)
                    continue
                
                if line.startswith("info"):
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "depth" and i+1 < len(parts):
                            try:
                                depth = max(depth, int(parts[i+1]))
                            except:
                                pass
                        elif part == "score" and i+2 < len(parts):
                            if parts[i+1] == "cp":
                                try:
                                    evaluation = int(parts[i+2])
                                except:
                                    pass
                            elif parts[i+1] == "mate":
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
            
            total_time = time.time() - start_time
            
            if best_move and best_move != "(none)":
                result.update({
                    "move": best_move,
                    "eval": evaluation,
                    "depth": depth,
                    "time": total_time,
                    "success": True
                })
            else:
                result["error"] = "no move returned"
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
    def run_comparison(self):
        """Run focused comparison on reliable positions."""
        print("🔍 V7P3R REFINED STOCKFISH COMPARISON")
        print("=" * 60)
        
        # Verify engines
        for name, path in self.engines.items():
            if not Path(path).exists():
                print(f"❌ {name}: {path} not found")
                return
            print(f"✅ {name}: {path}")
        
        results = []
        successful_comparisons = 0
        
        for i, pos_data in enumerate(self.test_positions, 1):
            fen = pos_data["fen"]
            description = pos_data["description"]
            phase = pos_data["phase"]
            
            print(f"\n📍 Position {i}: {description} ({phase})")
            print(f"   FEN: {fen}")
            
            # Test Stockfish first (reference)
            print("   🤖 Stockfish analysis...")
            sf_result = self.test_engine_simple(self.engines["stockfish"], fen, 5000)
            
            # Test V7P3R engines
            print("   🧠 V7P3R v7.0...")
            v70_result = self.test_engine_simple(self.engines["v7.0"], fen, 3000)
            
            print("   🧠 V7P3R v9.2...")
            v92_result = self.test_engine_simple(self.engines["v9.2"], fen, 3000)
            
            # Display results
            if sf_result["success"]:
                print(f"   📊 Stockfish: {sf_result['move']} (eval: {sf_result['eval']:+d}, depth: {sf_result['depth']})")
            else:
                print(f"   ❌ Stockfish failed: {sf_result['error']}")
            
            if v70_result["success"]:
                print(f"   📊 v7.0: {v70_result['move']} (eval: {v70_result['eval']:+d}, depth: {v70_result['depth']})")
            else:
                print(f"   ❌ v7.0 failed: {v70_result['error']}")
            
            if v92_result["success"]:
                print(f"   📊 v9.2: {v92_result['move']} (eval: {v92_result['eval']:+d}, depth: {v92_result['depth']})")
            else:
                print(f"   ❌ v9.2 failed: {v92_result['error']}")
            
            # Grade moves if all successful
            if sf_result["success"] and v70_result["success"] and v92_result["success"]:
                successful_comparisons += 1
                
                # Simple move agreement check
                sf_move = sf_result["move"]
                v70_move = v70_result["move"]
                v92_move = v92_result["move"]
                
                v70_matches_sf = (v70_move == sf_move)
                v92_matches_sf = (v92_move == sf_move)
                
                # Evaluation comparison
                sf_eval = sf_result["eval"]
                v70_eval = v70_result["eval"]
                v92_eval = v92_result["eval"]
                
                print(f"   🎯 Move agreement: v7.0={v70_matches_sf}, v9.2={v92_matches_sf}")
                print(f"   📈 Eval comparison: SF={sf_eval:+d}, v7.0={v70_eval:+d}, v9.2={v92_eval:+d}")
                
                # Simple scoring
                v70_score = (1 if v70_matches_sf else 0) + (1 if abs(v70_eval - sf_eval) < abs(v92_eval - sf_eval) else 0)
                v92_score = (1 if v92_matches_sf else 0) + (1 if abs(v92_eval - sf_eval) < abs(v70_eval - sf_eval) else 0)
                
                if v70_score > v92_score:
                    winner = "v7.0"
                elif v92_score > v70_score:
                    winner = "v9.2"
                else:
                    winner = "tie"
                
                print(f"   🏆 Winner: {winner}")
                
                comparison_data = {
                    "position": description,
                    "phase": phase,
                    "fen": fen,
                    "stockfish": sf_result,
                    "v7.0": v70_result,
                    "v9.2": v92_result,
                    "v70_matches_sf": v70_matches_sf,
                    "v92_matches_sf": v92_matches_sf,
                    "winner": winner
                }
                
                results.append(comparison_data)
            
            print()
        
        # Summary
        if successful_comparisons == 0:
            print("❌ No successful comparisons - check engine communication")
            return
        
        print(f"📊 SUCCESSFUL COMPARISONS: {successful_comparisons}/{len(self.test_positions)}")
        
        # Count wins
        v70_wins = sum(1 for r in results if r["winner"] == "v7.0")
        v92_wins = sum(1 for r in results if r["winner"] == "v9.2")
        ties = sum(1 for r in results if r["winner"] == "tie")
        
        # Move agreement statistics
        v70_sf_agreement = sum(1 for r in results if r["v70_matches_sf"])
        v92_sf_agreement = sum(1 for r in results if r["v92_matches_sf"])
        
        print(f"\n🏆 FINAL SCORES:")
        print(f"V7P3R v7.0: {v70_wins} wins ({v70_wins/successful_comparisons*100:.1f}%)")
        print(f"V7P3R v9.2: {v92_wins} wins ({v92_wins/successful_comparisons*100:.1f}%)")
        print(f"Ties: {ties} ({ties/successful_comparisons*100:.1f}%)")
        
        print(f"\n🎯 STOCKFISH MOVE AGREEMENT:")
        print(f"V7P3R v7.0: {v70_sf_agreement}/{successful_comparisons} ({v70_sf_agreement/successful_comparisons*100:.1f}%)")
        print(f"V7P3R v9.2: {v92_sf_agreement}/{successful_comparisons} ({v92_sf_agreement/successful_comparisons*100:.1f}%)")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"V7P3R_refined_comparison_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump({
                "summary": {
                    "successful_comparisons": successful_comparisons,
                    "total_positions": len(self.test_positions),
                    "v70_wins": v70_wins,
                    "v92_wins": v92_wins,
                    "ties": ties,
                    "v70_sf_agreement": v70_sf_agreement,
                    "v92_sf_agreement": v92_sf_agreement
                },
                "detailed_results": results
            }, f, indent=2)
        
        print(f"\n📄 Results saved: {results_file}")
        
        # Analysis
        if v92_wins > v70_wins:
            print("🟢 V9.2 shows better overall performance")
        elif v70_wins > v92_wins:
            print("🔴 V7.0 shows better overall performance")
        else:
            print("🟡 Both engines show similar performance")
        
        if v92_sf_agreement > v70_sf_agreement:
            print("🎯 V9.2 shows better agreement with Stockfish moves")
        elif v70_sf_agreement > v92_sf_agreement:
            print("🎯 V7.0 shows better agreement with Stockfish moves")
        else:
            print("🎯 Both engines show similar Stockfish agreement")

def main():
    comparator = RefinedStockfishComparator()
    comparator.run_comparison()

if __name__ == "__main__":
    main()
