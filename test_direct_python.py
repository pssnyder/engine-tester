#!/usr/bin/env python3
"""
Test V7P3R engines by calling the Python UCI script directly
"""

import subprocess
import time
from pathlib import Path

def test_engine_direct_python(engine_dir, version_name):
    """Test engine by calling Python directly on the UCI script"""
    print(f"\n{'='*70}")
    print(f"Testing {version_name} via direct Python call")
    print(f"{'='*70}")
    
    uci_script = Path(engine_dir) / "src" / "v7p3r_uci.py"
    
    if not uci_script.exists():
        print(f"❌ UCI script not found: {uci_script}")
        return False
    
    print(f"UCI Script: {uci_script}")
    print(f"Working dir: {engine_dir}")
    
    try:
        # Call Python directly on the UCI script
        proc = subprocess.Popen(
            ["python", str(uci_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(engine_dir)
        )
        
        print(f"✓ Process started with PID: {proc.pid}")
        
        # Send UCI command
        print("\nSending: uci")
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        
        # Read response
        print("Engine response:")
        start = time.time()
        timeout = 5.0
        found_uciok = False
        engine_name = None
        
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if line:
                line = line.strip()
                print(f"  < {line}")
                if "uciok" in line:
                    found_uciok = True
                    break
                if "id name" in line:
                    engine_name = line.replace("id name", "").strip()
            else:
                time.sleep(0.1)
        
        if found_uciok:
            print(f"\n✅ SUCCESS!")
            if engine_name:
                print(f"   Engine: {engine_name}")
            
            # Test a move from starting position
            print("\n🎯 Testing move generation from starting position...")
            proc.stdin.write("position startpos\n")
            proc.stdin.flush()
            proc.stdin.write("go movetime 1000\n")
            proc.stdin.flush()
            
            best_move = None
            start = time.time()
            while time.time() - start < 5.0:
                line = proc.stdout.readline()
                if line:
                    line = line.strip()
                    if line.startswith("info"):
                        print(f"     {line[:80]}...")
                    elif "bestmove" in line:
                        best_move = line.split()[1] if len(line.split()) > 1 else None
                        print(f"\n✅ Best move: {best_move}")
                        break
            
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=2)
            
            return True
        else:
            print(f"\n❌ FAILED: No uciok received")
            proc.terminate()
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("V7P3R ENGINE DIRECT PYTHON TEST")
    print("="*70)
    
    engines = {
        "v18.3": r"E:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\lichess\engines\V7P3R_v18.3_20251229",
        "v18.4": r"E:\Programming Stuff\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\development\V7P3R_v18.4_20260415"
    }
    
    results = {}
    for version, engine_dir in engines.items():
        results[version] = test_engine_direct_python(engine_dir, version)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for version, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"  {version:10s} {status}")
    
    if all(results.values()):
        print(f"\n💡 Solution: Use 'python <path>/src/v7p3r_uci.py' instead of .bat files")
    

if __name__ == "__main__":
    main()
