#!/usr/bin/env python3
"""
Capture Opponent - The Strategic Simplifier

This engine has one obsessive goal: remove as much material from the board as possible.
It will trade pieces aggressively, accepting up to -1 material disadvantage to force
simplifications. This creates a unique challenge for opponents - any hanging piece or
tactical tension will be immediately exploited.

Philosophy:
- Custom piece values: Pawn=2, Knight=4, Bishop=3, Rook=5, Queen=8
- Evaluates positions by TOTAL material on board (lower is better)
- Uses Static Exchange Evaluation (SEE) for multi-move capture sequences
- Accepts trades losing up to -1 material if it removes pieces
- Will trade queen for queen (perfect!), knight for 2 pawns (acceptable)
- Will NOT trade queen for 2 pawns (-4 material, too uneven)
- Prioritizes captures over all other moves (except checkmate)
- No endgame knowledge beyond checkmate detection

This engine will:
- Punish hanging pieces mercilessly
- Force concrete calculations from opponents
- Create simplified positions rapidly
- Challenge opponents to defend accurately
- Accept draws by insufficient material as success

Strategy: "If it can be taken, it WILL be taken" - The Capture Opponent

Standalone version - all template code embedded for independence.
"""

import sys
import chess
import random
import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# BASE TEMPLATE CODE (embedded for standalone operation)
# ============================================================================

# Approximate piece values for move ordering
# Used internally by MVV-LVA even for non-material engines
MOVE_ORDERING_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

# Search and evaluation constants - can be customized
MAX_QUIESCENCE_DEPTH = 8
MATE_SCORE = 30000
CHECKMATE_BONUS = 900000
CHECK_BONUS = 500000
CAPTURE_BONUS = 400000
KILLER_BONUS = 300000
PROMOTION_BONUS = 200000
PAWN_ADVANCE_BONUS = 100000

class NodeType(Enum):
    EXACT = 0
    LOWER_BOUND = 1
    UPPER_BOUND = 2

@dataclass
class TTEntry:
    """Transposition table entry"""
    zobrist_key: int
    depth: int
    value: float
    node_type: NodeType
    best_move: Optional[chess.Move]
    age: int

class ChessEngineTemplate:
    """
    Base chess engine template with complete search infrastructure.
    
    This class provides all the necessary components for a functional chess engine:
    - Complete search algorithm (minimax with alpha-beta)
    - Move ordering and pruning techniques
    - Transposition table management
    - Time management
    - UCI protocol support
    
    CUSTOMIZATION GUIDE:
    ====================
    
    REQUIRED Override:
    ------------------
    - _evaluate_position(): Your main evaluation function
    
    OPTIONAL Overrides (for specialized engines):
    ---------------------------------------------
    - _get_approximate_piece_value(): Custom values for move ordering
    - _quiescence_search(): Custom quiescence behavior
    - _order_moves(): Custom move ordering logic
    - _calculate_time_limit(): Custom time management
    
    DO NOT Override (unless you know what you're doing):
    ---------------------------------------------------
    - _search(): Core search algorithm
    - _probe_tt() / _store_tt_entry(): Transposition table
    - _get_zobrist_key(): Position hashing
    - get_best_move(): Iterative deepening controller
    
    EVALUATION STRATEGIES:
    =====================
    
    Material-Based Engines:
    - Pass piece_values dict to constructor
    - Use _evaluate_material_simple() or create custom material eval
    
    Positional Engines (PSTs):
    - Don't pass piece_values (will be None)
    - Override _evaluate_position() with PST lookup
    
    Mobility/Coverage Engines:
    - Don't pass piece_values
    - Override _evaluate_position() with dynamic calculation
    
    Hybrid Engines:
    - Combine multiple evaluation factors in _evaluate_position()
    """
    
    def __init__(self, max_depth: int = 2, tt_size_mb: int = 56, 
                 engine_name: str = "Capture Opponent v3.0", piece_values: Optional[Dict] = None):
        """
        Initialize the chess engine template
        
        Args:
            max_depth: Maximum search depth
            tt_size_mb: Transposition table size in MB
            engine_name: Name of the engine for UCI identification
            piece_values: Optional piece values dict (for material-based engines)
                         Pass None for positional/mobility-based engines
        """
        self.board = chess.Board()
        self.max_depth = max_depth
        self.engine_name = engine_name
        
        # piece_values is now truly optional - None for non-material engines
        self.piece_values = piece_values.copy() if piece_values else None
        
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
    
    def _is_time_up(self) -> bool:
        """Check if allocated time has been exceeded"""
        if self.time_limit <= 0:
            return False
        return time.time() - self.start_time >= self.time_limit
    
    def _calculate_time_limit(self, time_left: float, increment: float = 0) -> float:
        """
        Calculate time limit for this move based on remaining time
        
        Args:
            time_left: Time remaining in seconds
            increment: Time increment per move
            
        Returns:
            Time limit for this move in seconds (0 means no time limit)
        """
        if time_left <= 0:
            return 0  # No time limit when time_left is 0 or negative
            
        # Time management strategy
        if time_left > 1800:  # > 30 minutes
            return min(time_left / 40 + increment * 0.8, 30)
        elif time_left > 600:  # > 10 minutes  
            return min(time_left / 30 + increment * 0.8, 20)
        elif time_left > 60:  # > 1 minute
            return min(time_left / 20 + increment * 0.8, 10)
        else:  # < 1 minute
            return min(time_left / 10 + increment * 0.8, 5)
    
    def _get_approximate_piece_value(self, piece_type: int) -> int:
        """
        Get approximate piece value for move ordering (MVV-LVA, promotions)
        
        This is separate from evaluation and used internally for:
        - MVV-LVA capture ordering
        - Promotion move scoring
        - Other move ordering heuristics
        
        Can be overridden for custom move ordering behavior.
        
        Args:
            piece_type: chess.PAWN, chess.KNIGHT, etc.
            
        Returns:
            Approximate relative value (1-9 scale)
        """
        return MOVE_ORDERING_VALUES.get(piece_type, 0)
    
    def _evaluate_position(self, board: chess.Board) -> int:
        """
        Evaluate the current position - OVERRIDE THIS METHOD IN SUBCLASSES
        
        This is the main evaluation function that defines your engine's strategy.
        The template provides a simple baseline that uses piece_values if available.
        
        OVERRIDE THIS for custom engines:
        - Material engines: Use piece counting with piece_values
        - Positional engines: Use piece-square tables
        - Mobility engines: Count legal moves, attacks
        - Hybrid engines: Combine multiple factors
        
        Args:
            board: Current chess position
            
        Returns:
            Evaluation score (positive = good for side to move)
            Units depend on your evaluation (centipawns, mobility points, etc.)
        """
        # Default: use material if piece_values provided, otherwise return 0
        if self.piece_values:
            return self._evaluate_material_simple(board)
        else:
            # Non-material engines must override this method
            return 0
    
    def _evaluate_material_simple(self, board: chess.Board) -> int:
        """
        Simple material balance evaluation (baseline implementation)
        
        Only works if piece_values is set. Useful for material-based engines.
        
        Returns:
            Evaluation score in centipawns (positive = good for white)
        """
        if not self.piece_values:
            return 0
            
        score = 0
        
        for piece_type in chess.PIECE_TYPES:
            if piece_type == chess.KING:
                continue
                
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            piece_value = self.piece_values[piece_type]
            score += (white_count - black_count) * piece_value
        
        return score if board.turn == chess.WHITE else -score
    
    def _evaluate_material_with_bishop_pairs(self, board: chess.Board) -> int:
        """
        Material evaluation with dynamic bishop pair evaluation (example implementation)
        Shows how to extend the basic evaluation with additional heuristics.
        
        Returns:
            Evaluation score in centipawns (positive = good for white)
        """
        if not self.piece_values:
            return 0
            
        score = 0
        bishop_pair_bonus = 50
        bishop_alone_penalty = 50
        
        white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
        black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
        
        for piece_type in chess.PIECE_TYPES:
            if piece_type == chess.KING:
                continue
                
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            
            if piece_type == chess.BISHOP:
                # Dynamic bishop evaluation
                white_bishop_value = self.piece_values[chess.BISHOP]
                black_bishop_value = self.piece_values[chess.BISHOP]
                
                if white_bishops == 2:
                    white_bishop_value += bishop_pair_bonus // 2
                elif white_bishops == 1:
                    white_bishop_value -= bishop_alone_penalty
                    
                if black_bishops == 2:
                    black_bishop_value += bishop_pair_bonus // 2
                elif black_bishops == 1:
                    black_bishop_value -= bishop_alone_penalty
                    
                score += white_count * white_bishop_value - black_count * black_bishop_value
            else:
                piece_value = self.piece_values[piece_type]
                score += white_count * piece_value - black_count * piece_value
        
        # Small bonus for piece count diversity (prefer pieces over pawns)
        white_pieces = sum(len(board.pieces(pt, chess.WHITE)) for pt in chess.PIECE_TYPES if pt != chess.KING)
        black_pieces = sum(len(board.pieces(pt, chess.BLACK)) for pt in chess.PIECE_TYPES if pt != chess.KING)
        score += (white_pieces - black_pieces) * 5
        
        return score if board.turn == chess.WHITE else -score
    
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
        if self._is_time_up() or depth > MAX_QUIESCENCE_DEPTH:
            return self._evaluate_position(board)
            
        self.nodes_searched += 1
        stand_pat = self._evaluate_position(board)
        
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
        """
        Most Valuable Victim - Least Valuable Attacker scoring
        
        Uses approximate piece values for move ordering.
        """
        if not board.is_capture(move):
            return 0
            
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        
        if victim is None or attacker is None:
            return 0
            
        victim_value = self._get_approximate_piece_value(victim.piece_type)
        attacker_value = self._get_approximate_piece_value(attacker.piece_type)
        
        return victim_value * 10 - attacker_value
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move], ply: int, 
                     tt_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """
        Order moves for better alpha-beta pruning
        
        Priority:
        1. TT move (from transposition table)
        2. Checkmate threats
        3. Checks  
        4. Captures (MVV-LVA)
        5. Killer moves
        6. Pawn advances/promotions
        7. History heuristic
        8. Other moves
        """
        scored_moves = []
        
        for move in moves:
            score = 0
            
            # TT move gets highest priority
            if tt_move and move == tt_move:
                score = 1000000
            # Checkmate threats
            elif board.gives_check(move):
                board.push(move)
                if board.is_checkmate():
                    score = CHECKMATE_BONUS
                else:
                    score = CHECK_BONUS  # Regular checks
                board.pop()
            # Captures
            elif board.is_capture(move):
                score = CAPTURE_BONUS + self._mvv_lva_score(board, move)
            # Killer moves
            elif ply < len(self.killer_moves) and move in self.killer_moves[ply]:
                score = KILLER_BONUS
            # Pawn promotions
            elif move.promotion:
                score = PROMOTION_BONUS + self._get_approximate_piece_value(move.promotion)
            # Pawn advances (towards 7th/2nd rank)
            else:
                piece = board.piece_at(move.from_square)
                if piece and piece.piece_type == chess.PAWN:
                    to_rank = chess.square_rank(move.to_square)
                    if board.turn == chess.WHITE and to_rank >= 5:
                        score = PAWN_ADVANCE_BONUS + to_rank * 1000
                    elif board.turn == chess.BLACK and to_rank <= 2:
                        score = PAWN_ADVANCE_BONUS + (7 - to_rank) * 1000
                else:
                    # History heuristic for other moves
                    key = (move.from_square, move.to_square)
                    score = self.history_table.get(key, 0)
                
            scored_moves.append((score, move))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in scored_moves]
    
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
            return self._evaluate_position(board), None
            
        # Check for terminal nodes
        if board.is_game_over():
            if board.is_checkmate():
                return -MATE_SCORE + ply, None  # Prefer quicker mates
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
            self._evaluate_position(board) >= beta):
            
            board.push(chess.Move.null())
            null_score, _ = self._search(board, depth - 3, -beta, -beta + 1, ply + 1, False)
            null_score = -null_score
            board.pop()
            
            if null_score >= beta:
                return beta, None
        
        # Generate and order moves
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return self._evaluate_position(board), None
            
        ordered_moves = self._order_moves(board, legal_moves, ply, tt_move)
        best_move = None
        best_value = -float('inf')
        
        for i, move in enumerate(ordered_moves):
            board.push(move)
            
            # Use principal variation search for moves after the first
            if i == 0:
                value, _ = self._search(board, depth - 1, -beta, -alpha, ply + 1)
                value = -value
            else:
                # Search with null window
                value, _ = self._search(board, depth - 1, -alpha - 1, -alpha, ply + 1)
                value = -value
                
                # Re-search if necessary
                if alpha < value < beta:
                    value, _ = self._search(board, depth - 1, -beta, -alpha, ply + 1)
                    value = -value
            
            board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
                
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
            value, move = self._search(self.board, depth, -float('inf'), float('inf'), 0)
            search_time = time.time() - search_start
            
            if move is not None:
                best_move = move
                best_value = value
                
                # Output search info with flush for UCI output persistence
                nps = int(self.nodes_searched / max(search_time, 0.001))
                print(f"info depth {depth} score cp {value} nodes {self.nodes_searched} "
                      f"nps {nps} time {int(search_time * 1000)} pv {move.uci()}")
                sys.stdout.flush()  # Ensure output is visible immediately
                
            if self._is_time_up():
                break
        
        total_time = time.time() - self.start_time
        print(f"info string Search completed in {total_time:.3f}s, {self.nodes_searched} nodes")
        sys.stdout.flush()  # Ensure final message is visible
        
        return best_move


class UCIEngineInterface:
    """
    UCI interface for chess engines built on ChessEngineTemplate
    
    Handles all UCI protocol communication and works with any engine type:
    - Material-based engines (with piece_values)
    - Positional engines (PST-based)
    - Mobility/Coverage engines
    - Hybrid engines
    """
    
    def __init__(self, engine_class=None, **engine_kwargs):
        """
        Initialize UCI interface with a chess engine
        
        Args:
            engine_class: Class to instantiate (defaults to ChessEngineTemplate)
            **engine_kwargs: Additional arguments passed to engine constructor
        """
        if engine_class is None:
            engine_class = ChessEngineTemplate
        self.engine = engine_class(**engine_kwargs)
        
    def run(self):
        """Main UCI loop"""
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                    
                if line == "uci":
                    print(f"id name {self.engine.engine_name}")
                    print("id author OpponentEngine")
                    print("option name MaxDepth type spin default 6 min 1 max 20")
                    print("option name TTSize type spin default 128 min 16 max 1024")
                    print("uciok")
                    sys.stdout.flush()
                    
                elif line == "isready":
                    print("readyok")
                    sys.stdout.flush()
                    
                elif line == "ucinewgame":
                    # Recreate engine with same parameters
                    engine_class = type(self.engine)
                    kwargs = {
                        'max_depth': self.engine.max_depth,
                    }
                    # Only include piece_values if the engine has it
                    if hasattr(self.engine, 'piece_values') and self.engine.piece_values is not None:
                        kwargs['piece_values'] = self.engine.piece_values.copy()
                    
                    self.engine = engine_class(**kwargs)
                    
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
                sys.stderr.flush()
    
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
                engine_class = type(self.engine)
                kwargs = {
                    'max_depth': self.engine.max_depth,
                    'tt_size_mb': tt_size,
                }
                # Only include piece_values if the engine has it
                if hasattr(self.engine, 'piece_values') and self.engine.piece_values is not None:
                    kwargs['piece_values'] = self.engine.piece_values.copy()
                    
                self.engine = engine_class(**kwargs)
    
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
        original_depth = None
        
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
                original_depth = self.engine.max_depth
                self.engine.max_depth = depth_override
                time_left = 0  # No time limit when depth is specified
        
        # Find best move
        if depth_override:
            move = self.engine.get_best_move(time_left=0, increment=0)
            # Restore original depth
            if original_depth is not None:
                self.engine.max_depth = original_depth
        else:
            move = self.engine.get_best_move(time_left, increment)
            
        print(f"bestmove {move.uci() if move else '0000'}")
        sys.stdout.flush()


# ============================================================================
# CAPTURE OPPONENT IMPLEMENTATION
# ============================================================================

# Simple piece values for counting total material
CAPTURE_PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

# Evaluation constants - RADICALLY SIMPLIFIED
MATERIAL_REDUCTION_MULTIPLIER = 10000  # Huge reward for reducing total material
CAPTURE_AVAILABLE_BONUS = 50000  # Massive bonus just for having captures
NO_CAPTURE_PENALTY = 100000  # Catastrophic penalty for no captures
CHECKMATE_BONUS = 999999


class CaptureOpponent(ChessEngineTemplate):
    """
    An engine obsessed with clearing the board of material - ULTRA AGGRESSIVE VERSION.
    
    Philosophy: Trade EVERYTHING. Any capture is a good capture.
    Goal: Reduce total material on board to create insufficient material draws.
    Strategy: Non-stop attacking, relentless trading, board disruption.
    """
    
    def __init__(self, **kwargs):
        kwargs.setdefault('engine_name', 'Capture Opponent v2.0')
        kwargs.setdefault('piece_values', CAPTURE_PIECE_VALUES.copy())
        kwargs.setdefault('max_depth', 2)
        super().__init__(**kwargs)
        
        assert self.piece_values is not None, "Capture Opponent requires piece_values"
        
        # Track starting material to measure reduction
        self.starting_material = self._calculate_total_material(chess.Board())
    
    def _calculate_total_material(self, board: chess.Board) -> int:
        """Calculate total material on the board (both sides combined)"""
        assert self.piece_values is not None
        total = 0
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            total += (white_count + black_count) * self.piece_values[piece_type]
        return total
    
    def _calculate_material_balance(self, board: chess.Board) -> int:
        """Calculate material balance (our advantage)"""
        assert self.piece_values is not None
        our_material = 0
        their_material = 0
        
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            our_count = len(board.pieces(piece_type, board.turn))
            their_count = len(board.pieces(piece_type, not board.turn))
            piece_value = self.piece_values[piece_type]
            our_material += our_count * piece_value
            their_material += their_count * piece_value
        
        return our_material - their_material
    
    # No complex trade evaluation needed - ALL captures are good captures!
    
    def _evaluate_position(self, board: chess.Board) -> int:
        """
        FIXED evaluation: Reward IMMEDIATE captures and LOW material.
        
        The key insight: We return a score from OUR perspective (side to move).
        Higher score = better for us. So we want HIGH scores when material is LOW.
        """
        # Check for checkmate - we WIN or LOSE
        if board.is_checkmate():
            return -CHECKMATE_BONUS  # We're checkmated - BAD
        
        # Stalemate or insufficient material = SUCCESS! (we cleared the board)
        if board.is_stalemate() or board.is_insufficient_material():
            return CHECKMATE_BONUS // 2
        
        # Calculate TOTAL material on board (both sides combined)
        total_material = self._calculate_total_material(board)
        
        # PRIMARY GOAL: LOWER total material = HIGHER score
        # Starting material ~78, we want to get to 0
        # So score = (starting - current) * multiplier
        material_reduction = self.starting_material - total_material
        score = material_reduction * MATERIAL_REDUCTION_MULTIPLIER
        
        # SECONDARY GOAL: Have captures available RIGHT NOW
        capture_moves = [m for m in board.legal_moves if board.is_capture(m)]
        
        if len(capture_moves) > 0:
            # HUGE reward for having captures
            score += CAPTURE_AVAILABLE_BONUS
            # Each additional capture is valuable
            score += len(capture_moves) * 10000
        else:
            # MASSIVE penalty if we can't capture anything
            score -= NO_CAPTURE_PENALTY
        
        # Don't flip the sign - score is already from our perspective
        return score
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move], ply: int,
                     tt_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """
        CAPTURES FIRST, ALWAYS. Everything else is secondary.
        """
        captures = []
        non_captures = []
        
        for move in moves:
            if board.is_capture(move):
                # Score captures by victim value (higher value victims first)
                victim = board.piece_at(move.to_square)
                if victim:
                    victim_value = self._get_approximate_piece_value(victim.piece_type)
                else:
                    victim_value = 1  # En passant
                captures.append((victim_value, move))
            else:
                non_captures.append(move)
        
        # Sort captures by victim value (take the most valuable pieces first)
        captures.sort(key=lambda x: x[0], reverse=True)
        
        # Return ALL captures first, then everything else
        return [move for _, move in captures] + non_captures
    
    def get_best_move(self, time_left: float = 0, increment: float = 0) -> Optional[chess.Move]:
        """Find the best move (most likely a capture!)"""
        # Update starting material if this is a new game
        if self.board.fullmove_number == 1 and self.board.turn == chess.WHITE:
            self.starting_material = self._calculate_total_material(self.board)
        
        return super().get_best_move(time_left, increment)


def main():
    """Run the Capture Opponent engine with UCI interface"""
    interface = UCIEngineInterface(
        engine_class=CaptureOpponent,
        max_depth=2,
        tt_size_mb=256
    )
    
    print("info string Capture Opponent v2.0 - ULTRA AGGRESSIVE", file=sys.stderr)
    print("info string Goal: Trade EVERYTHING. Reduce total material to zero.", file=sys.stderr)
    print("info string Strategy: ANY capture is good. No material balance checks.", file=sys.stderr)
    print("info string Philosophy: Board disruption through relentless trading.", file=sys.stderr)
    sys.stderr.flush()
    
    interface.run()


if __name__ == "__main__":
    main()
