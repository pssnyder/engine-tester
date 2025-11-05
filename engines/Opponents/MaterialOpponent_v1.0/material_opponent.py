#!/usr/bin/env python3
"""
Material Opponent Chess Engine
A UCI-compatible chess engine using material balance evaluation with minimax search.

Features:
- Minimax with alpha-beta pruning
- Move ordering (MVV-LVA, killer moves, history heuristic)
- Quiescence search on captures
- Null move pruning
- Zobrist transposition table
- Dynamic bishop pair evaluation
- Time management for various time controls
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

class MaterialOpponent:
    def __init__(self, max_depth: int = 6, tt_size_mb: int = 128):
        """
        Initialize the Material Opponent engine
        
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
            return self._evaluate_material(board)
            
        self.nodes_searched += 1
        stand_pat = self._evaluate_material(board)
        
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
                score = 200000 + PIECE_VALUES.get(move.promotion, 0)
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
            return self._evaluate_material(board), None
            
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
            self._evaluate_material(board) >= beta):
            
            board.push(chess.Move.null())
            null_score, _ = self._search(board, depth - 3, -beta, -beta + 1, ply + 1, False)
            null_score = -null_score
            board.pop()
            
            if null_score >= beta:
                return beta, None
        
        # Generate and order moves
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return self._evaluate_material(board), None
            
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

class UCIMaterialEngine:
    """UCI interface for Material Opponent engine"""
    
    def __init__(self):
        self.engine = MaterialOpponent()
        
    def run(self):
        """Main UCI loop"""
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                    
                if line == "uci":
                    print("id name Material Opponent")
                    print("id author OpponentEngine")
                    print("option name MaxDepth type spin default 6 min 1 max 20")
                    print("option name TTSize type spin default 128 min 16 max 1024")
                    print("uciok")
                    sys.stdout.flush()  # Ensure output is immediately visible
                    
                elif line == "isready":
                    print("readyok")
                    sys.stdout.flush()  # Ensure output is immediately visible
                    
                elif line == "ucinewgame":
                    self.engine = MaterialOpponent(self.engine.max_depth)
                    
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
                self.engine = MaterialOpponent(self.engine.max_depth, tt_size)
    
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
    engine = UCIMaterialEngine()
    engine.run()
