#!/usr/bin/env python3
"""
Coverage Opponent Chess Engine
A UCI-compatible chess engine that uses piece mobility and coverage for evaluation.

This engine evaluates positions based on piece "opportunity value" - the number of
legal moves each piece has plus bonuses for attacking occupied squares. It has no
understanding of traditional material values and makes all decisions based on:
- Piece mobility (number of legal squares)
- Attack coverage (threats on occupied squares)

Key Concept: A piece's value = mobility + occupied square attacks
- Mobile, active pieces are highly valued
- Pieces attacking enemy pieces get bonuses
- No static material or positional knowledge

This creates a hyperactive, mobility-focused playing style that can sacrifice
traditional material for active piece play and board control.
"""

import sys
import chess
import random
import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Search and evaluation constants - can be customized
MAX_QUIESCENCE_DEPTH = 8
MATE_SCORE = 30000
CHECKMATE_BONUS = 900000
CHECK_BONUS = 500000
CAPTURE_BONUS = 400000
KILLER_BONUS = 300000
PROMOTION_BONUS = 200000
PAWN_ADVANCE_BONUS = 100000

# Coverage evaluation constants
MOBILITY_VALUE = 1      # +1 per legal square
OCCUPIED_ATTACK_BONUS = 1  # +1 for attacking occupied square

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

class CoverageOpponent:
    """
    Coverage-based chess engine using piece mobility and attack opportunities.
    
    This engine evaluates positions based entirely on piece activity:
    - Mobility: Each legal square a piece can move to adds value
    - Attack coverage: Pieces attacking occupied squares get bonuses
    - No traditional material understanding
    
    The result is a hyperactive, mobility-driven playing style that values
    piece activity over traditional material considerations.
    """
    
    def __init__(self, max_depth: int = 6, tt_size_mb: int = 128):
        """
        Initialize the coverage chess engine
        
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
    
    def _calculate_piece_coverage(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> int:
        """
        Calculate the opportunity value of a piece based on mobility and attacks
        
        Args:
            board: Current position
            square: Square the piece is on
            piece: The piece to evaluate
            
        Returns:
            Opportunity value (mobility + occupied attack bonuses)
        """
        coverage_value = 0
        
        # Get all squares this piece attacks/can move to
        attacks = board.attacks(square)
        
        for target_square in attacks:
            # +1 for each square the piece can move to (mobility)
            coverage_value += MOBILITY_VALUE
            
            # +1 bonus if attacking an occupied square (threat value)
            target_piece = board.piece_at(target_square)
            if target_piece is not None:
                coverage_value += OCCUPIED_ATTACK_BONUS
        
        return coverage_value
    
    def _evaluate_position(self, board: chess.Board) -> int:
        """
        Evaluate position based on piece coverage and mobility
        
        No traditional material understanding - only opportunity values:
        - Each legal square a piece can move to: +1
        - Each occupied square a piece attacks: +1 bonus
        
        Args:
            board: Current chess position
            
        Returns:
            Evaluation score (positive = good for side to move)
        """
        white_coverage = 0
        black_coverage = 0
        
        # Calculate coverage for all pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_coverage = self._calculate_piece_coverage(board, square, piece)
                
                if piece.color == chess.WHITE:
                    white_coverage += piece_coverage
                else:
                    black_coverage += piece_coverage
        
        # Return score from perspective of side to move
        score = white_coverage - black_coverage
        return score if board.turn == chess.WHITE else -score
    
    def _evaluate_material_simple(self, board: chess.Board) -> int:
        """
        Fallback material evaluation for move ordering only
        Uses approximate values for MVV-LVA scoring
        """
        # Simple piece values for move ordering (not used in main evaluation)
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        score = 0
        for piece_type in chess.PIECE_TYPES:
            if piece_type == chess.KING:
                continue
                
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            piece_value = piece_values[piece_type]
            score += (white_count - black_count) * piece_value
        
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
        if self._is_time_up() or depth > MAX_QUIESCENCE_DEPTH:  # Limit quiescence depth
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
        Uses approximate piece values for move ordering only
        """
        if not board.is_capture(move):
            return 0
            
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        
        if victim is None or attacker is None:
            return 0
        
        # Approximate values for move ordering (not evaluation)
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        victim_value = piece_values.get(victim.piece_type, 0)
        attacker_value = piece_values.get(attacker.piece_type, 0)
        
        return victim_value * 10 - attacker_value
    
    def _order_moves(self, board: chess.Board, moves: List[chess.Move], ply: int, 
                     tt_move: Optional[chess.Move] = None) -> List[chess.Move]:
        """
        Order moves for better alpha-beta pruning
        
        Priority:
        1. TT move
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
                    score = 900000
                else:
                    score = 500000  # Regular checks
                board.pop()
            # Captures
            elif board.is_capture(move):
                score = 400000 + self._mvv_lva_score(board, move)
            # Killer moves
            elif ply < len(self.killer_moves) and move in self.killer_moves[ply]:
                score = 300000
            # Pawn promotions
            elif move.promotion:
                # Approximate promotion values for move ordering
                promo_values = {chess.QUEEN: 9, chess.ROOK: 5, chess.BISHOP: 3, chess.KNIGHT: 3}
                score = PROMOTION_BONUS + promo_values.get(move.promotion, 0)
            # Pawn advances (towards 7th/2nd rank)
            else:
                piece = board.piece_at(move.from_square)
                if piece and piece.piece_type == chess.PAWN:
                    to_rank = chess.square_rank(move.to_square)
                    if board.turn == chess.WHITE and to_rank >= 5:
                        score = 100000 + to_rank * 1000
                    elif board.turn == chess.BLACK and to_rank <= 2:
                        score = 100000 + (7 - to_rank) * 1000
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
                
                # Output search info with flush for persistence
                nps = int(self.nodes_searched / max(search_time, 0.001))
                print(f"info depth {depth} score cp {value} nodes {self.nodes_searched} "
                      f"nps {nps} time {int(search_time * 1000)} pv {move.uci()}")
                sys.stdout.flush()
                
            if self._is_time_up():
                break
        
        total_time = time.time() - self.start_time
        print(f"info string Search completed in {total_time:.3f}s, {self.nodes_searched} nodes")
        sys.stdout.flush()
        
        return best_move


class UCICoverageEngine:
    """UCI interface for the coverage chess engine"""
    
    def __init__(self):
        """Initialize UCI interface with coverage engine"""
        self.engine = CoverageOpponent()
        
    def run(self):
        """Main UCI loop"""
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                    
                if line == "uci":
                    print("id name Coverage Opponent v1.0")
                    print("id author OpponentEngine")
                    print("option name MaxDepth type spin default 6 min 1 max 20")
                    print("option name TTSize type spin default 128 min 16 max 1024")
                    print("uciok")
                    
                elif line == "isready":
                    print("readyok")
                    
                elif line == "ucinewgame":
                    self.engine = CoverageOpponent(
                        max_depth=self.engine.max_depth,
                        tt_size_mb=128
                    )
                    
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
                self.engine = CoverageOpponent(
                    max_depth=self.engine.max_depth,
                    tt_size_mb=tt_size
                )
    
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
                # Override max depth for this search and disable time management
                depth_override = int(parts[i + 1])
                # Store original depth to restore later
                original_depth = self.engine.max_depth
                self.engine.max_depth = depth_override
                time_left = 0  # No time limit when depth is specified
        
        # Find best move
        if depth_override:
            move = self.engine.get_best_move(time_left=0, increment=0)
            # Restore original depth
            self.engine.max_depth = original_depth
        else:
            move = self.engine.get_best_move(time_left, increment)
            
        print(f"bestmove {move.uci() if move else '0000'}")


# Main execution
if __name__ == "__main__":
    uci_engine = UCICoverageEngine()
    uci_engine.run()
