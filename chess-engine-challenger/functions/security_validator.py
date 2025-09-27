"""
Security Validator for Chess Engine Challenger
Input validation and rate limiting for safe public access
"""

import re
import time
import chess
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Input validation for chess engine communication"""
    
    def __init__(self):
        self.valid_engines = ['Human', 'V7P3R', 'C0BR4', 'SlowMate', 'Random_Opponent']
        self.valid_time_controls = ['30|0', '10|5', '5|5', '3|2', '1|1']
    
    def validate_move_input(self, move_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate move input for security"""
        
        required_fields = ['game_id', 'move']
        for field in required_fields:
            if field not in move_data:
                return False, f"Missing required field: {field}"
        
        # Validate game_id (UUID format)
        game_id = move_data['game_id']
        if not re.match(r'^[a-f0-9\-]{36}$', str(game_id)):
            return False, "Invalid game ID format"
        
        # Validate move (UCI format)
        move = move_data['move']
        if not self._validate_uci_move(move):
            return False, "Invalid move format"
        
        return True, None
    
    def validate_game_creation(self, game_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate game creation request"""
        
        required_fields = ['white_player', 'black_player', 'time_control']
        for field in required_fields:
            if field not in game_data:
                return False, f"Missing required field: {field}"
        
        # Validate players
        white_player = game_data['white_player']
        black_player = game_data['black_player']
        
        if white_player not in self.valid_engines:
            return False, f"Invalid white player: {white_player}"
        
        if black_player not in self.valid_engines:
            return False, f"Invalid black player: {black_player}"
        
        # Validate time control
        time_control = game_data['time_control']
        if time_control not in self.valid_time_controls:
            return False, f"Invalid time control: {time_control}"
        
        return True, None
    
    def _validate_uci_move(self, move: str) -> bool:
        """Validate UCI move format"""
        if not isinstance(move, str) or len(move) < 4 or len(move) > 5:
            return False
        
        # Standard UCI: e2e4, e7e8q, etc.
        pattern = r'^[a-h][1-8][a-h][1-8][qrbn]?$'
        return bool(re.match(pattern, move.lower()))
    
    def validate_fen_position(self, fen: str) -> bool:
        """Validate FEN string"""
        try:
            if not isinstance(fen, str) or len(fen) > 100:
                return False
            
            # Use python-chess for validation
            chess.Board(fen)
            return True
        except:
            return False


class RateLimiter:
    """Simple rate limiting for public API"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.max_requests_per_minute = 30
    
    def check_rate_limit(self, client_id: str, endpoint: str = "default") -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        minute_ago = now - 60
        
        key = f"{client_id}:{endpoint}"
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [req for req in self.requests[key] if req > minute_ago]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
