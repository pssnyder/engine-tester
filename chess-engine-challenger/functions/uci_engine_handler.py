"""
UCI Engine Handler for Chess Engine Challenger
Optimized for V7P3R v12.2, C0BR4 v2.9, SlowMate v3.1, and Random_Opponent
"""

import subprocess
import threading
import time
import os
import logging
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import chess
import tempfile
import shutil

logger = logging.getLogger(__name__)

class EngineStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting" 
    READY = "ready"
    THINKING = "thinking"
    ERROR = "error"

@dataclass
class EngineConfig:
    """Configuration for specific engines"""
    name: str
    executable_name: str
    local_path: str  # Local development path
    cloud_path: str  # Cloud storage path
    startup_timeout: int = 10
    move_timeout: int = 30
    supports_eval: bool = True
    max_memory_mb: int = 256

class UCIEngine:
    """Manages a single UCI engine with local/cloud flexibility"""
    
    def __init__(self, config: EngineConfig, is_local: bool = True):
        self.config = config
        self.is_local = is_local
        self.process: Optional[subprocess.Popen] = None
        self.status = EngineStatus.STOPPED
        self.last_eval: Optional[float] = None
        self.executable_path: Optional[str] = None
        
    def _get_executable_path(self) -> str:
        """Get the correct executable path for local or cloud deployment"""
        if self.is_local:
            # Local development - use direct paths to your engines
            engine_paths = {
                'V7P3R': r's:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\v7p3r_engine.exe',
                'C0BR4': r's:\Maker Stuff\Programming\Chess Engines\C0BR4 Chess Engine\cobra-chess-engine\cobra_engine.exe',
                'SlowMate': r's:\Maker Stuff\Programming\Chess Engines\SlowMate\slowmate_engine.exe',
                'Random_Opponent': r's:\Maker Stuff\Programming\Chess Engines\Random_Opponent\random_opponent.exe'
            }
            
            if self.config.name in engine_paths:
                return engine_paths[self.config.name]
            else:
                # Fallback to relative path
                return os.path.join('..', 'engines', self.config.executable_name)
        else:
            # Cloud deployment - download from Cloud Storage
            return self._download_engine_from_cloud()
    
    def _download_engine_from_cloud(self) -> str:
        """Download engine from Firebase Cloud Storage for cloud deployment"""
        try:
            from firebase_admin import storage
            
            bucket = storage.bucket()
            blob = bucket.blob(f'engines/{self.config.executable_name}')
            
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, self.config.executable_name)
            
            # Download
            blob.download_to_filename(temp_path)
            
            # Make executable (Unix systems)
            if os.name != 'nt':
                os.chmod(temp_path, 0o755)
            
            logger.info(f"Downloaded {self.config.name} to {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to download {self.config.name}: {e}")
            raise
    
    def start(self) -> bool:
        """Start the engine process"""
        try:
            self.status = EngineStatus.STARTING
            self.executable_path = self._get_executable_path()
            
            if not os.path.exists(self.executable_path):
                logger.error(f"Engine executable not found: {self.executable_path}")
                self.status = EngineStatus.ERROR
                return False
            
            # Start process
            self.process = subprocess.Popen(
                [self.executable_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(self.executable_path)
            )
            
            # UCI initialization
            self._send_command("uci")
            if not self._wait_for_response("uciok", self.config.startup_timeout):
                logger.error(f"Engine {self.config.name} failed UCI initialization")
                self._cleanup()
                return False
            
            self._send_command("isready")
            if not self._wait_for_response("readyok", 5):
                logger.error(f"Engine {self.config.name} not ready")
                self._cleanup()
                return False
            
            self.status = EngineStatus.READY
            logger.info(f"Engine {self.config.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {self.config.name}: {e}")
            self.status = EngineStatus.ERROR
            self._cleanup()
            return False
    
    def stop(self):
        """Stop the engine process"""
        if self.process:
            try:
                self._send_command("quit")
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                if self.process:
                    self.process.kill()
            finally:
                self._cleanup()
        
        self.status = EngineStatus.STOPPED
    
    def get_best_move(self, fen: str, time_limit_ms: int = 1000) -> Optional[Tuple[str, Optional[float], float]]:
        """Get best move with timing and evaluation"""
        if self.status != EngineStatus.READY:
            return None
        
        try:
            self.status = EngineStatus.THINKING
            start_time = time.time()
            
            # Set position
            self._send_command(f"position fen {fen}")
            
            # Start thinking
            self._send_command(f"go movetime {time_limit_ms}")
            
            # Wait for response
            move, evaluation = self._wait_for_best_move(time_limit_ms / 1000 + 5)
            move_time = time.time() - start_time
            
            self.status = EngineStatus.READY
            
            if move:
                return (move, evaluation, move_time)
            
        except Exception as e:
            logger.error(f"Error getting move from {self.config.name}: {e}")
            self.status = EngineStatus.ERROR
        
        return None
    
    def _send_command(self, command: str):
        """Send command to engine"""
        if self.process and self.process.stdin:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
    
    def _wait_for_response(self, expected: str, timeout: float = 5.0) -> bool:
        """Wait for expected response"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.process and self.process.stdout:
                try:
                    line = self.process.stdout.readline().strip()
                    if expected.lower() in line.lower():
                        return True
                except:
                    break
            time.sleep(0.01)
        
        return False
    
    def _wait_for_best_move(self, timeout: float = 30.0) -> Tuple[Optional[str], Optional[float]]:
        """Wait for bestmove response"""
        start_time = time.time()
        evaluation = None
        
        while time.time() - start_time < timeout:
            if self.process and self.process.stdout:
                try:
                    line = self.process.stdout.readline().strip()
                    
                    # Extract evaluation
                    if "info" in line and "score cp" in line:
                        try:
                            parts = line.split()
                            cp_index = parts.index("cp")
                            if cp_index + 1 < len(parts):
                                evaluation = float(parts[cp_index + 1]) / 100.0
                        except:
                            pass
                    
                    # Check for bestmove
                    if line.startswith("bestmove"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return (parts[1], evaluation)
                        break
                        
                except:
                    break
            
            time.sleep(0.01)
        
        return (None, evaluation)
    
    def _cleanup(self):
        """Clean up resources"""
        if self.process:
            self.process = None
        
        # Clean up temporary files for cloud deployment
        if not self.is_local and self.executable_path:
            try:
                temp_dir = os.path.dirname(self.executable_path)
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

class UCIEngineManager:
    """Manages multiple UCI engines with local/cloud deployment support"""
    
    def __init__(self, is_local: bool = True):
        self.is_local = is_local
        self.engines: Dict[str, UCIEngine] = {}
        self.engine_configs = self._create_engine_configs()
    
    def _create_engine_configs(self) -> Dict[str, EngineConfig]:
        """Create configurations for your specific engines"""
        return {
            'V7P3R': EngineConfig(
                name='V7P3R',
                executable_name='v7p3r_engine.exe',
                local_path=r's:\Maker Stuff\Programming\Chess Engines\V7P3R Chess Engine\v7p3r-chess-engine\v7p3r_engine.exe',
                cloud_path='engines/v7p3r_engine.exe',
                startup_timeout=12,  # V7P3R might need more time due to bitboard initialization
                move_timeout=30,
                supports_eval=True,
                max_memory_mb=512    # V7P3R uses more memory for bitboards
            ),
            'C0BR4': EngineConfig(
                name='C0BR4',
                executable_name='cobra_engine.exe',
                local_path=r's:\Maker Stuff\Programming\Chess Engines\C0BR4 Chess Engine\cobra-chess-engine\cobra_engine.exe',
                cloud_path='engines/cobra_engine.exe',
                startup_timeout=8,
                move_timeout=25,
                supports_eval=True,
                max_memory_mb=256
            ),
            'SlowMate': EngineConfig(
                name='SlowMate',
                executable_name='slowmate_engine.exe',
                local_path=r's:\Maker Stuff\Programming\Chess Engines\SlowMate\slowmate_engine.exe',
                cloud_path='engines/slowmate_engine.exe',
                startup_timeout=5,
                move_timeout=20,
                supports_eval=False,  # Might not support evaluation output
                max_memory_mb=128
            ),
            'Random_Opponent': EngineConfig(
                name='Random_Opponent',
                executable_name='random_opponent.exe',
                local_path=r's:\Maker Stuff\Programming\Chess Engines\Random_Opponent\random_opponent.exe',
                cloud_path='engines/random_opponent.exe',
                startup_timeout=3,   # Should be very fast
                move_timeout=5,      # Random moves are instant
                supports_eval=False, # Random engine won't have evaluations
                max_memory_mb=64
            )
        }
    
    def get_available_engines(self) -> list:
        """Get list of available engines plus Human"""
        return ['Human'] + list(self.engine_configs.keys())
    
    def get_engine_move(self, engine_name: str, fen: str, time_limit_ms: int = 1000) -> Optional[Tuple[str, Optional[float], float]]:
        """Get move from specified engine"""
        if engine_name == 'Human':
            return None  # Human moves handled by frontend
        
        if engine_name not in self.engine_configs:
            logger.error(f"Unknown engine: {engine_name}")
            return None
        
        # Get or create engine
        if engine_name not in self.engines:
            config = self.engine_configs[engine_name]
            engine = UCIEngine(config, self.is_local)
            
            if not engine.start():
                logger.error(f"Failed to start {engine_name}")
                return None
                
            self.engines[engine_name] = engine
        
        # Get move
        return self.engines[engine_name].get_best_move(fen, time_limit_ms)
    
    def shutdown_all(self):
        """Shutdown all engines"""
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()
