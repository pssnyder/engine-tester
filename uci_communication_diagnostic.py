#!/usr/bin/env python3
"""
C0BR4 UCI Communication Diagnostic Tool v2.7
============================================
This tool acts as a "man-in-the-middle" to capture and analyze the exact UCI communication
between Arena (or any GUI) and C0BR4 to identify illegal move communication issues.

Features:
- Captures all UCI input/output 
- Validates move legality using python-chess
- Detects move format issues, timing problems, and protocol violations
- Logs problematic UCI sequences for debugging
"""

import chess
import chess.engine
import subprocess
import sys
import time
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

class UCICommunicationLogger:
    def __init__(self, engine_path: str, log_file: Optional[str] = None):
        self.engine_path = Path(engine_path)
        self.log_file = log_file or f"uci_communication_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.communication_log = []
        self.current_position = chess.Board()
        self.illegal_moves_detected = []
        self.warnings = []
        
    def log_communication(self, direction: str, message: str, timestamp: float = None):
        """Log a UCI communication event."""
        if timestamp is None:
            timestamp = time.time()
            
        entry = {
            'timestamp': timestamp,
            'direction': direction,  # 'GUI->ENGINE' or 'ENGINE->GUI'
            'message': message.strip(),
            'position_fen': self.current_position.fen(),
            'legal_moves': [move.uci() for move in self.current_position.legal_moves]
        }
        
        self.communication_log.append(entry)
        
        # Real-time analysis
        if direction == 'ENGINE->GUI' and message.startswith('bestmove'):
            self.analyze_bestmove(message, timestamp)
        elif direction == 'GUI->ENGINE' and message.startswith('position'):
            self.update_position(message)
            
    def analyze_bestmove(self, bestmove_message: str, timestamp: float):
        """Analyze a bestmove response for legality."""
        parts = bestmove_message.strip().split()
        if len(parts) < 2:
            return
            
        move_str = parts[1]
        
        # Skip special cases
        if move_str in ['(none)', 'resign', 'null']:
            return
            
        try:
            # Parse and validate the move
            move = chess.Move.from_uci(move_str)
            is_legal = move in self.current_position.legal_moves
            
            analysis = {
                'timestamp': timestamp,
                'move_uci': move_str,
                'is_legal': is_legal,
                'position_fen': self.current_position.fen(),
                'legal_moves_count': len(list(self.current_position.legal_moves)),
                'legal_moves': [m.uci() for m in self.current_position.legal_moves]
            }
            
            if not is_legal:
                print(f"🚨 ILLEGAL MOVE DETECTED: {move_str}")
                print(f"   Position: {self.current_position.fen()}")
                print(f"   Legal moves: {', '.join([m.uci() for m in list(self.current_position.legal_moves)][:10])}")
                
                self.illegal_moves_detected.append(analysis)
            else:
                print(f"✅ Legal move: {move_str}")
                
        except ValueError as e:
            print(f"❌ Invalid move format: {move_str} - {e}")
            self.warnings.append({
                'timestamp': timestamp,
                'type': 'invalid_move_format',
                'move': move_str,
                'error': str(e)
            })
    
    def update_position(self, position_command: str):
        """Update our tracking of the current position."""
        try:
            # Parse position command
            parts = position_command.split()
            
            if 'startpos' in parts:
                self.current_position = chess.Board()
                
                # Apply moves if present
                if 'moves' in parts:
                    moves_index = parts.index('moves')
                    for move_str in parts[moves_index + 1:]:
                        try:
                            move = chess.Move.from_uci(move_str)
                            if move in self.current_position.legal_moves:
                                self.current_position.push(move)
                            else:
                                print(f"⚠️  Illegal move in position history: {move_str}")
                        except:
                            print(f"⚠️  Invalid move in position history: {move_str}")
                            
            elif 'fen' in parts:
                # Extract FEN
                fen_start = parts.index('fen') + 1
                fen_parts = []
                for i in range(fen_start, len(parts)):
                    if parts[i] == 'moves':
                        break
                    fen_parts.append(parts[i])
                
                if len(fen_parts) >= 6:
                    fen = ' '.join(fen_parts[:6])
                    self.current_position = chess.Board(fen)
                    
                    # Apply moves if present
                    if 'moves' in parts:
                        moves_index = parts.index('moves')
                        for move_str in parts[moves_index + 1:]:
                            try:
                                move = chess.Move.from_uci(move_str)
                                if move in self.current_position.legal_moves:
                                    self.current_position.push(move)
                                else:
                                    print(f"⚠️  Illegal move in position history: {move_str}")
                            except:
                                print(f"⚠️  Invalid move in position history: {move_str}")
                                
        except Exception as e:
            print(f"⚠️  Error parsing position command: {e}")
    
    def save_log(self):
        """Save the communication log to file."""
        log_data = {
            'metadata': {
                'engine_path': str(self.engine_path),
                'log_start': datetime.now().isoformat(),
                'total_communications': len(self.communication_log),
                'illegal_moves_detected': len(self.illegal_moves_detected),
                'warnings': len(self.warnings)
            },
            'communication_log': self.communication_log,
            'illegal_moves': self.illegal_moves_detected,
            'warnings': self.warnings
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"📊 Communication log saved to: {self.log_file}")

class UCIProxy:
    """Acts as a proxy between GUI and engine to capture communication."""
    
    def __init__(self, engine_path: str):
        self.engine_path = engine_path
        self.logger = UCICommunicationLogger(engine_path)
        self.engine_process = None
        
    def start_engine(self):
        """Start the engine process."""
        try:
            self.engine_process = subprocess.Popen(
                [self.engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            print(f"✅ Started engine: {self.engine_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to start engine: {e}")
            return False
    
    def run_interactive_test(self):
        """Run an interactive test session."""
        if not self.start_engine():
            return
            
        print("\n🚀 C0BR4 UCI Communication Diagnostic Tool v2.7")
        print("=" * 60)
        print("Type UCI commands (or 'quit' to exit):")
        print("Commands are sent to C0BR4 and responses are analyzed.")
        print("All communication is logged for analysis.")
        print("=" * 60)
        
        # Start background thread to read engine output
        def read_engine_output():
            while self.engine_process and self.engine_process.poll() is None:
                try:
                    line = self.engine_process.stdout.readline()
                    if line:
                        timestamp = time.time()
                        self.logger.log_communication('ENGINE->GUI', line, timestamp)
                        print(f"ENGINE: {line.strip()}")
                except:
                    break
        
        output_thread = threading.Thread(target=read_engine_output, daemon=True)
        output_thread.start()
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input("UCI> ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input:
                        continue
                    
                    # Send command to engine
                    timestamp = time.time()
                    self.logger.log_communication('GUI->ENGINE', user_input, timestamp)
                    
                    if self.engine_process and self.engine_process.stdin:
                        self.engine_process.stdin.write(f"{user_input}\n")
                        self.engine_process.stdin.flush()
                    
                    # Brief pause to let engine respond
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
        
        finally:
            # Clean up
            if self.engine_process:
                try:
                    self.engine_process.stdin.write("quit\n")
                    self.engine_process.stdin.flush()
                    self.engine_process.terminate()
                    self.engine_process.wait(timeout=2)
                except:
                    self.engine_process.kill()
            
            # Save log
            self.logger.save_log()
            
            # Print summary
            print(f"\n📊 SESSION SUMMARY:")
            print(f"Total communications: {len(self.logger.communication_log)}")
            print(f"Illegal moves detected: {len(self.logger.illegal_moves_detected)}")
            print(f"Warnings: {len(self.logger.warnings)}")
            
            if self.logger.illegal_moves_detected:
                print(f"\n🚨 ILLEGAL MOVES FOUND:")
                for illegal in self.logger.illegal_moves_detected:
                    print(f"  {illegal['move_uci']} in position {illegal['position_fen'][:30]}...")

def run_quick_illegal_test(engine_path: str):
    """Run a quick test with known problematic positions."""
    
    # These are positions where C0BR4 made illegal moves in tournament
    test_positions = [
        {
            'name': 'Tournament illegal h8h1',
            'fen': 'r6r/pp2kb2/3p1p2/1N1Pp3/3bP3/P2B2P1/1P1Q2PP/7K b - - 7 28',
            'description': 'Position where C0BR4 played illegal h8h1'
        },
        {
            'name': 'Tournament illegal a2a1', 
            'fen': '8/5p1k/5Ppb/2p3P1/qp6/8/KB5Q/8 w - - 5 59',
            'description': 'Position where C0BR4 played illegal a2a1'
        },
        {
            'name': 'Starting position test',
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'description': 'Starting position for baseline test'
        }
    ]
    
    proxy = UCIProxy(engine_path)
    if not proxy.start_engine():
        return
    
    print(f"🧪 Running quick illegal move test...")
    
    try:
        # Initialize engine
        commands = ["uci", "isready"]
        for cmd in commands:
            proxy.engine_process.stdin.write(f"{cmd}\n")
            proxy.engine_process.stdin.flush()
            proxy.logger.log_communication('GUI->ENGINE', cmd)
            time.sleep(0.5)
            
            # Read response
            while True:
                line = proxy.engine_process.stdout.readline()
                if line:
                    proxy.logger.log_communication('ENGINE->GUI', line)
                    print(f"ENGINE: {line.strip()}")
                    if line.strip() in ['uciok', 'readyok']:
                        break
                else:
                    break
        
        # Test each position
        for pos in test_positions:
            print(f"\n🔍 Testing: {pos['name']}")
            print(f"   {pos['description']}")
            print(f"   FEN: {pos['fen']}")
            
            # Set position
            position_cmd = f"position fen {pos['fen']}"
            proxy.engine_process.stdin.write(f"{position_cmd}\n")
            proxy.engine_process.stdin.flush()
            proxy.logger.log_communication('GUI->ENGINE', position_cmd)
            
            # Get move
            go_cmd = "go movetime 3000"
            proxy.engine_process.stdin.write(f"{go_cmd}\n")
            proxy.engine_process.stdin.flush()
            proxy.logger.log_communication('GUI->ENGINE', go_cmd)
            
            # Wait for bestmove
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                line = proxy.engine_process.stdout.readline()
                if line:
                    proxy.logger.log_communication('ENGINE->GUI', line)
                    print(f"ENGINE: {line.strip()}")
                    if line.strip().startswith('bestmove'):
                        break
                        
            time.sleep(0.5)
            
    finally:
        # Clean up
        if proxy.engine_process:
            proxy.engine_process.stdin.write("quit\n")
            proxy.engine_process.stdin.flush()
            proxy.engine_process.terminate()
            proxy.engine_process.wait(timeout=2)
        
        proxy.logger.save_log()
        
        # Summary
        print(f"\n📊 QUICK TEST SUMMARY:")
        print(f"Positions tested: {len(test_positions)}")
        print(f"Illegal moves detected: {len(proxy.logger.illegal_moves_detected)}")
        
        if proxy.logger.illegal_moves_detected:
            print(f"\n🚨 ILLEGAL MOVES REPRODUCED:")
            for illegal in proxy.logger.illegal_moves_detected:
                print(f"  {illegal['move_uci']} in position ending ...{illegal['position_fen'][-20:]}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python uci_communication_diagnostic.py <engine_path> [--quick-test]")
        print("")
        print("  <engine_path>: Path to C0BR4 engine executable")
        print("  --quick-test: Run automated test with known problematic positions")
        print("  (default): Run interactive UCI communication test")
        sys.exit(1)
    
    engine_path = sys.argv[1]
    
    if not Path(engine_path).exists():
        print(f"❌ Engine not found: {engine_path}")
        sys.exit(1)
    
    if len(sys.argv) > 2 and sys.argv[2] == '--quick-test':
        run_quick_illegal_test(engine_path)
    else:
        proxy = UCIProxy(engine_path)
        proxy.run_interactive_test()

if __name__ == "__main__":
    main()
