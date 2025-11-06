#!/usr/bin/env python3
"""
VPR Chess Engine v9.0 - C0BR4 Intelligence Port
A UCI-compatible chess engine porting C0BR4's proven tournament architecture.

Core Philosophy:
- Port battle-tested C0BR4 heuristics incrementally
- Keep it simple (between Material Opponent and V7P3R complexity)
- Focus on decisiveness and forward progress
- Maintain speed while adding intelligence

v9.0 Features (C0BR4-inspired):
- Hierarchical move ordering (MVV-LVA + positional bonuses)
- Piece-square tables for positional understanding
- Phase-aware evaluation and time management
- Static Exchange Evaluation (SEE) for trade intelligence
- Forward progress encouragement (solves rook shuffling)

C0BR4 Ports in v9.0:
- Move ordering: Captures (10000+), Promotions (9000+), Checks (500), Center (10), Development (5)
- Basic piece-square tables (opening/endgame)
- Positional bonuses for decisive play
"""

import sys
import chess
import random
import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Piece values with dynamic bishop evaluation
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 325,  # Base value, adjusted dynamically
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

BISHOP_PAIR_BONUS = 50  # Additional value when both bishops present
BISHOP_ALONE_PENALTY = 50  # Penalty when only one bishop remains

# Piece-Square Tables (C0BR4-style) - values from White's perspective
# Tables are indexed [rank][file] where rank 0 = rank 1, rank 7 = rank 8

# Pawn PST - encourage center control and advancement
PST_PAWN_OPENING = [
    [0,   0,   0,   0,   0,   0,   0,   0],   # Rank 1
    [50,  50,  50,  50,  50,  50,  50,  50],  # Rank 2
    [10,  10,  20,  30,  30,  20,  10,  10],  # Rank 3
    [5,   5,   10,  25,  25,  10,  5,   5],   # Rank 4
    [0,   0,   0,   20,  20,  0,   0,   0],   # Rank 5
    [5,   -5,  -10, 0,   0,   -10, -5,  5],   # Rank 6
    [5,   10,  10,  -20, -20, 10,  10,  5],   # Rank 7
    [0,   0,   0,   0,   0,   0,   0,   0]    # Rank 8
]

PST_PAWN_ENDGAME = [
    [0,   0,   0,   0,   0,   0,   0,   0],   # Rank 1
    [80,  80,  80,  80,  80,  80,  80,  80],  # Rank 2 - push to promote
    [50,  50,  50,  50,  50,  50,  50,  50],  # Rank 3
    [30,  30,  30,  30,  30,  30,  30,  30],  # Rank 4
    [20,  20,  20,  20,  20,  20,  20,  20],  # Rank 5
    [10,  10,  10,  10,  10,  10,  10,  10],  # Rank 6
    [10,  10,  10,  10,  10,  10,  10,  10],  # Rank 7
    [0,   0,   0,   0,   0,   0,   0,   0]    # Rank 8
]

# Knight PST - encourage center control and outposts
PST_KNIGHT_OPENING = [
    [-50, -40, -30, -30, -30, -30, -40, -50],  # Rank 1
    [-40, -20, 0,   0,   0,   0,   -20, -40],  # Rank 2
    [-30, 0,   10,  15,  15,  10,  0,   -30],  # Rank 3
    [-30, 5,   15,  20,  20,  15,  5,   -30],  # Rank 4
    [-30, 0,   15,  20,  20,  15,  0,   -30],  # Rank 5
    [-30, 5,   10,  15,  15,  10,  5,   -30],  # Rank 6
    [-40, -20, 0,   5,   5,   0,   -20, -40],  # Rank 7
    [-50, -40, -30, -30, -30, -30, -40, -50]   # Rank 8
]

PST_KNIGHT_ENDGAME = [
    [-50, -40, -30, -30, -30, -30, -40, -50],  # Rank 1
    [-40, -20, 0,   0,   0,   0,   -20, -40],  # Rank 2
    [-30, 0,   10,  15,  15,  10,  0,   -30],  # Rank 3
    [-30, 5,   15,  20,  20,  15,  5,   -30],  # Rank 4
    [-30, 0,   15,  20,  20,  15,  0,   -30],  # Rank 5
    [-30, 5,   10,  15,  15,  10,  5,   -30],  # Rank 6
    [-40, -20, 0,   5,   5,   0,   -20, -40],  # Rank 7
    [-50, -40, -30, -30, -30, -30, -40, -50]   # Rank 8
]

# Bishop PST - encourage long diagonals and center control
PST_BISHOP_OPENING = [
    [-20, -10, -10, -10, -10, -10, -10, -20],  # Rank 1
    [-10, 0,   0,   0,   0,   0,   0,   -10],  # Rank 2
    [-10, 0,   5,   10,  10,  5,   0,   -10],  # Rank 3
    [-10, 5,   5,   10,  10,  5,   5,   -10],  # Rank 4
    [-10, 0,   10,  10,  10,  10,  0,   -10],  # Rank 5
    [-10, 10,  10,  10,  10,  10,  10,  -10],  # Rank 6
    [-10, 5,   0,   0,   0,   0,   5,   -10],  # Rank 7
    [-20, -10, -10, -10, -10, -10, -10, -20]   # Rank 8
]

PST_BISHOP_ENDGAME = [
    [-20, -10, -10, -10, -10, -10, -10, -20],  # Rank 1
    [-10, 0,   0,   0,   0,   0,   0,   -10],  # Rank 2
    [-10, 0,   5,   10,  10,  5,   0,   -10],  # Rank 3
    [-10, 5,   5,   10,  10,  5,   5,   -10],  # Rank 4
    [-10, 0,   10,  10,  10,  10,  0,   -10],  # Rank 5
    [-10, 10,  10,  10,  10,  10,  10,  -10],  # Rank 6
    [-10, 5,   0,   0,   0,   0,   5,   -10],  # Rank 7
    [-20, -10, -10, -10, -10, -10, -10, -20]   # Rank 8
]

# Rook PST - encourage open files and 7th rank
PST_ROOK_OPENING = [
    [0,   0,   0,   0,   0,   0,   0,   0],    # Rank 1
    [5,   10,  10,  10,  10,  10,  10,  5],    # Rank 2
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 3
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 4
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 5
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 6
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 7
    [0,   0,   0,   5,   5,   0,   0,   0]     # Rank 8
]

PST_ROOK_ENDGAME = [
    [0,   0,   0,   0,   0,   0,   0,   0],    # Rank 1
    [5,   10,  10,  10,  10,  10,  10,  5],    # Rank 2
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 3
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 4
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 5
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 6
    [-5,  0,   0,   0,   0,   0,   0,   -5],   # Rank 7
    [0,   0,   0,   5,   5,   0,   0,   0]     # Rank 8
]

# Queen PST - encourage center control but avoid early development
PST_QUEEN_OPENING = [
    [-20, -10, -10, -5,  -5,  -10, -10, -20],  # Rank 1
    [-10, 0,   0,   0,   0,   0,   0,   -10],  # Rank 2
    [-10, 0,   5,   5,   5,   5,   0,   -10],  # Rank 3
    [-5,  0,   5,   5,   5,   5,   0,   -5],   # Rank 4
    [0,   0,   5,   5,   5,   5,   0,   -5],   # Rank 5
    [-10, 5,   5,   5,   5,   5,   0,   -10],  # Rank 6
    [-10, 0,   5,   0,   0,   0,   0,   -10],  # Rank 7
    [-20, -10, -10, -5,  -5,  -10, -10, -20]   # Rank 8
]

PST_QUEEN_ENDGAME = [
    [-20, -10, -10, -5,  -5,  -10, -10, -20],  # Rank 1
    [-10, 0,   0,   0,   0,   0,   0,   -10],  # Rank 2
    [-10, 0,   5,   5,   5,   5,   0,   -10],  # Rank 3
    [-5,  0,   5,   5,   5,   5,   0,   -5],   # Rank 4
    [-5,  0,   5,   5,   5,   5,   0,   -5],   # Rank 5
    [-10, 0,   5,   5,   5,   5,   0,   -10],  # Rank 6
    [-10, 0,   0,   0,   0,   0,   0,   -10],  # Rank 7
    [-20, -10, -10, -5,  -5,  -10, -10, -20]   # Rank 8
]

# King PST - encourage safety in opening, activity in endgame
PST_KING_OPENING = [
    [-30, -40, -40, -50, -50, -40, -40, -30],  # Rank 1
    [-30, -40, -40, -50, -50, -40, -40, -30],  # Rank 2
    [-30, -40, -40, -50, -50, -40, -40, -30],  # Rank 3
    [-30, -40, -40, -50, -50, -40, -40, -30],  # Rank 4
    [-20, -30, -30, -40, -40, -30, -30, -20],  # Rank 5
    [-10, -20, -20, -20, -20, -20, -20, -10],  # Rank 6
    [20,  20,  0,   0,   0,   0,   20,  20],   # Rank 7
    [20,  30,  10,  0,   0,   10,  30,  20]    # Rank 8 - encourage castling
]

PST_KING_ENDGAME = [
    [-50, -40, -30, -20, -20, -30, -40, -50],  # Rank 1 - center in endgame
    [-30, -20, -10, 0,   0,   -10, -20, -30],  # Rank 2
    [-30, -10, 20,  30,  30,  20,  -10, -30],  # Rank 3
    [-30, -10, 30,  40,  40,  30,  -10, -30],  # Rank 4
    [-30, -10, 30,  40,  40,  30,  -10, -30],  # Rank 5
    [-30, -10, 20,  30,  30,  20,  -10, -30],  # Rank 6
    [-30, -30, 0,   0,   0,   0,   -30, -30],  # Rank 7
    [-50, -30, -30, -30, -30, -30, -30, -50]   # Rank 8
]

# PST lookup dictionary for easy access
PST_OPENING = {
    chess.PAWN: PST_PAWN_OPENING,
    chess.KNIGHT: PST_KNIGHT_OPENING,
    chess.BISHOP: PST_BISHOP_OPENING,
    chess.ROOK: PST_ROOK_OPENING,
    chess.QUEEN: PST_QUEEN_OPENING,
    chess.KING: PST_KING_OPENING
}

PST_ENDGAME = {
    chess.PAWN: PST_PAWN_ENDGAME,
    chess.KNIGHT: PST_KNIGHT_ENDGAME,
    chess.BISHOP: PST_BISHOP_ENDGAME,
    chess.ROOK: PST_ROOK_ENDGAME,
    chess.QUEEN: PST_QUEEN_ENDGAME,
    chess.KING: PST_KING_ENDGAME
}

class NodeType(Enum):
    EXACT = 0
    LOWER_BOUND = 1
    UPPER_BOUND = 2

class GamePhase(Enum):
    """Game phase classification for phase-aware evaluation"""
    OPENING = 0      # Move < 6 AND material >= 5500 (conservative)
    MIDDLEGAME = 1   # Default phase (safer fallback)
    ENDGAME = 2      # Material <= 2000

@dataclass
class TTEntry:
    """Transposition table entry"""
    zobrist_key: int
    depth: int
    value: float
    node_type: NodeType
    best_move: Optional[chess.Move]
    age: int

class VPREngine:
    def __init__(self, max_depth: int = 6, tt_size_mb: int = 128):
        """
        Initialize the VPR engine
        
        Args:
            max_depth: Maximum search depth
            tt_size_mb: Transposition table size in MB
        """
        self.board = chess.Board()
        self.max_depth = max_depth
        self.start_time = 0
        self.time_limit = 0
        self.nodes_searched = 0
        self.age = 0
        
        # Transposition table
        self.tt_size = (tt_size_mb * 1024 * 1024) // 64  # Approximate entries
        self.transposition_table: Dict[int, TTEntry] = {}
        
        # Move ordering tables
        self.killer_moves: List[List[Optional[chess.Move]]] = [[None, None] for _ in range(64)]
        self.history_table: Dict[Tuple[chess.Square, chess.Square], int] = {}
        
        # Game phase cache
        self.phase_cache: Dict[int, GamePhase] = {}
        
        # Zobrist keys for hashing
        self._init_zobrist()
        
    def _init_zobrist(self):
        """Initialize Zobrist hashing keys"""
        random.seed(12345)  # Fixed seed for reproducibility
        self.zobrist_pieces = {}
        self.zobrist_castling = {}
        self.zobrist_en_passant = {}
        self.zobrist_side_to_move = random.getrandbits(64)
        
        # Piece-square zobrist keys
        for square in chess.SQUARES:
            for piece in chess.PIECE_TYPES:
                for color in chess.COLORS:
                    self.zobrist_pieces[(square, piece, color)] = random.getrandbits(64)
        
        # Castling rights
        for i in range(4):  # 4 castling rights (WK, WQ, BK, BQ)
            self.zobrist_castling[i] = random.getrandbits(64)
            
        # En passant file
        for file in range(8):
            self.zobrist_en_passant[file] = random.getrandbits(64)
    
    def _get_zobrist_key(self, board: chess.Board) -> int:
        """Calculate Zobrist hash for current position"""
        key = 0
        
        # Pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                key ^= self.zobrist_pieces[(square, piece.piece_type, piece.color)]
        
        # Side to move
        if board.turn == chess.BLACK:
            key ^= self.zobrist_side_to_move
            
        # Castling rights
        castling_key = 0
        if board.has_kingside_castling_rights(chess.WHITE):
            castling_key ^= self.zobrist_castling[0]
        if board.has_queenside_castling_rights(chess.WHITE):
            castling_key ^= self.zobrist_castling[1]
        if board.has_kingside_castling_rights(chess.BLACK):
            castling_key ^= self.zobrist_castling[2]
        if board.has_queenside_castling_rights(chess.BLACK):
            castling_key ^= self.zobrist_castling[3]
        key ^= castling_key
        
        # En passant
        if board.ep_square is not None:
            key ^= self.zobrist_en_passant[chess.square_file(board.ep_square)]
            
        return key
    
    def _detect_game_phase(self, board: chess.Board) -> GamePhase:
        """
        Detect current game phase using balanced thresholds
        
        Classification (balanced for VPR's lightweight architecture):
        - Opening: move < 12 AND material >= 4500 (realistic)
        - Endgame: material <= 2500 (clear endgame)
        - Middlegame: Default (safer fallback)
        
        Uses total material value for more accurate detection
        
        Args:
            board: Current chess position
            
        Returns:
            GamePhase enum value
        """
        zobrist_key = self._get_zobrist_key(board)
        
        # Check cache first
        if zobrist_key in self.phase_cache:
            return self.phase_cache[zobrist_key]
        
        # Calculate total material value (both sides)
        total_material = 0
        for piece_type in chess.PIECE_TYPES:
            if piece_type == chess.KING:
                continue
            piece_value = PIECE_VALUES.get(piece_type, 0)
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            total_material += (white_count + black_count) * piece_value
        
        moves_played = len(board.move_stack) if board.move_stack else (board.fullmove_number - 1) * 2 + (0 if board.turn == chess.WHITE else 1)
        
        # Balanced phase detection for VPR v8.1
        if moves_played < 12 and total_material >= 4500:
            # Realistic opening: first 11 moves AND 58% of material
            phase = GamePhase.OPENING
        elif total_material <= 2500:
            # Clear endgame: minimal material left
            phase = GamePhase.ENDGAME
        else:
            # Default to middlegame when uncertain (safer)
            phase = GamePhase.MIDDLEGAME
        
        # Cache result
        self.phase_cache[zobrist_key] = phase
        
        return phase
    
    def _is_time_up(self) -> bool:
        """Check if allocated time has been exceeded"""
        if self.time_limit <= 0:
            return False
        return time.time() - self.start_time >= self.time_limit
    
    def _calculate_time_limit(self, time_left: float, increment: float = 0) -> float:
        """
        Calculate time limit for this move based on remaining time and game phase
        
        Phase-aware time allocation:
        - Opening: Faster moves (50x divisor), less critical
        - Middlegame: Deeper thinking (30x divisor), tactical complexity
        - Endgame: Precise calculation (40x divisor), simpler positions
        
        Args:
            time_left: Time remaining in seconds
            increment: Time increment per move
            
        Returns:
            Time limit for this move in seconds (0 means no time limit)
        """
        if time_left <= 0:
            return 0  # No time limit when time_left is 0 or negative
        
        # Detect game phase for phase-aware time management
        phase = self._detect_game_phase(self.board)
        
        # Phase-dependent base divisor
        if phase == GamePhase.OPENING:
            base_divisor = 50  # Move faster in opening
        elif phase == GamePhase.MIDDLEGAME:
            base_divisor = 30  # Think longer in middlegame
        else:  # ENDGAME
            base_divisor = 40  # Precise but simpler positions
        
        # Apply time pressure adjustments
        if time_left > 1800:  # > 30 minutes
            return min(time_left / base_divisor + increment * 0.8, 30)
        elif time_left > 600:  # > 10 minutes  
            return min(time_left / (base_divisor * 0.9) + increment * 0.8, 20)
        elif time_left > 60:  # > 1 minute
            return min(time_left / (base_divisor * 0.7) + increment * 0.8, 10)
        else:  # < 1 minute
            return min(time_left / (base_divisor * 0.5) + increment * 0.8, 5)
    
    def _evaluate_material(self, board: chess.Board) -> int:
        """
        Evaluate position based on material balance with dynamic bishop evaluation
        
        Returns:
            Evaluation score in centipawns (positive = good for white)
        """
        score = 0
        
        white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
        black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
        
        for piece_type in chess.PIECE_TYPES:
            if piece_type == chess.KING:
                continue
                
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            
            if piece_type == chess.BISHOP:
                # Dynamic bishop evaluation
                white_bishop_value = PIECE_VALUES[chess.BISHOP]
                black_bishop_value = PIECE_VALUES[chess.BISHOP]
                
                if white_bishops == 2:
                    white_bishop_value += BISHOP_PAIR_BONUS // 2  # Split bonus between bishops
                elif white_bishops == 1:
                    white_bishop_value -= BISHOP_ALONE_PENALTY
                    
                if black_bishops == 2:
                    black_bishop_value += BISHOP_PAIR_BONUS // 2
                elif black_bishops == 1:
                    black_bishop_value -= BISHOP_ALONE_PENALTY
                    
                score += white_count * white_bishop_value - black_count * black_bishop_value
            else:
                piece_value = PIECE_VALUES[piece_type]
                score += white_count * piece_value - black_count * piece_value
        
        # Small bonus for piece count diversity (prefer pieces over pawns)
        white_pieces = sum(len(board.pieces(pt, chess.WHITE)) for pt in chess.PIECE_TYPES if pt != chess.KING)
        black_pieces = sum(len(board.pieces(pt, chess.BLACK)) for pt in chess.PIECE_TYPES if pt != chess.KING)
        score += (white_pieces - black_pieces) * 5
        
        return score if board.turn == chess.WHITE else -score
    
    def _evaluate_pst(self, board: chess.Board) -> int:
        """
        Evaluate position using piece-square tables (C0BR4-style).
        
        Interpolates between opening and endgame PST based on material remaining.
        This provides positional understanding and solves passive play issues.
        
        Returns:
            PST evaluation score in centipawns (positive = good for white)
        """
        # Calculate game phase (0.0 = opening, 1.0 = endgame)
        total_material = 0
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            count = len(board.pieces(piece_type, chess.WHITE)) + len(board.pieces(piece_type, chess.BLACK))
            total_material += count * PIECE_VALUES[piece_type]
        
        # Phase interpolation: 7800 = typical opening material, 2000 = endgame threshold
        phase = 1.0 - min(1.0, max(0.0, (total_material - 2000) / 5800))
        
        score = 0
        
        # Evaluate all pieces on the board
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.piece_type == chess.KING:
                continue
            
            # Get rank and file (0-7 indexed)
            rank = chess.square_rank(square)
            file = chess.square_file(square)
            
            # For black pieces, mirror the rank (black's rank 1 = index 7)
            if piece.color == chess.BLACK:
                rank = 7 - rank
            
            # Get opening and endgame values
            pst_opening = PST_OPENING.get(piece.piece_type, [[0]*8 for _ in range(8)])
            pst_endgame = PST_ENDGAME.get(piece.piece_type, [[0]*8 for _ in range(8)])
            
            opening_value = pst_opening[rank][file]
            endgame_value = pst_endgame[rank][file]
            
            # Interpolate between opening and endgame
            pst_value = int(opening_value * (1.0 - phase) + endgame_value * phase)
            
            # Add to score (positive for white, negative for black)
            if piece.color == chess.WHITE:
                score += pst_value
            else:
                score -= pst_value
        
        return score if board.turn == chess.WHITE else -score
    
    def _evaluate(self, board: chess.Board) -> int:
        """
        Complete position evaluation (C0BR4-style).
        
        Combines material and positional understanding for better play.
        This is the main evaluation function called by search.
        
        Returns:
            Total evaluation score in centipawns (positive = good for side to move)
        """
        material_score = self._evaluate_material(board)
        pst_score = self._evaluate_pst(board)
        
        # Combine material and positional scores
        total_score = material_score + pst_score
        
        return total_score
    
    def _quiescence_search(self, board: chess.Board, alpha: float, beta: float, depth: int = 0) -> float:
        """
        Quiescence search to avoid horizon effect on captures
        
        Args:
            board: Current position
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            depth: Current quiescence depth
            
        Returns:
            Evaluation score
        """
        if self._is_time_up() or depth > 8:  # Limit quiescence depth
            return self._evaluate(board)
            
        self.nodes_searched += 1
        stand_pat = self._evaluate(board)
        
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat
            
        # Generate and sort captures
        captures = []
        for move in board.legal_moves:
            if board.is_capture(move):
                captures.append((self._mvv_lva_score(board, move), move))
        
        captures.sort(key=lambda x: x[0], reverse=True)
        
        for _, move in captures:
            board.push(move)
            score = -self._quiescence_search(board, -beta, -alpha, depth + 1)
            board.pop()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
                
        return alpha
    
    def _mvv_lva_score(self, board: chess.Board, move: chess.Move) -> int:
        """Most Valuable Victim - Least Valuable Attacker scoring"""
        if not board.is_capture(move):
            return 0
            
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        
        if victim is None or attacker is None:
            return 0
            
        victim_value = PIECE_VALUES.get(victim.piece_type, 0)
        attacker_value = PIECE_VALUES.get(attacker.piece_type, 0)
        
        return victim_value * 10 - attacker_value
    
    def _static_exchange_evaluation(self, board: chess.Board, move: chess.Move) -> int:
        """
        Static Exchange Evaluation (SEE) - calculate material outcome of capture sequence
        
        Simulates all recaptures on the target square to determine the final material balance.
        This is the engine's tactical understanding of whether a capture is sound.
        
        Args:
            board: Current position
            move: Capture move to evaluate
            
        Returns:
            Net material gain/loss in centipawns (positive = we gain material)
            
        Examples:
            Queen takes rook protected by pawn: -400 (we lose queen for rook)
            Pawn takes pawn protected by nothing: +100 (we gain pawn)
            Rook takes bishop protected by knight: +25 (we gain bishop, lose rook)
        """
        if not board.is_capture(move):
            return 0
        
        # Get initial victim value
        victim = board.piece_at(move.to_square)
        if victim is None:
            victim_value = PIECE_VALUES[chess.PAWN]  # En passant
        else:
            victim_value = PIECE_VALUES[victim.piece_type]
        
        # Get attacker value
        attacker = board.piece_at(move.from_square)
        if attacker is None:
            return 0
        attacker_value = PIECE_VALUES[attacker.piece_type]
        
        # Make the capture
        board.push(move)
        target_square = move.to_square
        gain = [victim_value]
        
        # Simulate exchange sequence
        current_attacker_value = attacker_value
        
        while True:
            # Find smallest attacker that can recapture
            smallest_attacker = None
            smallest_value = float('inf')
            
            for recapture in board.legal_moves:
                if recapture.to_square == target_square:
                    piece = board.piece_at(recapture.from_square)
                    if piece:
                        piece_value = PIECE_VALUES.get(piece.piece_type, 0)
                        if piece_value < smallest_value:
                            smallest_value = piece_value
                            smallest_attacker = recapture
            
            if smallest_attacker is None:
                break
            
            gain.append(current_attacker_value)
            current_attacker_value = smallest_value
            board.push(smallest_attacker)
        
        # Restore board state
        for _ in range(len(gain) - 1):
            board.pop()
        board.pop()
        
        # Minimax the gain list to get final material balance
        if len(gain) == 1:
            return gain[0]
        
        for i in range(len(gain) - 1, 0, -1):
            gain[i - 1] = max(gain[i - 1] - gain[i], 0)
        
        return gain[0]
    
    def _evaluate_trade(self, board: chess.Board, move: chess.Move, phase: GamePhase) -> bool:
        """
        Evaluate if a capture is tactically sound based on game phase
        
        Different phases require different trade strategies:
        - Opening: Accept trades losing ≤1 pawn (simplification valuable)
        - Middlegame: Only advantageous trades (maximize material)
        - Endgame: Accept equal trades when ahead, be careful when behind
        
        Args:
            board: Current position
            move: Capture move to evaluate
            phase: Current game phase
            
        Returns:
            True if trade should be prioritized (good trade for this phase)
            
        Examples:
            Queen for 2 rooks (-100): Good in opening/endgame, bad in middlegame
            Rook for bishop+knight (0): Good in all phases
            Knight for 3 pawns (0): Good in all phases
            Queen for 3 pawns (-600): Bad in all phases
        """
        if not board.is_capture(move):
            return False
        
        # Calculate SEE to understand the trade
        see_value = self._static_exchange_evaluation(board, move)
        
        # Phase-dependent trade acceptance
        if phase == GamePhase.OPENING:
            # Opening: Accept trades losing up to 1 pawn
            # Rationale: Simplify position, reduce complexity, save time
            return see_value >= -100
            
        elif phase == GamePhase.MIDDLEGAME:
            # Middlegame: Only accept advantageous trades (strict)
            # Rationale: Critical tactical phase, maximize material edge
            return see_value >= 0
            
        else:  # ENDGAME
            # Endgame: Context-dependent (are we ahead or behind?)
            material_balance = self._evaluate_material(board)
            
            if material_balance > 200:  # We're ahead by 2+ pawns
                # Trade pieces to simplify (converting advantage)
                return see_value >= -50
            else:
                # Be careful when behind or equal
                return see_value >= 0
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move], ply: int, 
                    tt_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """
        Order moves for better alpha-beta pruning (C0BR4-style hierarchy)
        
        Priority (v9.0 - C0BR4 port):
        1. TT move (1,000,000)
        2. Captures via MVV-LVA (10,000 + victim - attacker)
        3. Promotions (9,000 + promoted piece value)
        4. Checks (500)
        5. Center control (10)
        6. Development (5)
        7. History heuristic (variable)
        
        This simpler hierarchy encourages forward play and solves rook shuffling.
        """
        scored_moves = []
        
        for move in moves:
            # TT move gets highest priority
            if tt_move and move == tt_move:
                score = 1000000
            else:
                score = self._score_move_c0br4_style(board, move, ply)
                
            scored_moves.append((score, move))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in scored_moves]
    
    def _score_move_c0br4_style(self, board: chess.Board, move: chess.Move, ply: int) -> int:
        """
        Score a move using C0BR4's proven hierarchy.
        
        This method implements the exact move ordering that makes C0BR4 successful:
        - Captures valued by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
        - Promotions highly valued (just below captures)
        - Checks get tactical priority
        - Small bonuses for center control and development (prevents shuffling)
        """
        # Captures: MVV-LVA scoring (10,000 + victim_value - attacker_value)
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            victim_value = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0
            attacker_value = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 100
            
            return 10000 + victim_value - attacker_value
        
        # Promotions: High value (9,000 + piece value)
        if move.promotion:
            return 9000 + PIECE_VALUES.get(move.promotion, 0)
        
        # Checks: Tactical priority
        if board.gives_check(move):
            return 500
        
        # Positional bonuses (center control, development)
        score = 0
        
        # Center control bonus (e4, d4, e5, d5 for white; similar for black)
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        if move.to_square in center_squares:
            score += 10
        
        # Development bonus (moving pieces from back rank)
        from_rank = chess.square_rank(move.from_square)
        if board.turn == chess.WHITE and from_rank == 0:
            score += 5
        elif board.turn == chess.BLACK and from_rank == 7:
            score += 5
        
        # History heuristic for remaining moves
        key = (move.from_square, move.to_square)
        score += self.history_table.get(key, 0)
        
        return score
    
    def _update_killer_moves(self, move: chess.Move, ply: int):
        """Update killer moves table"""
        if ply < len(self.killer_moves):
            if self.killer_moves[ply][0] != move:
                self.killer_moves[ply][1] = self.killer_moves[ply][0]
                self.killer_moves[ply][0] = move
    
    def _update_history(self, move: chess.Move, depth: int):
        """Update history heuristic table"""
        key = (move.from_square, move.to_square)
        self.history_table[key] = self.history_table.get(key, 0) + depth * depth
    
    def _store_tt_entry(self, zobrist_key: int, depth: int, value: float, 
                       node_type: NodeType, best_move: Optional[chess.Move]):
        """Store entry in transposition table"""
        if len(self.transposition_table) >= self.tt_size:
            # Simple replacement: remove oldest entries
            old_keys = [k for k, v in self.transposition_table.items() if v.age < self.age - 2]
            for key in old_keys[:len(old_keys)//2]:  # Remove half of old entries
                del self.transposition_table[key]
        
        self.transposition_table[zobrist_key] = TTEntry(
            zobrist_key, depth, value, node_type, best_move, self.age
        )
    
    def _probe_tt(self, zobrist_key: int, depth: int, alpha: float, beta: float) -> Tuple[Optional[float], Optional[chess.Move]]:
        """Probe transposition table"""
        entry = self.transposition_table.get(zobrist_key)
        if entry is None or entry.depth < depth:
            return None, entry.best_move if entry else None
            
        if entry.node_type == NodeType.EXACT:
            return entry.value, entry.best_move
        elif entry.node_type == NodeType.LOWER_BOUND and entry.value >= beta:
            return entry.value, entry.best_move
        elif entry.node_type == NodeType.UPPER_BOUND and entry.value <= alpha:
            return entry.value, entry.best_move
            
        return None, entry.best_move
    
    def _search(self, board: chess.Board, depth: int, alpha: float, beta: float, 
               ply: int, do_null_move: bool = True) -> Tuple[float, Optional[chess.Move]]:
        """
        Main minimax search with alpha-beta pruning
        
        Args:
            board: Current position
            depth: Remaining search depth  
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            ply: Current ply from root
            do_null_move: Whether null move pruning is allowed
            
        Returns:
            Tuple of (evaluation, best_move)
        """
        if self._is_time_up():
            return self._evaluate(board), None
            
        # Check for terminal nodes
        if board.is_game_over():
            if board.is_checkmate():
                return -30000 + ply, None  # Prefer quicker mates
            else:
                return 0, None  # Draw
        
        if depth <= 0:
            return self._quiescence_search(board, alpha, beta), None
            
        self.nodes_searched += 1
        zobrist_key = self._get_zobrist_key(board)
        original_alpha = alpha
        
        # Transposition table lookup
        tt_value, tt_move = self._probe_tt(zobrist_key, depth, alpha, beta)
        if tt_value is not None:
            return tt_value, tt_move
        
        # Null move pruning
        if (do_null_move and depth >= 3 and not board.is_check() and 
            self._evaluate(board) >= beta):
            
            board.push(chess.Move.null())
            null_score, _ = self._search(board, depth - 3, -beta, -beta + 1, ply + 1, False)
            null_score = -null_score
            board.pop()
            
            if null_score >= beta:
                return beta, None
        
        # Generate and order moves
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return self._evaluate(board), None
            
        ordered_moves = self._order_moves(board, legal_moves, ply, tt_move)
        best_move = None
        best_value = -float('inf')
        current_pv = []
        
        for i, move in enumerate(ordered_moves):
            board.push(move)
            
            # Create new PV for this line
            child_pv = []
            
            # Use principal variation search for moves after the first
            if i == 0:
                value, _ = self._search(board, depth - 1, -beta, -alpha, ply + 1, True)
                value = -value
            else:
                # Search with null window
                value, _ = self._search(board, depth - 1, -alpha - 1, -alpha, ply + 1, True)
                value = -value
                
                # Re-search if necessary
                if alpha < value < beta:
                    child_pv = []  # Reset PV for re-search
                    value, _ = self._search(board, depth - 1, -beta, -alpha, ply + 1, True)
                    value = -value
            
            board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
                # Update principal variation - collect it properly
                if ply == 0:  # Only collect PV at root
                    current_pv = [move] + child_pv[:7]  # Limit PV length to 8 moves total
                
            if value > alpha:
                alpha = value
                
            if alpha >= beta:
                # Beta cutoff - update tables
                if not board.is_capture(move):
                    self._update_killer_moves(move, ply)
                    self._update_history(move, depth)
                break
        
        # Store in transposition table
        if best_value <= original_alpha:
            node_type = NodeType.UPPER_BOUND
        elif best_value >= beta:
            node_type = NodeType.LOWER_BOUND
        else:
            node_type = NodeType.EXACT
            
        self._store_tt_entry(zobrist_key, depth, best_value, node_type, best_move)
        
        return best_value, best_move
    
    def _extract_pv_from_tt(self, board: chess.Board, depth: int) -> List[chess.Move]:
        """Extract principal variation from transposition table"""
        pv = []
        current_board = board.copy()
        
        for _ in range(min(depth, 8)):  # Limit PV length
            zobrist_key = self._get_zobrist_key(current_board)
            entry = self.transposition_table.get(zobrist_key)
            
            if entry is None or entry.best_move is None:
                break
                
            move = entry.best_move
            if move not in current_board.legal_moves:
                break
                
            pv.append(move)
            current_board.push(move)
            
        return pv
    
    def get_best_move(self, time_left: float = 0, increment: float = 0) -> Optional[chess.Move]:
        """
        Find the best move using iterative deepening
        
        Args:
            time_left: Time remaining in seconds
            increment: Time increment per move
            
        Returns:
            Best move found
        """
        if self.board.is_game_over():
            return None
            
        self.start_time = time.time()
        self.time_limit = self._calculate_time_limit(time_left, increment)
        self.nodes_searched = 0
        self.age += 1
        
        best_move = None
        best_value = -float('inf')
        
        # Iterative deepening
        for depth in range(1, self.max_depth + 1):
            if self._is_time_up():
                break
                
            search_start = time.time()
            value, move = self._search(self.board, depth, -float('inf'), float('inf'), 0, True)
            search_time = time.time() - search_start
            
            if move is not None:
                best_move = move
                best_value = value
                
                # Extract PV from transposition table (more reliable)
                pv = self._extract_pv_from_tt(self.board, depth)
                pv_string = " ".join([m.uci() for m in pv]) if pv else move.uci()
                
                # Output search info with full PV
                nps = int(self.nodes_searched / max(search_time, 0.001))
                total_search_time = time.time() - self.start_time
                print(f"info depth {depth} score cp {int(value)} nodes {self.nodes_searched} "
                      f"nps {nps} time {int(total_search_time * 1000)} pv {pv_string}")
                sys.stdout.flush()  # Ensure each depth update is immediately visible
                
            if self._is_time_up():
                break
        
        total_time = time.time() - self.start_time
        print(f"info string Search completed in {total_time:.3f}s, {self.nodes_searched} nodes")
        sys.stdout.flush()  # Ensure completion message is visible
        
        return best_move

class UCIInterface:
    """UCI interface for VPR engine"""
    
    def __init__(self):
        self.engine = VPREngine()
        
    def run(self):
        """Main UCI loop"""
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                    
                if line == "uci":
                    print("id name VPR v9.0")
                    print("id author Pat Snyder")
                    print("option name MaxDepth type spin default 6 min 1 max 20")
                    print("option name TTSize type spin default 128 min 16 max 1024")
                    print("uciok")
                    sys.stdout.flush()  # Ensure output is immediately visible
                    
                elif line == "isready":
                    print("readyok")
                    sys.stdout.flush()  # Ensure output is immediately visible
                    
                elif line == "ucinewgame":
                    self.engine = VPREngine(self.engine.max_depth)
                    
                elif line.startswith("setoption"):
                    self._handle_setoption(line)
                    
                elif line.startswith("position"):
                    self._handle_position(line)
                    
                elif line.startswith("go"):
                    self._handle_go(line)
                    
                elif line == "quit":
                    break
                    
            except EOFError:
                break
            except Exception as e:
                print(f"info string Error: {e}", file=sys.stderr)
                sys.stderr.flush()  # Ensure error messages are visible
    
    def _handle_setoption(self, line: str):
        """Handle UCI setoption command"""
        parts = line.split()
        if len(parts) >= 5 and parts[1] == "name" and parts[3] == "value":
            name = parts[2]
            value = parts[4]
            
            if name == "MaxDepth":
                self.engine.max_depth = max(1, min(20, int(value)))
            elif name == "TTSize":
                tt_size = max(16, min(1024, int(value)))
                self.engine = VPREngine(self.engine.max_depth, tt_size)
    
    def _handle_position(self, line: str):
        """Handle UCI position command"""
        parts = line.split()
        if parts[1] == "startpos":
            self.engine.board = chess.Board()
            moves_idx = 3 if len(parts) > 3 and parts[2] == "moves" else None
        else:  # position fen ...
            fen_parts = []
            i = 2
            while i < len(parts) and parts[i] != "moves":
                fen_parts.append(parts[i])
                i += 1
            self.engine.board = chess.Board(" ".join(fen_parts))
            moves_idx = i + 1 if i < len(parts) - 1 and parts[i] == "moves" else None
        
        if moves_idx:
            for move_str in parts[moves_idx:]:
                move = chess.Move.from_uci(move_str)
                self.engine.board.push(move)
    
    def _handle_go(self, line: str):
        """Handle UCI go command"""
        parts = line.split()
        time_left = 0
        increment = 0
        depth_override = None
        
        # Parse time controls
        for i, part in enumerate(parts):
            if part == "wtime" and self.engine.board.turn == chess.WHITE:
                time_left = float(parts[i + 1]) / 1000  # Convert ms to seconds
            elif part == "btime" and self.engine.board.turn == chess.BLACK:
                time_left = float(parts[i + 1]) / 1000
            elif part == "winc" and self.engine.board.turn == chess.WHITE:
                increment = float(parts[i + 1]) / 1000
            elif part == "binc" and self.engine.board.turn == chess.BLACK:
                increment = float(parts[i + 1]) / 1000
            elif part == "depth":
                # Override max depth for this search only
                depth_override = int(parts[i + 1])
                time_left = 0  # No time limit when depth is specified
        
        # Use depth override without permanently changing engine settings
        if depth_override:
            # Temporarily store original max_depth
            original_max_depth = self.engine.max_depth
            self.engine.max_depth = depth_override
            move = self.engine.get_best_move(time_left=0, increment=0)
            # Restore original max_depth
            self.engine.max_depth = original_max_depth
        else:
            move = self.engine.get_best_move(time_left, increment)
        
        print(f"bestmove {move.uci() if move else '0000'}")
        sys.stdout.flush()  # Ensure bestmove is immediately visible

if __name__ == "__main__":
    engine = UCIInterface()
    engine.run()
