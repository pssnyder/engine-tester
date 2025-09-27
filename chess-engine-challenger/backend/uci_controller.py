"""
Secure UCI Controller for Chess Engine Challenger
Handles communication with any UCI-compliant chess engine with security hardening
"""

import subprocess
import threading
import time
import os
import signal
import chess
import chess.engine
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EngineStatus(Enum):
    """Engine status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting" 
    READY = "ready"
    THINKING = "thinking"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class EngineConfig:
    """Configuration for a chess engine"""
    name: str
    executable_path: str
    startup_timeout: int = 10  # seconds
    move_timeout: int = 30     # seconds
    supports_eval: bool = True
    max_memory_mb: int = 256   # Memory limit
    
class SecureUCIEngine:
    """
    Secure UCI engine wrapper with hardened process management
    """
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = EngineStatus.STOPPED
        self.last_eval: Optional[float] = None
        self.last_move_time: float = 0.0
        self._lock = threading.Lock()
        self._output_buffer: List[str] = []
        
        # Security: Validate executable path
        if not self._validate_executable_path(config.executable_path):
            raise ValueError(f"Invalid executable path: {config.executable_path}")
    
    def _validate_executable_path(self, path: str) -> bool:
        """Validate that the executable path is secure and exists"""
        # Security: Prevent path traversal attacks
        if '..' in path or '~' in path:
            logger.error(f"Path traversal attempt detected: {path}")
            return False
        
        # Security: Must be in engines directory
        engines_dir = os.path.join(os.path.dirname(__file__), '..', 'engines')
        engines_dir = os.path.abspath(engines_dir)
        full_path = os.path.abspath(path)
        
        if not full_path.startswith(engines_dir):
            logger.error(f"Executable must be in engines directory: {path}")
            return False
        
        # Check if file exists and is executable
        if not os.path.isfile(full_path):
            logger.error(f"Executable not found: {path}")
            return False
        
        return True
    
    def start(self) -> bool:
        """Start the engine process with security hardening"""
        with self._lock:
            if self.status != EngineStatus.STOPPED:
                return False
            
            try:
                self.status = EngineStatus.STARTING
                
                # Security: Use absolute path and prevent shell injection
                full_path = os.path.abspath(self.config.executable_path)
                
                # Start process with security restrictions
                self.process = subprocess.Popen(
                    [full_path],  # No shell=True to prevent injection
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(full_path),  # Set working directory
                    # Security: Process limits (platform dependent)
                    # Note: Resource limits would be added here for production
                )
                
                # Initialize UCI communication
                if self._send_command_safe("uci", timeout=self.config.startup_timeout):
                    if self._wait_for_response("uciok", timeout=self.config.startup_timeout):
                        self._send_command_safe("isready")
                        if self._wait_for_response("readyok", timeout=5):
                            self.status = EngineStatus.READY
                            logger.info(f"Engine {self.config.name} started successfully")
                            return True
                
                # If we get here, startup failed
                self._cleanup_process()
                self.status = EngineStatus.ERROR
                return False
                
            except Exception as e:
                logger.error(f"Failed to start engine {self.config.name}: {e}")
                self._cleanup_process()
                self.status = EngineStatus.ERROR
                return False
    
    def stop(self):
        """Stop the engine process"""
        with self._lock:
            if self.process:
                try:
                    self._send_command_safe("quit", timeout=2)
                    self.process.terminate()
                    
                    # Give process time to terminate gracefully
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Engine {self.config.name} did not terminate gracefully, killing")
                        self.process.kill()
                        self.process.wait(timeout=1)
                        
                except Exception as e:
                    logger.error(f"Error stopping engine {self.config.name}: {e}")
                finally:
                    self._cleanup_process()
            
            self.status = EngineStatus.STOPPED
    
    def get_best_move(self, fen: str, time_limit_ms: int = 1000) -> Optional[Tuple[str, float, float]]:
        """
        Get best move from engine with timing and evaluation
        Returns: (move, eval_score, time_taken) or None if failed
        """
        if not self._validate_fen(fen):
            logger.error(f"Invalid FEN provided to {self.config.name}: {fen}")
            return None
        
        with self._lock:
            if self.status != EngineStatus.READY:
                return None
            
            try:
                self.status = EngineStatus.THINKING
                start_time = time.time()
                
                # Set position
                if not self._send_command_safe(f"position fen {fen}"):
                    return None
                
                # Start thinking with time limit
                if not self._send_command_safe(f"go movetime {time_limit_ms}"):
                    return None
                
                # Wait for best move response
                response = self._wait_for_best_move(timeout=time_limit_ms/1000 + 5)
                move_time = time.time() - start_time
                self.last_move_time = move_time
                
                self.status = EngineStatus.READY
                
                if response:
                    move, eval_score = response
                    self.last_eval = eval_score
                    return (move, eval_score, move_time)
                
                return None
                
            except Exception as e:
                logger.error(f"Error getting move from {self.config.name}: {e}")
                self.status = EngineStatus.ERROR
                return None
    
    def _validate_fen(self, fen: str) -> bool:
        """Validate FEN string to prevent injection attacks"""
        try:
            # Security: Use chess library to validate FEN
            chess.Board(fen)
            
            # Additional security: FEN should only contain valid characters
            valid_chars = set('rnbqkpRNBQKP12345678/- KQkqabcdefgh0123456789')
            if not all(c in valid_chars for c in fen):
                return False
                
            return True
        except:
            return False
    
    def _send_command_safe(self, command: str, timeout: float = 5.0) -> bool:
        """Send command to engine with input validation"""
        # Security: Validate UCI commands to prevent injection
        if not self._validate_uci_command(command):
            logger.error(f"Invalid UCI command: {command}")
            return False
        
        try:
            if self.process and self.process.stdin:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                return True
        except Exception as e:
            logger.error(f"Error sending command to {self.config.name}: {e}")
            
        return False
    
    def _validate_uci_command(self, command: str) -> bool:
        """Validate that command is a safe UCI command"""
        # Security: Whitelist of allowed UCI commands
        allowed_commands = [
            r'^uci$',
            r'^isready$', 
            r'^quit$',
            r'^position fen [a-zA-Z0-9/\-\s]+$',
            r'^position startpos(?: moves [a-h][1-8][a-h][1-8][qrbn]?)*$',
            r'^go movetime \d+$',
            r'^go depth \d+$',
            r'^go infinite$',
            r'^stop$',
            r'^setoption name \w+ value \w+$'
        ]
        
        return any(re.match(pattern, command, re.IGNORECASE) for pattern in allowed_commands)
    
    def _wait_for_response(self, expected: str, timeout: float = 5.0) -> bool:
        """Wait for expected response from engine"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.process and self.process.stdout:
                try:
                    # Non-blocking read with timeout
                    import select
                    import sys
                    
                    if sys.platform == 'win32':
                        # Windows: simplified approach
                        try:
                            line = self.process.stdout.readline().strip()
                            if expected.lower() in line.lower():
                                return True
                        except:
                            pass
                    else:
                        # Unix: use select for timeout
                        ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
                        if ready:
                            line = self.process.stdout.readline().strip()
                            if expected.lower() in line.lower():
                                return True
                        
                except Exception as e:
                    logger.error(f"Error reading from {self.config.name}: {e}")
                    break
            
            time.sleep(0.01)  # Small delay to prevent busy waiting
        
        return False
    
    def _wait_for_best_move(self, timeout: float = 30.0) -> Optional[Tuple[str, Optional[float]]]:
        """Wait for bestmove response and extract evaluation if available"""
        start_time = time.time()
        eval_score = None
        
        while time.time() - start_time < timeout:
            if self.process and self.process.stdout:
                try:
                    line = self.process.stdout.readline().strip()
                    
                    # Extract evaluation from info lines
                    if line.startswith("info") and "score cp" in line:
                        try:
                            # Extract centipawn score
                            cp_match = re.search(r'score cp (-?\d+)', line)
                            if cp_match:
                                eval_score = float(cp_match.group(1)) / 100.0
                        except:
                            pass
                    
                    # Check for bestmove
                    if line.startswith("bestmove"):
                        parts = line.split()
                        if len(parts) >= 2:
                            move = parts[1]
                            # Validate move format
                            if self._validate_move_format(move):
                                return (move, eval_score)
                        break
                        
                except Exception as e:
                    logger.error(f"Error reading bestmove from {self.config.name}: {e}")
                    break
            
            time.sleep(0.01)
        
        return None
    
    def _validate_move_format(self, move: str) -> bool:
        """Validate chess move format"""
        # Standard algebraic notation: e2e4, e7e8q, etc.
        pattern = r'^[a-h][1-8][a-h][1-8][qrbn]?$'
        return bool(re.match(pattern, move, re.IGNORECASE))
    
    def _cleanup_process(self):
        """Clean up process resources"""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
            except:
                pass
            self.process = None

class UCIEngineManager:
    """
    Manages multiple UCI engines with security and resource management
    """
    
    def __init__(self):
        self.engines: Dict[str, SecureUCIEngine] = {}
        self.engine_configs = self._load_engine_configs()
        self._active_games: Dict[str, str] = {}  # game_id -> engine_name
        
        # Security: Rate limiting
        self._request_counts: Dict[str, List[float]] = {}
        self.max_requests_per_minute = 60
    
    def _load_engine_configs(self) -> Dict[str, EngineConfig]:
        """Load engine configurations"""
        engines_dir = os.path.join(os.path.dirname(__file__), '..', 'engines')
        configs = {}
        
        # V7P3R Engine
        v7p3r_path = os.path.join(engines_dir, 'v7p3r_engine.exe')
        if os.path.exists(v7p3r_path):
            configs['V7P3R'] = EngineConfig(
                name='V7P3R',
                executable_path=v7p3r_path,
                startup_timeout=10,
                move_timeout=30,
                supports_eval=True
            )
        
        # C0BR4 Engine  
        cobra_path = os.path.join(engines_dir, 'cobra_engine.exe')
        if os.path.exists(cobra_path):
            configs['C0BR4'] = EngineConfig(
                name='C0BR4',
                executable_path=cobra_path,
                startup_timeout=8,
                move_timeout=25,
                supports_eval=True
            )
        
        # SlowMate Engine
        slowmate_path = os.path.join(engines_dir, 'slowmate_engine.exe')
        if os.path.exists(slowmate_path):
            configs['SlowMate'] = EngineConfig(
                name='SlowMate',
                executable_path=slowmate_path,
                startup_timeout=5,
                move_timeout=20,
                supports_eval=False
            )
        
        return configs
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engines plus Human option"""
        engines = ['Human'] + list(self.engine_configs.keys())
        return engines
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        if client_id not in self._request_counts:
            self._request_counts[client_id] = []
        
        # Remove old requests
        self._request_counts[client_id] = [
            req_time for req_time in self._request_counts[client_id] 
            if req_time > minute_ago
        ]
        
        # Check if under limit
        if len(self._request_counts[client_id]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        self._request_counts[client_id].append(now)
        return True
    
    def get_engine_move(self, engine_name: str, fen: str, time_limit_ms: int = 1000, 
                       client_id: str = "default") -> Optional[Tuple[str, Optional[float], float]]:
        """
        Get move from specified engine with security checks
        Returns: (move, evaluation, time_taken) or None
        """
        # Security: Rate limiting
        if not self.check_rate_limit(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return None
        
        # Security: Input validation
        if engine_name not in self.engine_configs:
            logger.error(f"Invalid engine name: {engine_name}")
            return None
        
        # Get or create engine instance
        if engine_name not in self.engines:
            config = self.engine_configs[engine_name]
            engine = SecureUCIEngine(config)
            
            if not engine.start():
                logger.error(f"Failed to start engine: {engine_name}")
                return None
                
            self.engines[engine_name] = engine
        
        engine = self.engines[engine_name]
        
        # Security: Time limit bounds
        time_limit_ms = max(100, min(time_limit_ms, 30000))  # 0.1s to 30s
        
        try:
            result = engine.get_best_move(fen, time_limit_ms)
            return result
        except Exception as e:
            logger.error(f"Error getting move from {engine_name}: {e}")
            return None
    
    def shutdown_all_engines(self):
        """Shutdown all engine processes"""
        for engine in self.engines.values():
            try:
                engine.stop()
            except Exception as e:
                logger.error(f"Error stopping engine: {e}")
        
        self.engines.clear()
    
    def cleanup_inactive_engines(self, max_idle_time: float = 600):
        """Clean up engines that have been idle for too long"""
        current_time = time.time()
        engines_to_remove = []
        
        for name, engine in self.engines.items():
            # Check if engine has been idle
            if (current_time - getattr(engine, '_last_activity', current_time)) > max_idle_time:
                engines_to_remove.append(name)
        
        for name in engines_to_remove:
            try:
                self.engines[name].stop()
                del self.engines[name]
                logger.info(f"Cleaned up idle engine: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up engine {name}: {e}")
