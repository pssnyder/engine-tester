#!/usr/bin/env python3
"""
Diagnostic script to test different UCI communication methods with .bat engines
"""

import subprocess
import time
import sys
from pathlib import Path

def test_method_1_direct_bat(bat_path):
    """Test 1: Direct .bat execution"""
    print("\n" + "="*70)
    print("TEST 1: Direct .bat execution")
    print("="*70)
    
    try:
        proc = subprocess.Popen(
            [str(bat_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        print(f"✓ Process started with PID: {proc.pid}")
        
        # Send UCI command
        print("Sending: uci")
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        
        # Read response
        print("Reading response...")
        start = time.time()
        timeout = 5.0
        found_uciok = False
        
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if line:
                print(f"  < {line.strip()}")
                if "uciok" in line:
                    found_uciok = True
                    break
            else:
                time.sleep(0.1)
        
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.terminate()
        
        if found_uciok:
            print("✅ SUCCESS: Engine responded with uciok")
            return True
        else:
            print("❌ FAILED: No uciok received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_2_cmd_wrapper(bat_path):
    """Test 2: cmd.exe /c wrapper"""
    print("\n" + "="*70)
    print("TEST 2: cmd.exe /c wrapper")
    print("="*70)
    
    try:
        proc = subprocess.Popen(
            ['cmd.exe', '/c', str(bat_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        print(f"✓ Process started with PID: {proc.pid}")
        
        # Send UCI command
        print("Sending: uci")
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        
        # Read response
        print("Reading response...")
        start = time.time()
        timeout = 5.0
        found_uciok = False
        
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if line:
                print(f"  < {line.strip()}")
                if "uciok" in line:
                    found_uciok = True
                    break
            else:
                time.sleep(0.1)
        
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.terminate()
        
        if found_uciok:
            print("✅ SUCCESS: Engine responded with uciok")
            return True
        else:
            print("❌ FAILED: No uciok received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_3_cmd_wrapper_with_cwd(bat_path):
    """Test 3: cmd.exe /c wrapper with working directory"""
    print("\n" + "="*70)
    print("TEST 3: cmd.exe /c wrapper with cwd")
    print("="*70)
    
    try:
        bat_dir = Path(bat_path).parent
        print(f"Working directory: {bat_dir}")
        
        proc = subprocess.Popen(
            ['cmd.exe', '/c', str(bat_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(bat_dir)
        )
        
        print(f"✓ Process started with PID: {proc.pid}")
        
        # Send UCI command
        print("Sending: uci")
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        
        # Read response
        print("Reading response...")
        start = time.time()
        timeout = 5.0
        found_uciok = False
        
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if line:
                print(f"  < {line.strip()}")
                if "uciok" in line:
                    found_uciok = True
                    break
            else:
                time.sleep(0.1)
        
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.terminate()
        
        if found_uciok:
            print("✅ SUCCESS: Engine responded with uciok")
            return True
        else:
            print("❌ FAILED: No uciok received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_4_chess_engine_lib(bat_path):
    """Test 4: Using chess.engine library"""
    print("\n" + "="*70)
    print("TEST 4: chess.engine library with cmd wrapper")
    print("="*70)
    
    try:
        import chess.engine
        
        cmd = ['cmd.exe', '/c', str(bat_path)]
        print(f"Command: {cmd}")
        
        with chess.engine.SimpleEngine.popen_uci(cmd) as engine:
            print(f"✓ Engine initialized")
            
            # Get engine info
            print(f"Engine name: {engine.id.get('name', 'Unknown')}")
            print(f"Engine author: {engine.id.get('author', 'Unknown')}")
            
            # Test a simple position
            import chess
            board = chess.Board()
            result = engine.play(board, chess.engine.Limit(time=1.0))
            print(f"Best move from starting position: {result.move}")
            
            print("✅ SUCCESS: chess.engine library works!")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_5_unbuffered(bat_path):
    """Test 5: Unbuffered I/O"""
    print("\n" + "="*70)
    print("TEST 5: Unbuffered I/O (bufsize=0, universal_newlines=False)")
    print("="*70)
    
    try:
        bat_dir = Path(bat_path).parent
        
        proc = subprocess.Popen(
            ['cmd.exe', '/c', str(bat_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            cwd=str(bat_dir)
        )
        
        print(f"✓ Process started with PID: {proc.pid}")
        
        # Send UCI command (as bytes)
        print("Sending: uci")
        proc.stdin.write(b"uci\n")
        proc.stdin.flush()
        
        # Read response
        print("Reading response...")
        start = time.time()
        timeout = 5.0
        found_uciok = False
        
        while time.time() - start < timeout:
            try:
                line = proc.stdout.readline().decode('utf-8', errors='ignore')
                if line:
                    print(f"  < {line.strip()}")
                    if "uciok" in line:
                        found_uciok = True
                        break
                else:
                    time.sleep(0.1)
            except:
                time.sleep(0.1)
        
        proc.stdin.write(b"quit\n")
        proc.stdin.flush()
        proc.terminate()
        
        if found_uciok:
            print("✅ SUCCESS: Engine responded with uciok")
            return True
        else:
            print("❌ FAILED: No uciok received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("BAT ENGINE UCI COMMUNICATION DIAGNOSTIC")
    print("="*70)
    
    # Test both engines
    engines = {
        "v18.3": r"E:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\lichess\engines\V7P3R_v18.3_20251229\V7P3R_v18.3.bat",
        "v18.4": r"E:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\development\V7P3R_v18.4_20260415\V7P3R_v18.4.bat"
    }
    
    for version, bat_path in engines.items():
        print(f"\n{'#'*70}")
        print(f"# Testing {version}: {bat_path}")
        print(f"{'#'*70}")
        
        if not Path(bat_path).exists():
            print(f"❌ Engine not found: {bat_path}")
            continue
        
        # Run all tests
        results = {
            "Direct .bat": test_method_1_direct_bat(bat_path),
            "cmd /c": test_method_2_cmd_wrapper(bat_path),
            "cmd /c + cwd": test_method_3_cmd_wrapper_with_cwd(bat_path),
            "chess.engine": test_method_4_chess_engine_lib(bat_path),
            "Unbuffered": test_method_5_unbuffered(bat_path)
        }
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SUMMARY FOR {version}")
        print(f"{'='*70}")
        for method, success in results.items():
            status = "✅ WORKS" if success else "❌ FAILED"
            print(f"  {method:20s} {status}")


if __name__ == "__main__":
    main()
