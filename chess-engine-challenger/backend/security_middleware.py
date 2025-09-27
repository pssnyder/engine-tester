"""
Security Middleware for Chess Engine Challenger
Provides input validation, rate limiting, and attack prevention
"""

import re
import time
import chess
import hashlib
from typing import Dict, List, Optional, Any
from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Comprehensive security validation for chess engine communication"""
    
    def __init__(self):
        self.rate_limits: Dict[str, List[float]] = {}
        self.blocked_ips: set = set()
        
        # Security thresholds
        self.max_requests_per_minute = 30
        self.max_games_per_hour = 10
        self.max_moves_per_game = 300
        
    def validate_move_input(self, move_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate move input for security and correctness"""
        
        # Check required fields
        required_fields = ['game_id', 'move']
        for field in required_fields:
            if field not in move_data:
                return False, f"Missing required field: {field}"
        
        # Validate game_id format (UUID-like)
        game_id = move_data['game_id']
        if not re.match(r'^[a-f0-9\-]{36}$', str(game_id)):
            logger.warning(f"Invalid game_id format: {game_id}")
            return False, "Invalid game ID format"
        
        # Validate move format
        move = move_data['move']
        if not self._validate_chess_move(move):
            logger.warning(f"Invalid move format: {move}")
            return False, "Invalid move format"
        
        return True, None
    
    def validate_game_creation(self, game_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate game creation request"""
        
        # Required fields
        required_fields = ['white_player', 'black_player', 'time_control']
        for field in required_fields:
            if field not in game_data:
                return False, f"Missing required field: {field}"
        
        # Validate player names
        valid_players = ['Human', 'V7P3R', 'C0BR4', 'SlowMate']
        
        white_player = game_data['white_player']
        black_player = game_data['black_player']
        
        if white_player not in valid_players:
            return False, f"Invalid white player: {white_player}"
        
        if black_player not in valid_players:
            return False, f"Invalid black player: {black_player}"
        
        # Validate time control format
        time_control = game_data['time_control']
        if not re.match(r'^\d+\|\d+$', time_control):
            return False, "Invalid time control format (expected: minutes|increment)"
        
        return True, None
    
    def _validate_chess_move(self, move: str) -> bool:
        """Validate chess move notation"""
        if not isinstance(move, str):
            return False
        
        # Standard algebraic notation: e2e4, e7e8q, etc.
        if not re.match(r'^[a-h][1-8][a-h][1-8][qrbn]?$', move.lower()):
            return False
        
        # Additional validation: squares must be different
        if move[:2] == move[2:4]:
            return False
        
        return True
    
    def check_rate_limit(self, client_ip: str, endpoint: str = "default") -> bool:
        """Check if client has exceeded rate limits"""
        if client_ip in self.blocked_ips:
            return False
        
        now = time.time()
        minute_ago = now - 60
        
        # Create unique key for IP + endpoint
        key = f"{client_ip}:{endpoint}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Remove old requests
        self.rate_limits[key] = [
            req_time for req_time in self.rate_limits[key] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.rate_limits[key]) >= self.max_requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return False
        
        # Add current request
        self.rate_limits[key].append(now)
        return True
    
    def validate_fen_position(self, fen: str) -> bool:
        """Validate FEN string for chess position"""
        try:
            # Use python-chess to validate
            chess.Board(fen)
            
            # Additional security: reasonable length
            if len(fen) > 100:  # FEN shouldn't be this long
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = ['<', '>', '&', '"', "'", '(', ')', '{', '}']
            if any(pattern in fen for pattern in suspicious_patterns):
                return False
            
            return True
        except:
            return False
    
    def sanitize_string_input(self, input_str: str, max_length: int = 100) -> str:
        """Sanitize string input to prevent injection attacks"""
        if not isinstance(input_str, str):
            return ""
        
        # Truncate to max length
        input_str = input_str[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', '"', "'", '`', '(', ')', '{', '}', ';', '|']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')
        
        return input_str.strip()

# Global security validator instance
security_validator = SecurityValidator()

def rate_limit_decorator(endpoint_name: str = None):
    """Decorator to apply rate limiting to Flask routes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
            endpoint = endpoint_name or func.__name__
            
            if not security_validator.check_rate_limit(client_ip, endpoint):
                return jsonify({
                    'success': False, 
                    'error': 'Rate limit exceeded. Please wait before making more requests.'
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input_decorator(validation_func):
    """Decorator to validate input data"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
                
                is_valid, error_msg = validation_func(data)
                if not is_valid:
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                # Store validated data for the route
                g.validated_data = data
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Input validation error: {e}")
                return jsonify({'success': False, 'error': 'Invalid request format'}), 400
        
        return wrapper
    return decorator

def security_headers_decorator(func):
    """Add security headers to response"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        
        return response
    return wrapper
