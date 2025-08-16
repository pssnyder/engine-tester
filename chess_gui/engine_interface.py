#!/usr/bin/env python3
"""
Universal Engine Interface for Chess Testing

Provides a common API for interacting with chess engines through:
1. UCI protocol (universal)
2. Direct Python module access (when available)

This abstraction layer allows the testing GUI to work with any chess engine
while providing enhanced functionality for engines with direct Python access.
"""

import chess
import chess.engine
import time
import threading
import queue
from typing import Optional, Dict, Any, Callable, List, Tuple
from abc import ABC, abstractmethod

class EngineInterface(ABC):
    """Abstract base class for engine interfaces"""
    
    def __init__(self, name: str):
        self.name = name
        self.info_callback: Optional[Callable] = None
        
    @abstractmethod
    def start(self) -> bool:
        """Start the engine"""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop the engine"""
        pass
        
    @abstractmethod
    def get_move(self, board: chess.Board, time_limit: float = 1.0, depth: Optional[int] = None) -> Optional[str]:
        """Get best move from engine"""
        pass
        
    @abstractmethod
    def evaluate_position(self, board: chess.Board, depth: Optional[int] = None) -> Dict[str, Any]:
        """Evaluate current position"""
        pass
        
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if engine is ready"""
        pass
        
    def set_info_callback(self, callback: Optional[Callable]):
        """Set callback for search information"""
        self.info_callback = callback

class UCIEngine(EngineInterface):
    """UCI-based engine interface for universal compatibility"""
    
    def __init__(self, name: str, engine_path: str):
        super().__init__(name)
        self.engine_path = engine_path
        self.engine = None
        
    def start(self) -> bool:
        """Start UCI engine (simplified version)"""
        try:
            # For now, we'll implement basic UCI support
            # This can be enhanced later with proper async handling
            print(f"UCI engine {self.name} would be started from {self.engine_path}")
            return True
        except Exception as e:
            print(f"Failed to start UCI engine {self.name}: {e}")
            return False
            
    def stop(self):
        """Stop UCI engine"""
        if self.engine:
            self.engine = None
            
    def get_move(self, board: chess.Board, time_limit: float = 1.0, depth: Optional[int] = None) -> Optional[str]:
        """Get best move from UCI engine (placeholder)"""
        print(f"UCI engine {self.name} would analyze position and return move")
        return None  # Placeholder for UCI implementation
            
    def evaluate_position(self, board: chess.Board, depth: Optional[int] = None) -> Dict[str, Any]:
        """Evaluate position using UCI engine (placeholder)"""
        print(f"UCI engine {self.name} would evaluate position")
        return {}  # Placeholder for UCI implementation
        
    def is_ready(self) -> bool:
        """Check if UCI engine is ready"""
        return True  # Simplified for now
        
    def _format_uci_info(self, info) -> Dict[str, Any]:
        """Format UCI info to standard format (placeholder)"""
        return {}

class ChessAIEngine(EngineInterface):
    """Direct Python interface for chess-ai engine"""
    
    def __init__(self, name: str = "chess-ai"):
        super().__init__(name)
        self.ready = False
        
        # Import chess-ai modules
        try:
            import chess_ai
            import interface
            self.chess_ai = chess_ai
            self.interface = interface
            self.ready = True
        except ImportError as e:
            print(f"Failed to import chess-ai modules: {e}")
            
    def start(self) -> bool:
        """Start chess-ai engine"""
        return self.ready
        
    def stop(self):
        """Stop chess-ai engine"""
        pass  # No cleanup needed for direct Python access
        
    def get_move(self, board: chess.Board, time_limit: float = 1.0, depth: Optional[int] = None) -> Optional[str]:
        """Get best move from chess-ai"""
        if not self.ready:
            return None
            
        try:
            # Use our search function with info callback
            best_move = self.chess_ai.search(
                board=board.copy(),
                depth=depth or 4,
                time_limit=time_limit,
                info_callback=self.info_callback,
                stop_event=None
            )
            return best_move
            
        except Exception as e:
            print(f"Error getting move from chess-ai: {e}")
            return None
            
    def evaluate_position(self, board: chess.Board, depth: Optional[int] = None) -> Dict[str, Any]:
        """Evaluate position using chess-ai"""
        if not self.ready:
            return {}
            
        try:
            # Capture evaluation info
            eval_info = {}
            
            def capture_eval(**info):
                eval_info.update(info)
                
            # Run evaluation
            self.chess_ai.search(
                board=board.copy(),
                depth=depth or 3,
                time_limit=0.1,  # Quick eval
                info_callback=capture_eval,
                stop_event=None
            )
            
            return eval_info
            
        except Exception as e:
            print(f"Error evaluating position with chess-ai: {e}")
            return {}
            
    def is_ready(self) -> bool:
        """Check if chess-ai is ready"""
        return self.ready
        
    def get_detailed_metrics(self, board: chess.Board, depth: int = 4) -> Dict[str, Any]:
        """Get detailed search metrics (chess-ai specific)"""
        if not self.ready:
            return {}
            
        try:
            metrics = []
            
            def capture_metrics(**info):
                metrics.append(info.copy())
                
            start_time = time.time()
            best_move = self.chess_ai.search(
                board=board.copy(),
                depth=depth,
                info_callback=capture_metrics,
                stop_event=None
            )
            total_time = time.time() - start_time
            
            return {
                "best_move": best_move,
                "total_time": total_time,
                "search_metrics": metrics,
                "final_metrics": metrics[-1] if metrics else {}
            }
            
        except Exception as e:
            print(f"Error getting detailed metrics: {e}")
            return {}

class EngineManager:
    """Manages multiple engine interfaces"""
    
    def __init__(self):
        self.engines: Dict[str, EngineInterface] = {}
        self.current_engine: Optional[str] = None
        
    def add_engine(self, interface: EngineInterface) -> bool:
        """Add an engine interface"""
        if interface.start():
            self.engines[interface.name] = interface
            if not self.current_engine:
                self.current_engine = interface.name
            return True
        return False
        
    def remove_engine(self, name: str):
        """Remove an engine interface"""
        if name in self.engines:
            self.engines[name].stop()
            del self.engines[name]
            if self.current_engine == name:
                self.current_engine = list(self.engines.keys())[0] if self.engines else None
                
    def set_current_engine(self, name: str) -> bool:
        """Set the current active engine"""
        if name in self.engines:
            self.current_engine = name
            return True
        return False
        
    def get_current_engine(self) -> Optional[EngineInterface]:
        """Get the current active engine"""
        if self.current_engine and self.current_engine in self.engines:
            return self.engines[self.current_engine]
        return None
        
    def list_engines(self) -> List[str]:
        """List all available engines"""
        return list(self.engines.keys())
        
    def stop_all(self):
        """Stop all engines"""
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()
        self.current_engine = None

# Factory function for creating engine interfaces
def create_engine_interface(engine_type: str, **kwargs) -> Optional[EngineInterface]:
    """Factory function to create engine interfaces"""
    
    if engine_type == "chess-ai":
        return ChessAIEngine()
    elif engine_type == "uci":
        name = kwargs.get("name", "Unknown Engine")
        path = kwargs.get("path", "")
        if not path:
            raise ValueError("UCI engine requires 'path' parameter")
        return UCIEngine(name, path)
    else:
        raise ValueError(f"Unknown engine type: {engine_type}")
