#!/usr/bin/env python3
"""
Standalone demo of .bat engine support for Universal Puzzle Analyzer
This demo focuses on the engine launching capability without requiring the full database setup
"""

import subprocess
import time
import os
from typing import List, Dict, Optional, Tuple

class SimpleEngineAnalyzer:
    """Simplified analyzer that demonstrates .bat engine support"""
    
    def __init__(self, engine_path: str):
        self.engine_path = engine_path
        self.engine_type = self._detect_engine_type(engine_path)
        self.engine_command = self._build_engine_command(engine_path)
        self.engine_info = self._get_engine_info()
        self.engine_name = self.engine_info.get('name', os.path.basename(engine_path))
        
    def _detect_engine_type(self, engine_path: str) -> str:
        """Detect whether engine is .exe or .bat file"""
        path_lower = engine_path.lower()
        if path_lower.endswith('.bat'):
            return 'bat'
        elif path_lower.endswith('.exe'):
            return 'exe'
        else:
            return 'exe'
    
    def _build_engine_command(self, engine_path: str) -> List[str]:
        """Build the command to launch the engine based on file type"""
        if self.engine_type == 'bat':
            return ['cmd.exe', '/c', engine_path]
        else:
            return [engine_path]
    
    def _get_engine_info(self) -> Dict[str, str]:
        """Get engine information via UCI protocol"""
        try:
            process = subprocess.Popen(
                self.engine_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=os.path.dirname(self.engine_path) if self.engine_type == 'bat' else None
            )
            
            engine_info = {}
            
            # Send UCI command
            if process.stdin:
                process.stdin.write("uci\n")
                process.stdin.flush()
            
            # Read UCI response
            start_time = time.time()
            while time.time() - start_time < 5:
                if not process.stdout:
                    break
                    
                if process.poll() is not None:
                    break
                
                try:
                    line = process.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    line = line.strip()
                    
                    if line.startswith("id name"):
                        engine_info['name'] = line[8:].strip()
                    elif line.startswith("id author"):
                        engine_info['author'] = line[9:].strip()
                    elif line == "uciok":
                        break
                        
                except:
                    break
            
            # Clean up
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                    process.wait(timeout=1)
                except:
                    pass
            
            return engine_info
            
        except Exception as e:
            print(f"Warning: Could not get engine info via UCI: {e}")
            return {'name': os.path.basename(self.engine_path)}
    
    def get_engine_move(self, fen: str, time_seconds: float = 5.0) -> Optional[str]:
        """Get the engine's best move for a position"""
        try:
            process = subprocess.Popen(
                self.engine_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=os.path.dirname(self.engine_path) if self.engine_type == 'bat' else None
            )
            
            # UCI commands
            commands = [
                "uci",
                "isready",
                f"position fen {fen}",
                f"go movetime {int(time_seconds * 1000)}"
            ]
            
            for cmd in commands:
                if process.stdin:
                    process.stdin.write(f"{cmd}\n")
                    process.stdin.flush()
                if cmd == "uci" or cmd == "isready":
                    time.sleep(0.2)
            
            # Read output until bestmove
            best_move = None
            start_time = time.time()
            timeout = time_seconds + 3
            
            while time.time() - start_time < timeout:
                if not process.stdout:
                    break
                
                if process.poll() is not None:
                    break
                    
                try:
                    line = process.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                        
                    line = line.strip()
                    
                    if line.startswith("bestmove"):
                        parts = line.split()
                        if len(parts) > 1:
                            best_move = parts[1]
                        break
                except:
                    break
            
            # Clean up
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
            
            return best_move
            
        except Exception as e:
            print(f"Error getting engine move: {e}")
            return None


def demo_engine_types():
    """Demonstrate .bat and .exe engine support"""
    
    print("🎮 UNIVERSAL PUZZLE ANALYZER - ENGINE TYPE SUPPORT DEMO")
    print("=" * 65)
    
    # Test engines
    engines_to_test = [
        {
            "name": "V7P3R v14.2 (.bat)",
            "path": r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\V7P3R\V7P3R_v14.2\V7P3R_v14.2.bat",
            "type": "bat"
        },
        {
            "name": "Stockfish (.exe)",
            "path": r"S:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\engines\Stockfish\stockfish-windows-x86-64-avx2.exe",
            "type": "exe"
        }
    ]
    
    # Test positions
    test_positions = [
        {
            "name": "Starting Position",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        },
        {
            "name": "After 1.e4",
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        }
    ]
    
    for engine_config in engines_to_test:
        print(f"\n🔧 TESTING: {engine_config['name']}")
        print(f"   Path: {engine_config['path']}")
        print(f"   Exists: {os.path.exists(engine_config['path'])}")
        
        if not os.path.exists(engine_config['path']):
            print("   ⚠️  Engine not found, skipping...")
            continue
        
        try:
            # Initialize analyzer
            analyzer = SimpleEngineAnalyzer(engine_config['path'])
            
            print(f"   ✅ Engine type detected: {analyzer.engine_type}")
            print(f"   ✅ Engine command: {analyzer.engine_command}")
            print(f"   ✅ Engine name: {analyzer.engine_name}")
            print(f"   ✅ Engine author: {analyzer.engine_info.get('author', 'Unknown')}")
            
            # Test moves on different positions
            for position in test_positions:
                print(f"\n   🎯 Testing {position['name']}:")
                print(f"      FEN: {position['fen']}")
                
                move = analyzer.get_engine_move(position['fen'], 3.0)
                if move:
                    print(f"      ✅ Suggested move: {move}")
                else:
                    print(f"      ❌ Failed to get move")
                    
        except Exception as e:
            print(f"   ❌ Error testing engine: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 65)
    print("🎉 DEMO COMPLETE!")
    print("\n💡 KEY IMPROVEMENTS:")
    print("   • Universal Puzzle Analyzer now supports .bat files")
    print("   • Automatically detects engine type (.bat vs .exe)")
    print("   • Proper working directory handling for .bat engines")
    print("   • Backward compatibility with existing .exe engines")
    print("   • Enables cloud deployment of Python-based engines")
    print("\n📋 USAGE:")
    print("   # With .bat engine:")
    print("   python -m engine_utilities.universal_puzzle_analyzer \\")
    print("     --engine engines\\V7P3R\\V7P3R_v14.2\\V7P3R_v14.2.bat")
    print("   ")
    print("   # With .exe engine (still works):")
    print("   python -m engine_utilities.universal_puzzle_analyzer \\")
    print("     --engine engines\\Stockfish\\stockfish.exe")


if __name__ == "__main__":
    demo_engine_types()