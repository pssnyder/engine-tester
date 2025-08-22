"""
Engine interface module for Puzzle Challenger.
Handles communication with UCI chess engines.
"""

import subprocess
import threading
import time
import chess
import re
import os

class UCIEngine:
    """Class to interface with UCI chess engines."""
    
    def __init__(self, engine_path):
        """Initialize the engine with the path to the executable."""
        self.engine_path = engine_path
        self.process = None
        self.ready = False
        self.name = "Unknown Engine"
        self.author = "Unknown"
        self.options = {}
        self._result = None
        self._command_queue = []
        
    def start(self):
        """Start the engine process."""
        if self.process is not None and self.process.poll() is None:
            # Engine already running
            return
        
        try:
            # Start the engine process
            self.process = subprocess.Popen(
                self.engine_path,
                universal_newlines=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                cwd=os.path.dirname(self.engine_path)
            )
            
            # Start the output reading thread
            self.output_thread = threading.Thread(
                target=self._read_output,
                daemon=True
            )
            self.output_thread.start()
            
            # Initialize the engine with UCI protocol
            self.send_command("uci")
            
            # Wait for the engine to be ready
            timeout = 5.0
            start_time = time.time()
            while not self.ready and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if not self.ready:
                raise TimeoutError("Engine did not respond with 'uciok' in time")
            
            # Set some default options
            self.send_command("setoption name Hash value 128")
            self.send_command("isready")
            
            # Wait for engine to be ready
            self._wait_for_ready()
            
            print(f"Engine '{self.name}' by {self.author} started successfully")
            
        except Exception as e:
            print(f"Error starting engine: {e}")
            if self.process:
                self.process.terminate()
                self.process = None
            raise
    
    def _read_output(self):
        """Read and process engine output in a separate thread."""
        for line in iter(self.process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue
                
            # Process identification info
            if line.startswith("id name "):
                self.name = line[8:].strip()
            elif line.startswith("id author "):
                self.author = line[10:].strip()
            
            # Process options
            elif line.startswith("option name "):
                self._parse_option(line)
            
            # Process UCI protocol commands
            elif line == "uciok":
                self.ready = True
            elif line == "readyok":
                self._result = "ready"
            
            # Process bestmove
            elif line.startswith("bestmove "):
                self._result = line
    
    def _parse_option(self, line):
        """Parse engine option information."""
        # This is a simplified implementation
        match = re.match(r"option name ([^ ]+) type ([^ ]+)(.*)", line)
        if match:
            name, option_type, rest = match.groups()
            self.options[name] = {
                "type": option_type,
                "default": None,
                "min": None,
                "max": None,
                "var": []
            }
            
            # Parse additional parameters
            if "default" in rest:
                match = re.search(r"default ([^ ]+)", rest)
                if match:
                    self.options[name]["default"] = match.group(1)
            
            if "min" in rest:
                match = re.search(r"min ([^ ]+)", rest)
                if match:
                    self.options[name]["min"] = match.group(1)
                    
            if "max" in rest:
                match = re.search(r"max ([^ ]+)", rest)
                if match:
                    self.options[name]["max"] = match.group(1)
                    
            if "var" in rest:
                vars = re.findall(r"var ([^ ]+)", rest)
                self.options[name]["var"] = vars
    
    def _wait_for_ready(self, timeout=5.0):
        """Wait for the engine to respond with 'readyok'."""
        start_time = time.time()
        while self._result != "ready" and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if self._result != "ready":
            raise TimeoutError("Engine did not respond with 'readyok' in time")
        
        self._result = None
    
    def send_command(self, command):
        """Send a command to the engine."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Engine process is not running")
        
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
    
    def get_best_move(self, board, time_ms=1000):
        """
        Get the best move for the given position.
        
        Args:
            board: A chess.Board object representing the position
            time_ms: Time to think in milliseconds
            
        Returns:
            The best move in UCI notation (e.g., "e2e4")
        """
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Engine process is not running")
        
        # Reset previous result
        self._result = None
        
        # Set up the position
        fen = board.fen()
        self.send_command("position fen " + fen)
        
        # Start calculating
        self.send_command(f"go movetime {time_ms}")
        
        # Wait for the result
        timeout = time_ms / 1000.0 + 1.0  # Add 1 second buffer
        start_time = time.time()
        while self._result is None and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if self._result is None:
            raise TimeoutError("Engine did not respond with a move in time")
        
        # Parse the bestmove
        match = re.match(r"bestmove ([a-h][1-8][a-h][1-8][qrbnk]?)", self._result)
        if match:
            bestmove = match.group(1)
            return bestmove
        else:
            raise ValueError(f"Could not parse engine response: {self._result}")
    
    def stop(self):
        """Stop the engine."""
        if self.process is not None and self.process.poll() is None:
            try:
                self.send_command("quit")
                self.process.wait(timeout=1.0)
            except:
                self.process.terminate()
            finally:
                self.process = None
    
    def __del__(self):
        """Ensure the engine is stopped when the object is garbage collected."""
        self.stop()
