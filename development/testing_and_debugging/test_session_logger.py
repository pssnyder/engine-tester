#!/usr/bin/env python3
"""
Test Session Logger for Chess Engine Testing

Logs all actions, positions, moves, evaluations, and performance metrics
during testing sessions for comprehensive analysis.
"""

import json
import time
import chess
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class MoveRecord:
    """Record of a single move in the game"""
    move_number: int
    player: str  # "human", "engine", or specific engine name
    move_uci: str
    move_san: str
    time_taken: float
    fen_before: str
    fen_after: str
    timestamp: float

@dataclass
class EvaluationRecord:
    """Record of a position evaluation"""
    fen: str
    evaluator: str  # Engine name or "manual"
    score: float  # Centipawns (+ for white, - for black)
    depth: int
    nodes: int
    time_ms: float
    nps: int
    pv: List[str]  # Principal variation
    is_mate: bool
    mate_in: Optional[int]
    timestamp: float

@dataclass
class TestAction:
    """Record of a test action (button press, etc.)"""
    action_type: str  # "single_test", "full_suite", "engine_move", etc.
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    duration: float
    timestamp: float

@dataclass
class SessionMetrics:
    """Overall session metrics"""
    session_id: str
    start_time: float
    end_time: Optional[float]
    total_moves: int
    total_evaluations: int
    total_tests: int
    engines_used: List[str]
    positions_analyzed: int

class TestSessionLogger:
    """Comprehensive test session logger"""
    
    def __init__(self, session_name: Optional[str] = None):
        self.session_id = session_name or f"chess_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        
        # Data storage
        self.moves: List[MoveRecord] = []
        self.evaluations: List[EvaluationRecord] = []
        self.test_actions: List[TestAction] = []
        self.position_history: List[str] = []
        
        # Current game state
        self.current_move_number = 1
        self.current_board = chess.Board()
        
        # Session info
        self.engines_used = set()
        self.session_notes = []
        
        print(f"Started test session: {self.session_id}")
    
    def log_move(self, move: chess.Move, player: str, time_taken: float = 0.0, 
                 board_before: Optional[chess.Board] = None, 
                 board_after: Optional[chess.Board] = None):
        """Log a move made in the game"""
        
        if board_before is None:
            board_before = self.current_board.copy()
        if board_after is None:
            board_after = board_before.copy()
            board_after.push(move)
            
        # Update our tracking
        self.current_board = board_after.copy()
        
        move_record = MoveRecord(
            move_number=self.current_move_number,
            player=player,
            move_uci=move.uci(),
            move_san=board_before.san(move),
            time_taken=time_taken,
            fen_before=board_before.fen(),
            fen_after=board_after.fen(),
            timestamp=time.time()
        )
        
        self.moves.append(move_record)
        self.position_history.append(board_after.fen())
        
        if board_after.turn == chess.WHITE:
            self.current_move_number += 1
            
        if player != "human":
            self.engines_used.add(player)
            
        print(f"Logged move: {move_record.move_san} by {player}")
    
    def log_evaluation(self, board: chess.Board, evaluator: str, eval_data: Dict[str, Any]):
        """Log a position evaluation"""
        
        eval_record = EvaluationRecord(
            fen=board.fen(),
            evaluator=evaluator,
            score=eval_data.get("score", 0),
            depth=eval_data.get("depth", 0),
            nodes=eval_data.get("nodes", 0),
            time_ms=eval_data.get("time_ms", 0),
            nps=eval_data.get("nps", 0),
            pv=eval_data.get("pv", []),
            is_mate=eval_data.get("is_mate", False),
            mate_in=eval_data.get("mate_in"),
            timestamp=time.time()
        )
        
        self.evaluations.append(eval_record)
        self.engines_used.add(evaluator)
        
        # Print evaluation in a nice format
        score_str = f"{eval_record.score:+.2f}" if not eval_record.is_mate else f"Mate in {eval_record.mate_in}"
        print(f"Evaluation by {evaluator}: {score_str} (depth {eval_record.depth}, {eval_record.nodes} nodes)")
    
    def log_test_action(self, action_type: str, parameters: Dict[str, Any], 
                       result: Dict[str, Any], duration: float):
        """Log a test action"""
        
        action = TestAction(
            action_type=action_type,
            parameters=parameters,
            result=result,
            duration=duration,
            timestamp=time.time()
        )
        
        self.test_actions.append(action)
        print(f"Logged test action: {action_type} (duration: {duration:.3f}s)")
    
    def add_note(self, note: str):
        """Add a note to the session"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.session_notes.append(f"[{timestamp}] {note}")
        print(f"Session note: {note}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        current_time = time.time()
        
        return {
            "session_id": self.session_id,
            "duration": current_time - self.start_time,
            "total_moves": len(self.moves),
            "total_evaluations": len(self.evaluations),
            "total_test_actions": len(self.test_actions),
            "engines_used": list(self.engines_used),
            "positions_analyzed": len(set(self.position_history)),
            "current_position": self.current_board.fen(),
            "last_move": self.moves[-1].move_san if self.moves else None
        }
    
    def export_session(self, filepath: Optional[str] = None) -> str:
        """Export the complete session data to JSON"""
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"test_session_{self.session_id}_{timestamp}.json"
        
        # Prepare final metrics
        end_time = time.time()
        metrics = SessionMetrics(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=end_time,
            total_moves=len(self.moves),
            total_evaluations=len(self.evaluations),
            total_tests=len(self.test_actions),
            engines_used=list(self.engines_used),
            positions_analyzed=len(set(self.position_history))
        )
        
        # Compile all data
        session_data = {
            "metadata": {
                "session_id": self.session_id,
                "export_timestamp": datetime.now().isoformat(),
                "duration_seconds": end_time - self.start_time,
                "chess_ai_version": "1.0",  # Could be dynamic
                "format_version": "1.0"
            },
            "metrics": asdict(metrics),
            "moves": [asdict(move) for move in self.moves],
            "evaluations": [asdict(eval) for eval in self.evaluations],
            "test_actions": [asdict(action) for action in self.test_actions],
            "position_history": self.position_history,
            "session_notes": self.session_notes,
            "final_position": self.current_board.fen()
        }
        
        # Export to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            print(f"Session exported to: {filepath}")
            print(f"Session summary:")
            print(f"  Duration: {end_time - self.start_time:.1f} seconds")
            print(f"  Moves: {len(self.moves)}")
            print(f"  Evaluations: {len(self.evaluations)}")
            print(f"  Test actions: {len(self.test_actions)}")
            print(f"  Engines used: {', '.join(self.engines_used) if self.engines_used else 'None'}")
            
            return filepath
            
        except Exception as e:
            print(f"Error exporting session: {e}")
            return ""
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics from the session"""
        
        if not self.evaluations:
            return {"error": "No evaluations to analyze"}
        
        # Analyze search performance by engine
        engine_stats = {}
        
        for eval_record in self.evaluations:
            engine = eval_record.evaluator
            if engine not in engine_stats:
                engine_stats[engine] = {
                    "total_evaluations": 0,
                    "total_nodes": 0,
                    "total_time_ms": 0,
                    "depths": [],
                    "nps_values": []
                }
            
            stats = engine_stats[engine]
            stats["total_evaluations"] += 1
            stats["total_nodes"] += eval_record.nodes
            stats["total_time_ms"] += eval_record.time_ms
            stats["depths"].append(eval_record.depth)
            if eval_record.nps > 0:
                stats["nps_values"].append(eval_record.nps)
        
        # Calculate averages
        for engine, stats in engine_stats.items():
            if stats["total_evaluations"] > 0:
                stats["avg_nodes_per_eval"] = stats["total_nodes"] / stats["total_evaluations"]
                stats["avg_time_per_eval"] = stats["total_time_ms"] / stats["total_evaluations"]
                stats["avg_depth"] = sum(stats["depths"]) / len(stats["depths"])
                
                if stats["nps_values"]:
                    stats["avg_nps"] = sum(stats["nps_values"]) / len(stats["nps_values"])
                    stats["peak_nps"] = max(stats["nps_values"])
                else:
                    stats["avg_nps"] = 0
                    stats["peak_nps"] = 0
        
        return {
            "engine_performance": engine_stats,
            "session_metrics": self.get_session_summary()
        }

class SessionAnalyzer:
    """Analyze exported test session data"""
    
    @staticmethod
    def load_session(filepath: str) -> Optional[Dict[str, Any]]:
        """Load a session from exported JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    @staticmethod
    def compare_sessions(session_files: List[str]) -> Dict[str, Any]:
        """Compare performance across multiple sessions"""
        sessions = []
        for file in session_files:
            session = SessionAnalyzer.load_session(file)
            if session:
                sessions.append(session)
        
        if not sessions:
            return {"error": "No valid sessions to compare"}
        
        comparison = {
            "session_count": len(sessions),
            "sessions": []
        }
        
        for session in sessions:
            metrics = session.get("metrics", {})
            comparison["sessions"].append({
                "session_id": metrics.get("session_id", "unknown"),
                "duration": metrics.get("end_time", 0) - metrics.get("start_time", 0),
                "total_moves": metrics.get("total_moves", 0),
                "total_evaluations": metrics.get("total_evaluations", 0),
                "engines_used": metrics.get("engines_used", [])
            })
        
        return comparison
