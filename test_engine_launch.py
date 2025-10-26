#!/usr/bin/env python3
"""
Direct test of engine launching with new .bat support
"""

import subprocess
import os
import time

def test_bat_engine():
    """Test launching a .bat engine directly"""
    bat_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R\V7P3R_v14.2\V7P3R_v14.2.bat"
    
    print(f"Testing .bat engine: {bat_path}")
    print(f"Engine exists: {os.path.exists(bat_path)}")
    
    if not os.path.exists(bat_path):
        print("❌ Engine not found")
        return False
        
    try:
        # Test with cmd.exe approach
        command = ['cmd.exe', '/c', bat_path]
        print(f"Command: {command}")
        print(f"Working dir: {os.path.dirname(bat_path)}")
        
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=os.path.dirname(bat_path)
        )
        
        # Send UCI command
        print("Sending UCI command...")
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Read response for a few seconds
        start_time = time.time()
        responses = []
        while time.time() - start_time < 5:
            try:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    responses.append(line)
                    print(f"Response: {line}")
                    if line == "uciok":
                        break
                else:
                    time.sleep(0.1)
            except:
                break
        
        # Send quit
        try:
            process.stdin.write("quit\n")
            process.stdin.flush()
        except:
            pass
        
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=2)
        except:
            try:
                process.kill()
            except:
                pass
        
        if any("id name" in r for r in responses):
            print("✅ .bat engine responded correctly!")
            return True
        else:
            print("❌ .bat engine did not respond as expected")
            print(f"All responses: {responses}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing .bat engine: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exe_engine():
    """Test an .exe engine for comparison"""
    exe_path = r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe"
    
    print(f"\nTesting .exe engine: {exe_path}")
    print(f"Engine exists: {os.path.exists(exe_path)}")
    
    if not os.path.exists(exe_path):
        print("⚠️  Stockfish not found, skipping .exe test")
        return True
        
    try:
        command = [exe_path]
        print(f"Command: {command}")
        
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send UCI command
        print("Sending UCI command...")
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Read response
        start_time = time.time()
        responses = []
        while time.time() - start_time < 3:
            try:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    responses.append(line)
                    print(f"Response: {line}")
                    if line == "uciok":
                        break
                else:
                    time.sleep(0.1)
            except:
                break
        
        # Send quit
        try:
            process.stdin.write("quit\n")
            process.stdin.flush()
        except:
            pass
        
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=2)
        except:
            try:
                process.kill()
            except:
                pass
        
        if any("id name" in r for r in responses):
            print("✅ .exe engine responded correctly!")
            return True
        else:
            print("❌ .exe engine did not respond as expected")
            return False
            
    except Exception as e:
        print(f"❌ Error testing .exe engine: {e}")
        return False

if __name__ == "__main__":
    print("Engine Launch Test")
    print("=" * 40)
    
    bat_success = test_bat_engine()
    exe_success = test_exe_engine()
    
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f".bat engine test: {'✅ PASS' if bat_success else '❌ FAIL'}")
    print(f".exe engine test: {'✅ PASS' if exe_success else '❌ FAIL'}")
    
    if bat_success:
        print("\n🎉 .bat engine support is working!")
    else:
        print("\n❌ .bat engine support needs debugging")