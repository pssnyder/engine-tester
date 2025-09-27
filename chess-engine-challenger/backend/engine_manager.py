"""
Engine Manager - Handle UCI communication with chess engines
"""

import subprocess
import os
import threading
import time
from typing import Dict, List, Optional, Tuple
import chess

class UCIEngine:
    """Manages communication with a single UCI engine"""
    
    def __init__(self, name: str, executable_path: str):
        self.name = name
        self.executable_path = executable_path
        self.process = None
        self.is_ready = False
        self.thinking = False
        
    def start(self) -> bool:
        """Start the engine process"""
        try:
            self.process = subprocess.Popen(
                self.executable_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=os.path.dirname(self.executable_path)
            )
            
            # Send UCI initialization
            self._send_command("uci")
            self._wait_for_response("uciok", timeout=5)
            
            self._send_command("isready")
            self._wait_for_response("readyok", timeout=5)
            
            self.is_ready = True
            return True
            
        except Exception as e:
            print(f"Failed to start engine {self.name}: {e}")
            return False
    
    def stop(self):
        """Stop the engine process"""
        if self.process:
            self._send_command("quit")
            self.process.terminate()
            self.process = None
            self.is_ready = False
    
    def get_best_move(self, fen: str, time_limit_ms: int = 1000) -> Optional[str]:
        """Get the best move from the engine"""
        if not self.is_ready:
            return None
            
        try:
            # Set position
            self._send_command(f"position fen {fen}")
            
            # Start thinking
            self._send_command(f"go movetime {time_limit_ms}")
            self.thinking = True
            
            # Wait for bestmove response
            while True:
                response = self._read_response(timeout=time_limit_ms/1000 + 2)
                if response is None:
                    break
                    
                if response.startswith("bestmove"):
                    self.thinking = False
                    parts = response.split()
                    if len(parts) >= 2:
                        return parts[1]
                    break
                    
        except Exception as e:
            print(f"Error getting move from {self.name}: {e}")
            
        self.thinking = False
        return None
    
    def _send_command(self, command: str):
        """Send command to engine"""
        if self.process and self.process.stdin:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
    
    def _read_response(self, timeout: float = 1.0) -> Optional[str]:
        """Read response from engine"""
        if not self.process or not self.process.stdout:
            return None
            
        # Simple timeout implementation
        import select
        import sys
        
        if sys.platform == 'win32':
            # Windows doesn't support select on pipes, use basic approach
            try:
                response = self.process.stdout.readline().strip()
                return response if response else None
            except:
                return None
        else:
            # Unix-like systems
            ready, _, _ = select.select([self.process.stdout], [], [], timeout)
            if ready:
                return self.process.stdout.readline().strip()
            return None
    
    def _wait_for_response(self, expected: str, timeout: float = 5.0):
        """Wait for specific response from engine"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self._read_response(0.1)
            if response and expected in response:
                return True
        return False


class EngineManager:
    """Manages multiple chess engines"""
    
    def __init__(self):
        self.engines: Dict[str, UCIEngine] = {}
        self.engine_configs = self._load_engine_configs()
        
    def _load_engine_configs(self) -> Dict[str, str]:
        """Load available engines from engines directory"""
        engines_dir = os.path.join(os.path.dirname(__file__), '..', 'engines')
        configs = {
            'Human': None,  # Special case for human players
        }
        
        # Look for V7P3R engine
        v7p3r_path = r's:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\v7p3r_engine.exe'
        if os.path.exists(v7p3r_path):
            configs['V7P3R'] = v7p3r_path
        
        # Look for other engines in engines directory
        if os.path.exists(engines_dir):
            for file in os.listdir(engines_dir):
                if file.endswith('.exe'):
                    name = os.path.splitext(file)[0]
                    configs[name] = os.path.join(engines_dir, file)
        
        return configs
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engines"""
        return list(self.engine_configs.keys())
    
    def get_engine(self, name: str) -> Optional[UCIEngine]:
        """Get or create engine instance"""
        if name == 'Human':
            return None  # Human players don't need engine instances
            
        if name not in self.engines:
            if name in self.engine_configs:
                engine = UCIEngine(name, self.engine_configs[name])
                if engine.start():
                    self.engines[name] = engine
                else:
                    return None
            else:
                return None
                
        return self.engines.get(name)
    
    def shutdown_all(self):
        """Shutdown all engine processes"""
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()
