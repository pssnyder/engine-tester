"""
Simple session logger for the universal chess GUI
"""
import json
import time
import datetime
import os
from typing import Optional, Dict, Any, List
import chess


class SimpleSessionLogger:
    """Simple session logger for tracking chess engine testing"""
    
    def __init__(self):
        self.moves = []
        self.evaluations = []
        self.notes = []
        self.session_start = time.time()
        self.session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"chess_session_{timestamp}"
    
    def log_move(self, move, player: str, time_taken: float, 
                 board_before=None, board_after=None, **additional_data):
        """Log a move to the session with optional additional metrics"""
        move_data = {
            'move': str(move),
            'player': player,
            'time_taken': time_taken,
            'timestamp': time.time(),
            'move_number': len(self.moves) + 1
        }
        
        if board_before:
            move_data['fen_before'] = board_before.fen()
        if board_after:
            move_data['fen_after'] = board_after.fen()
            
        # Add any additional engine metrics
        move_data.update(additional_data)
            
        self.moves.append(move_data)
        
    def log_evaluation(self, board, evaluator: str, eval_data: Dict[str, Any]):
        """Log a position evaluation"""
        eval_entry = {
            'fen': board.fen(),
            'evaluator': evaluator,
            'eval_data': eval_data,
            'timestamp': time.time()
        }
        self.evaluations.append(eval_entry)
        
    def add_note(self, note: str):
        """Add a note to the session"""
        note_entry = {
            'note': note,
            'timestamp': time.time()
        }
        self.notes.append(note_entry)
        
    def export_session(self, filepath: Optional[str] = None) -> str:
        """Export the session to a JSON file"""
        if not filepath:
            os.makedirs("sessions", exist_ok=True)
            filepath = f"sessions/{self.session_id}.json"
            
        session_data = {
            'session_id': self.session_id,
            'session_start': self.session_start,
            'session_duration': time.time() - self.session_start,
            'moves': self.moves,
            'evaluations': self.evaluations,
            'notes': self.notes,
            'stats': {
                'total_moves': len(self.moves),
                'total_evaluations': len(self.evaluations),
                'total_notes': len(self.notes)
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        return filepath
