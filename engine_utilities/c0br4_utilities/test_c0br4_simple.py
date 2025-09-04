#!/usr/bin/env python3
"""
Quick C0BR4 Engine Test
"""

import subprocess
import time

def test_c0br4_simple():
    """Test C0BR4 with a simple position"""
    engine_path = r"s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\C0BR4\C0BR4_v2.3.exe"
    
    try:
        process = subprocess.Popen(
            engine_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        print("Testing C0BR4 v2.3...")
        
        # Test basic UCI
        commands = [
            "uci",
            "isready",
            "position startpos",
            "go movetime 2000"
        ]
        
        for cmd in commands:
            print(f"Sending: {cmd}")
            if process.stdin:
                process.stdin.write(f"{cmd}\n")
                process.stdin.flush()
            time.sleep(0.5 if cmd in ["uci", "isready"] else 0.1)
        
        # Read output
        start_time = time.time()
        timeout = 5
        best_move = None
        
        while time.time() - start_time < timeout:
            if not process.stdout:
                break
                
            line = process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
                
            line = line.strip()
            print(f"Engine: {line}")
            
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) > 1:
                    best_move = parts[1]
                break
        
        process.terminate()
        print(f"Result: {best_move}")
        
        # Test with FEN position
        print("\nTesting with FEN position...")
        
        process = subprocess.Popen(
            engine_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        commands = [
            "uci",
            "isready", 
            f"position fen {fen}",
            "go movetime 2000"
        ]
        
        for cmd in commands:
            print(f"Sending: {cmd}")
            if process.stdin:
                process.stdin.write(f"{cmd}\n")
                process.stdin.flush()
            time.sleep(0.5 if cmd in ["uci", "isready"] else 0.1)
        
        # Read output
        start_time = time.time()
        timeout = 5
        best_move = None
        
        while time.time() - start_time < timeout:
            if not process.stdout:
                break
                
            line = process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
                
            line = line.strip()
            print(f"Engine: {line}")
            
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) > 1:
                    best_move = parts[1]
                break
        
        process.terminate()
        print(f"Result: {best_move}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_c0br4_simple()
