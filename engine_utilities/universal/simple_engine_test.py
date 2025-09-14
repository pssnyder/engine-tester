#!/usr/bin/env python3
"""
Simple Engine Test - No external dependencies needed
Tests the v7p3r engine with basic positions
"""

import subprocess
import sys
import time
from pathlib import Path

def test_single_position():
    """Test a single position with the current v7p3r engine"""
    
    # Test position (Scholar's mate setup)
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
    
    print("=" * 60)
    print("V7P3R ENGINE TEST")
    print("=" * 60)
    print(f"Position: {fen}")
    print("Time limit: 3 seconds")
    print("=" * 60)
    
    # Engine command
    engine_path = Path("../V7P3R Chess Engine/v7p3r-chess-engine")
    command = ["python", "src/v7p3r_uci.py"]
    
    try:
        # Start engine
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=engine_path
        )
        
        print("Engine started...")
        
        # Send UCI and wait for response
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Read initial response
        uci_ready = False
        start_time = time.time()
        
        while not uci_ready and time.time() - start_time < 5:
            line = process.stdout.readline().strip()
            print(f"Engine: {line}")
            if "uciok" in line:
                uci_ready = True
        
        if not uci_ready:
            print("ERROR: Engine did not respond to UCI command")
            process.terminate()
            return
        
        print("\nSending position...")
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        print("Starting search...")
        process.stdin.write("go movetime 3000\n")
        process.stdin.flush()
        
        # Collect search results
        best_move = ""
        best_eval = 0
        depth = 0
        nodes = 0
        
        search_start = time.time()
        
        while time.time() - search_start < 5:  # Give extra time for response
            line = process.stdout.readline().strip()
            
            if line:
                print(f"Engine: {line}")
                
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
                                    best_eval = int(parts[i+2])
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
        
        # Results
        print("\n" + "=" * 60)
        print("SEARCH RESULTS")
        print("=" * 60)
        print(f"Best move: {best_move}")
        print(f"Evaluation: {best_eval:+d} centipawns")
        print(f"Search depth: {depth}")
        print(f"Nodes searched: {nodes:,}")
        print(f"Search time: {time.time() - search_start:.2f}s")
        
        # Check if this is the expected best move (Qxf7#)
        if best_move.lower() in ["qxf7", "qf7"]:
            print("\n🎉 SUCCESS: Engine found the checkmate!")
        elif best_move.startswith("q"):
            print(f"\n🤔 Engine chose queen move: {best_move}")
        else:
            print(f"\n❌ Engine missed the mate: {best_move}")
        
        # Cleanup
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        
    except Exception as e:
        print(f"ERROR: {e}")
        if 'process' in locals():
            process.terminate()

def test_confidence_system():
    """Test the confidence system with a known position"""
    
    print("\n" + "=" * 60)
    print("CONFIDENCE SYSTEM TEST")
    print("=" * 60)
    
    # Simple endgame where the engine should be confident
    fen = "8/8/8/8/8/3k4/3P4/3K4 w - - 0 1"  # King and pawn vs king
    
    print(f"Position: {fen}")
    print("Testing with confidence evaluation...")
    
    engine_path = Path("../V7P3R Chess Engine/v7p3r-chess-engine")
    command = ["python", "src/v7p3r_uci.py"]
    
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=engine_path
        )
        
        # Initialize
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Wait for uciok
        while True:
            line = process.stdout.readline().strip()
            if "uciok" in line:
                break
        
        # Enable multithreaded evaluation
        process.stdin.write("setoption name UseMultithreadedEval value true\n")
        process.stdin.flush()
        
        # Set position and search
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        process.stdin.write("go movetime 2000\n")
        process.stdin.flush()
        
        # Look for confidence information
        confidence_found = False
        search_start = time.time()
        
        while time.time() - search_start < 4:
            line = process.stdout.readline().strip()
            
            if line:
                print(f"Engine: {line}")
                
                if "confidence" in line.lower():
                    confidence_found = True
                    print("✅ Confidence system is active!")
                
                if line.startswith("bestmove"):
                    break
        
        if not confidence_found:
            print("⚠️  No confidence information detected in output")
        
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        
    except Exception as e:
        print(f"ERROR: {e}")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--confidence":
        test_confidence_system()
    else:
        test_single_position()
        test_confidence_system()
