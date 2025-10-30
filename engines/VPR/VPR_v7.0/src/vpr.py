#!/usr/bin/env python3
"""
TAL-BOT Chess Engine - Revolutionary Entropy-Driven Chess AI

An experimental anti-engine based on Mikhail Tal's sacrificial attacking style.
Uses dynamic piece values and chaos-driven search to destroy traditional engines.

THE 2+2=5 PRINCIPLE: Position >> Material
- True piece values based on attacks + legal moves (not static assumptions)
- Chaos factor preservation over safe evaluation
- Priority-based move ordering (best/worst pieces only)
- Entropy warfare: force opponents into complex positions

REVOLUTIONARY FEATURES:
- Dynamic piece value system (true positional worth)
- Chaos factor calculation and preservation
- Priority piece selection (ignore mediocre pieces)
- Principal Variation following for bullet speed
- Anti-engine logic that breaks traditional patterns

TAL-BOT MOTTO: "Into the dark forest where only we know the way out"

Author: Pat Snyder
Version: TAL-BOT v1.0 (The Entropy Engine)
"""

import time
import chess
from typing import Optional, List


class VPREngine:
    """VPR - Barebones chess engine optimized for maximum search depth"""
    
    def __init__(self):
        # Remove static piece values - now using dynamic potential system
        # Each piece's value calculated based on actual position contribution
        
        # Search configuration
        self.default_depth = 8  # Target deeper search
        self.nodes_searched = 0
        self.search_start_time = 0
        
        # TAL-BOT PV Following System
        self.principal_variation = []  # Current PV line
        self.pv_board_states = []      # Board states for PV following
        self.last_search_pv = []       # Last complete PV for instant moves
        self.pv_move_times = []        # Time taken for each PV move
        
        # Dynamic piece potential cache (cleared each position)
        self.piece_potential_cache = {}
    
    def _calculate_piece_potential(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> float:
        """
        Calculate dynamic piece potential based on actual position contribution
        All values in pawn advantage units (1.0 = 1 pawn)
        TUNED SCORING SYSTEM with proper priority hierarchy
        
        Args:
            board: Current position
            square: Piece location
            piece: The piece to evaluate
            
        Returns:
            Dynamic potential value (can be negative for weak pieces)
        """
        potential = 0.0
        
        # 1. Base value = number of squares this piece attacks (mobility foundation)
        attacks = board.attacks(square)
        base_value = len(attacks) * 0.1  # Each square attacked = 0.1 pawns
        potential += base_value
        
        # 2. CRITICAL: If attacked by opponent (HIGHEST PRIORITY)
        opponent_attackers = board.attackers(not piece.color, square)
        if opponent_attackers:
            # Find the least valuable attacker (most likely to capture)
            min_attacker_value = float('inf')
            for attacker_square in opponent_attackers:
                attacker_piece = board.piece_at(attacker_square)
                if attacker_piece:
                    attacker_attacks = len(board.attacks(attacker_square))
                    min_attacker_value = min(min_attacker_value, attacker_attacks)
            
            if min_attacker_value != float('inf'):
                # MAJOR PENALTY: Being attacked is very bad
                attack_penalty = min_attacker_value * 0.2 + 2.0  # At least 2 pawn penalty
                potential -= attack_penalty
        
        # 3. Defense bonus: +0.2 for each friendly piece defended (good but not critical)
        defended_pieces = 0
        for attack_square in attacks:
            defended_piece = board.piece_at(attack_square)
            if defended_piece and defended_piece.color == piece.color:
                defended_pieces += 1
        potential += defended_pieces * 0.2  # Increased from 0.1
        
        # 4. Attack bonus: +0.5 for each enemy piece attacked (very valuable)
        attacked_enemies = 0
        enemy_piece_values = []
        for attack_square in attacks:
            enemy_piece = board.piece_at(attack_square)
            if enemy_piece and enemy_piece.color != piece.color:
                attacked_enemies += 1
                # Weight attacks based on enemy piece mobility (stronger pieces = higher value)
                enemy_mobility = len(board.attacks(attack_square))
                enemy_piece_values.append(enemy_mobility * 0.1)
        
        if attacked_enemies > 0:
            # Bonus based on value of pieces we're attacking
            potential += sum(enemy_piece_values) * 0.5  # Increased from 0.2
        
        # 5. CRITICAL: Queen pin vulnerability (very dangerous)
        if piece.piece_type == chess.QUEEN:
            king_square = board.king(piece.color)
            if king_square and self._is_queen_pinnable(board, square, king_square, piece.color):
                potential -= 3.0  # MAJOR penalty - was /2, now fixed penalty
        
        # 6. CRITICAL: Pinned piece penalty (tactical disaster)
        if self._is_piece_pinned(board, square, piece.color):
            potential -= 1.5  # Increased from 1.0 - pinned pieces are bad
            # King penalty is handled separately in king evaluation
        
        # 7. King safety (handled in separate king evaluation)
        if piece.piece_type == chess.KING:
            potential += self._evaluate_king_safety(board, square, piece.color)
        
        # 8. MAJOR: Trapped piece penalty (especially major pieces)
        if piece.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
            if base_value <= 0.2:  # Very limited mobility (2 squares * 0.1)
                # Severe penalty scaled by piece importance
                trap_penalty = 3.0 if piece.piece_type == chess.QUEEN else 2.0
                potential -= trap_penalty
        elif piece.piece_type == chess.KNIGHT:
            if base_value <= 0.1:  # Knight with 1 or fewer moves
                potential -= 1.0  # Knights hate being trapped too
        
        # 9. Piece coordination bonus (moderate importance)
        potential += self._calculate_coordination_bonus(board, square, piece, attacks)
        
        # 10. Central control bonus (minor but important)
        potential += self._calculate_central_control(board, square, piece)
        
        # 11. Pawn structure interaction (important for pawns)
        if piece.piece_type == chess.PAWN:
            potential += self._evaluate_pawn_potential(board, square, piece)
        
        # Additional tactical heuristics with TUNED values:
        
        # 12. MAJOR: Double attack bonus (forks are gold!)
        if attacked_enemies >= 2:
            fork_bonus = 1.0 + (attacked_enemies - 2) * 0.5  # 1.0 for fork, +0.5 for each extra
            potential += fork_bonus
        
        # 13. Overloaded piece detection (moderate penalty)
        if defended_pieces >= 3:
            potential -= 0.5  # Increased penalty for overloaded defenders
        
        # 14. Development penalty (opening/middlegame concern)
        if piece.color == chess.WHITE and piece.piece_type != chess.PAWN:
            if chess.square_rank(square) == 0:  # Still on back rank
                potential -= 0.3  # Reduced from 0.5 - development matters but not critical
        elif piece.color == chess.BLACK and piece.piece_type != chess.PAWN:
            if chess.square_rank(square) == 7:  # Still on back rank
                potential -= 0.3
        
        # 15. Piece harmony bonus (minor tactical bonus)
        harmony_bonus = self._calculate_piece_harmony(board, square, piece)
        potential += harmony_bonus
        
        return potential
    
    def _calculate_piece_harmony(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> float:
        """Calculate bonus for pieces working in harmony"""
        harmony = 0.0
        
        if piece.piece_type == chess.ROOK:
            # Doubled rooks on files/ranks
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            
            piece_map = board.piece_map()
            for other_square, other_piece in piece_map.items():
                if (other_piece.color == piece.color and 
                    other_piece.piece_type == chess.ROOK and 
                    other_square != square):
                    other_file = chess.square_file(other_square)
                    other_rank = chess.square_rank(other_square)
                    
                    if file == other_file or rank == other_rank:
                        harmony += 0.2  # Doubled rooks bonus
        
        elif piece.piece_type == chess.BISHOP:
            # Bishop on long diagonal
            if square in [chess.A1, chess.H8, chess.A8, chess.H1]:  # Corner squares
                harmony += 0.1
        
        return harmony
    
    def _is_queen_pinnable(self, board: chess.Board, queen_square: chess.Square, 
                          king_square: chess.Square, color: chess.Color) -> bool:
        """Check if queen can be pinned to king"""
        # Check if queen and king are on same file, rank, or diagonal
        queen_file, queen_rank = chess.square_file(queen_square), chess.square_rank(queen_square)
        king_file, king_rank = chess.square_file(king_square), chess.square_rank(king_square)
        
        # Same file or rank (rook/queen pin)
        if queen_file == king_file or queen_rank == king_rank:
            return True
        
        # Same diagonal (bishop/queen pin)
        if abs(queen_file - king_file) == abs(queen_rank - king_rank):
            return True
        
        return False
    
    def _is_piece_pinned(self, board: chess.Board, square: chess.Square, color: chess.Color) -> bool:
        """Check if piece is pinned to king"""
        return board.is_pinned(color, square)
    
    def _evaluate_king_safety(self, board: chess.Board, king_square: chess.Square, color: chess.Color) -> float:
        """Evaluate king safety and return penalty for danger"""
        safety_score = 0.0
        
        # Check if king is in check
        if board.is_check():
            safety_score -= 5.0
        
        # Check for pinned pieces (each pinned piece hurts king safety)
        piece_map = board.piece_map()
        pinned_pieces = 0
        for square, piece in piece_map.items():
            if piece.color == color and board.is_pinned(color, square):
                pinned_pieces += 1
        
        safety_score -= pinned_pieces * 2.0  # 2 points per pinned piece
        
        # Check for attacking pieces near king
        king_area = board.attacks(king_square)
        enemy_attacks_near_king = 0
        for attack_square in king_area:
            if len(board.attackers(not color, attack_square)) > 0:
                enemy_attacks_near_king += 1
        
        safety_score -= enemy_attacks_near_king * 0.3  # Penalty for attacks near king
        
        return safety_score
    
    def _calculate_coordination_bonus(self, board: chess.Board, square: chess.Square, 
                                    piece: chess.Piece, attacks: chess.SquareSet) -> float:
        """Calculate bonus for piece coordination"""
        coordination = 0.0
        
        # Bonus for pieces working together (multiple pieces attacking same squares)
        for attack_square in attacks:
            friendly_attackers = len(board.attackers(piece.color, attack_square))
            if friendly_attackers > 1:  # Multiple pieces attacking same square
                coordination += 0.1 * (friendly_attackers - 1)
        
        # Special coordination bonuses
        if piece.piece_type == chess.ROOK:
            # Rook on open file bonus
            file = chess.square_file(square)
            file_squares = [chess.square(file, rank) for rank in range(8)]
            open_file = True
            for file_square in file_squares:
                file_piece = board.piece_at(file_square)
                if file_piece and file_piece.piece_type == chess.PAWN:
                    open_file = False
                    break
            if open_file:
                coordination += 0.5
        
        elif piece.piece_type == chess.BISHOP:
            # Bishop pair bonus (if we have both bishops)
            bishops = 0
            piece_map = board.piece_map()
            for other_square, other_piece in piece_map.items():
                if (other_piece.color == piece.color and 
                    other_piece.piece_type == chess.BISHOP and 
                    other_square != square):
                    bishops += 1
            if bishops >= 1:  # We have bishop pair
                coordination += 0.3
        
        return coordination
    
    def _calculate_central_control(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> float:
        """Calculate bonus for controlling central squares"""
        central_squares = {chess.D4, chess.D5, chess.E4, chess.E5}
        attacks = board.attacks(square)
        
        central_control = 0.0
        for central_square in central_squares:
            if central_square in attacks:
                central_control += 0.15  # Bonus for each central square controlled
        
        # Extra bonus if piece is actually in center
        if square in central_squares:
            central_control += 0.2
        
        return central_control
    
    def _evaluate_pawn_potential(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> float:
        """Evaluate pawn-specific potential"""
        pawn_bonus = 0.0
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        # Passed pawn bonus
        is_passed = True
        if piece.color == chess.WHITE:
            # Check for enemy pawns ahead
            for check_rank in range(rank + 1, 8):
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:
                        check_square = chess.square(check_file, check_rank)
                        check_piece = board.piece_at(check_square)
                        if (check_piece and check_piece.piece_type == chess.PAWN and 
                            check_piece.color == chess.BLACK):
                            is_passed = False
                            break
        else:
            # Check for enemy pawns ahead (black perspective)
            for check_rank in range(rank - 1, -1, -1):
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:
                        check_square = chess.square(check_file, check_rank)
                        check_piece = board.piece_at(check_square)
                        if (check_piece and check_piece.piece_type == chess.PAWN and 
                            check_piece.color == chess.WHITE):
                            is_passed = False
                            break
        
        if is_passed:
            # Passed pawn bonus increases as it advances
            if piece.color == chess.WHITE:
                pawn_bonus += (rank - 1) * 0.2  # More bonus closer to promotion
            else:
                pawn_bonus += (6 - rank) * 0.2
        
        # Doubled pawn penalty
        pawns_on_file = 0
        for check_rank in range(8):
            check_square = chess.square(file, check_rank)
            check_piece = board.piece_at(check_square)
            if (check_piece and check_piece.piece_type == chess.PAWN and 
                check_piece.color == piece.color):
                pawns_on_file += 1
        
        if pawns_on_file > 1:
            pawn_bonus -= 0.3  # Penalty for doubled pawns
        
        return pawn_bonus
    
    def _calculate_piece_priorities(self, board: chess.Board) -> dict:
        """
        Calculate piece priorities using dynamic potential system
        Focus on weak pieces (negative potential) and pieces with growth opportunity
        """
        piece_data = {}
        
        # Clear cache for new position
        self.piece_potential_cache = {}
        
        # Get all pieces directly
        piece_map = board.piece_map()
        
        for square, piece in piece_map.items():
            # Calculate dynamic potential value
            potential_value = self._calculate_piece_potential(board, square, piece)
            
            # Cache the calculation
            self.piece_potential_cache[square] = potential_value
            
            # Calculate tactical metrics for move ordering
            attackers = len(board.attackers(not piece.color, square))
            defenders = len(board.attackers(piece.color, square))
            mobility = len(board.attacks(square))
            
            # Get quick opportunity assessment
            is_under_attack = attackers > 0
            can_capture = 0
            for attack_square in board.attacks(square):
                target = board.piece_at(attack_square)
                if target and target.color != piece.color:
                    can_capture += 1
            
            # Calculate basic opportunity score
            opportunity_score = 0
            if can_capture > 0:
                opportunity_score += can_capture * 25
            if can_capture >= 2:  # Fork potential
                opportunity_score += 100
            
            # Calculate priority score - prioritize pieces that need immediate attention
            priority_score = 0
            
            # CRITICAL PRIORITY: Pieces under attack get maximum urgency
            if potential_value < -1.0:  # Severely threatened pieces
                priority_score = 2000 + abs(potential_value) * 200  # EMERGENCY - save this piece!
            elif potential_value < 0:  # Any negative potential
                priority_score = 1500 + abs(potential_value) * 100  # Very urgent rescue
            
            # HIGH PRIORITY: Pieces with tactical opportunities  
            elif opportunity_score > 100:  # Major tactical chances
                priority_score = 1000 + opportunity_score
            elif opportunity_score > 50:   # Good tactical chances
                priority_score = 800 + opportunity_score
                
            # MEDIUM PRIORITY: Pieces that can be improved
            elif potential_value < 1.0:
                priority_score = 500 + (1.0 - potential_value) * 100  # Improvement opportunity
            
            # LOW PRIORITY: Already good pieces
            else:
                priority_score = potential_value * 50  # Keep strong pieces active
            
            piece_data[square] = {
                'piece': piece,
                'potential': potential_value,
                'priority': priority_score,
                'mobility': mobility,
                'attackers': attackers,
                'defenders': defenders,
                'is_weak': potential_value < 0,
                'needs_improvement': 0 <= potential_value < 1.0,  # Updated threshold
                'is_strong': potential_value >= 2.0,  # Updated threshold
                'opportunity_score': opportunity_score  # Add this for consistency
            }
        
        return piece_data
    
    def search(self, board: chess.Board, time_limit: float = 3.0, 
               depth: Optional[int] = None) -> chess.Move:
        """
        TAL-BOT main search with PV collection and following
        
        Args:
            board: Current position
            time_limit: Time limit in seconds
            depth: Optional fixed depth (otherwise uses default)
            
        Returns:
            Best move found
        """
        self.nodes_searched = 0
        self.search_start_time = time.time()
        
        # Check for PV following opportunity (instant move)
        instant_move = self._check_pv_following(board)
        if instant_move:
            print(f"info string PV following: instant move {instant_move}")
            return instant_move
        
        # Use piece-focused move generation for better initial analysis
        legal_moves = self._generate_piece_focused_moves(board)
        if not legal_moves:
            return chess.Move.null()
        
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # Calculate time allocation (use 80% of available time)
        target_time = time_limit * 0.8
        
        # Iterative deepening with PV collection
        max_depth = depth if depth else self.default_depth
        best_move = legal_moves[0]
        best_score = -999999
        self.principal_variation = []
        
        for current_depth in range(1, max_depth + 1):
            iteration_start = time.time()
            elapsed = time.time() - self.search_start_time
            
            # Stop if we're running out of time
            if elapsed > target_time:
                break
            
            # Search at current depth with PV collection
            current_pv = []
            score = -999999
            current_best = best_move
            time_exceeded = False
            
            # Use piece-focused move generation for each depth
            depth_moves = self._generate_piece_focused_moves(board)
            
            for move in depth_moves:
                # Check time before starting move search
                elapsed = time.time() - self.search_start_time
                if elapsed > target_time:
                    time_exceeded = True
                    break
                
                board.push(move)
                
                # Negamax search with PV collection
                move_pv = []
                move_score = -self._negamax(board, current_depth - 1, -999999, 999999, target_time, move_pv)
                
                board.pop()
                
                if move_score > score:
                    score = move_score
                    current_best = move
                    current_pv = [move] + move_pv  # Build full PV
            
            # Update best move and PV only if we completed this depth
            if not time_exceeded:
                best_move = current_best
                best_score = score
                self.principal_variation = current_pv[:]  # Store current PV
                
                # UCI info output with full PV
                elapsed = time.time() - self.search_start_time
                nps = int(self.nodes_searched / elapsed) if elapsed > 0 else 0
                
                # Format PV for UCI
                pv_string = " ".join(str(move) for move in current_pv[:10])  # Show first 10 moves
                
                print(f"info depth {current_depth} score cp {int(score)} "
                      f"nodes {self.nodes_searched} time {int(elapsed * 1000)} "
                      f"nps {nps} pv {pv_string}")
        
        # Store final PV for potential following
        self.last_search_pv = self.principal_variation[:]
        self._store_pv_board_states(board)
        
        return best_move
    
    def _quick_material_balance(self, board: chess.Board) -> int:
        """
        Quick material balance using dynamic potential instead of static values
        
        Args:
            board: Current position
            
        Returns:
            Material balance from current player's perspective (in pawn units)
        """
        white_potential = 0.0
        black_potential = 0.0
        
        # Use piece_map() for efficiency
        piece_map = board.piece_map()
        
        for square, piece in piece_map.items():
            # Quick potential estimation (simpler than full calculation)
            base_potential = len(board.attacks(square))  # Mobility as base value
            
            if piece.color == chess.WHITE:
                white_potential += base_potential
            else:
                black_potential += base_potential
        
        if board.turn == chess.WHITE:
            return int(white_potential - black_potential)
        else:
            return int(black_potential - white_potential)
    
    def _analyze_piece_opportunities(self, board: chess.Board, square: chess.Square, piece: chess.Piece) -> dict:
        """
        Analyze a piece's critical opportunities and threats - human-like piece evaluation
        
        Args:
            board: Current position
            square: Piece location  
            piece: The piece to analyze
            
        Returns:
            Dict with piece opportunities and critical moves
        """
        opportunities = {
            'critical_moves': [],           # Most important moves for this piece
            'attack_vectors': [],           # Squares this piece attacks
            'threat_level': 0,              # How urgent this piece needs attention
            'opportunity_score': 0,         # How much this piece can contribute
            'is_under_attack': False,
            'can_capture': [],              # Enemy pieces this can capture
            'can_defend': [],               # Friendly pieces this can defend
            'can_fork': False,              # Can attack multiple pieces
            'can_check': False,             # Can check enemy king
            'mobility_squares': 0,          # Total squares accessible
            'escape_squares': []            # Safe squares if under attack
        }
        
        # Get all squares this piece attacks
        attack_squares = board.attacks(square)
        opportunities['attack_vectors'] = list(attack_squares)
        opportunities['mobility_squares'] = len(attack_squares)
        
        # Check if piece is under attack
        enemy_attackers = board.attackers(not piece.color, square)
        opportunities['is_under_attack'] = len(enemy_attackers) > 0
        
        if opportunities['is_under_attack']:
            opportunities['threat_level'] += 500  # MAXIMUM URGENCY - piece needs immediate help
            
            # Find escape squares for attacked piece
            for move in board.legal_moves:
                if move.from_square == square:
                    # Check if destination is safe
                    board.push(move)
                    is_safe = len(board.attackers(not piece.color, move.to_square)) == 0
                    board.pop()
                    
                    if is_safe:
                        opportunities['escape_squares'].append(move.to_square)
                        opportunities['critical_moves'].append(move)
                        opportunities['opportunity_score'] += 200  # High reward for finding safety
        
        # Analyze attack opportunities
        enemy_king = board.king(not piece.color)
        targets_attacked = 0
        
        for attack_square in attack_squares:
            target = board.piece_at(attack_square)
            
            if target:
                if target.color != piece.color:
                    # Enemy piece - can capture
                    opportunities['can_capture'].append(attack_square)
                    targets_attacked += 1
                    
                    # Check if this would be a good trade
                    target_potential = self._calculate_piece_potential(board, attack_square, target)
                    our_potential = self._calculate_piece_potential(board, square, piece)
                    
                    if target_potential > our_potential:
                        # Good capture - high priority
                        capture_move = chess.Move(square, attack_square)
                        if capture_move in board.legal_moves:
                            opportunities['critical_moves'].append(capture_move)
                            opportunities['opportunity_score'] += 100  # Increased from 50
                
                else:
                    # Friendly piece - can defend
                    opportunities['can_defend'].append(attack_square)
            
            # Check if we can give check
            if attack_square == enemy_king:
                opportunities['can_check'] = True
                opportunities['opportunity_score'] += 75  # Increased from 30
                
                # Add checking moves to critical moves
                for move in board.legal_moves:
                    if move.from_square == square and move.to_square in attack_squares:
                        board.push(move)
                        if board.is_check():
                            opportunities['critical_moves'].append(move)
                        board.pop()
        
        # Check for fork opportunities (attacking multiple pieces)
        if targets_attacked >= 2:
            opportunities['can_fork'] = True
            opportunities['opportunity_score'] += 150  # MAJOR bonus - increased from 40
        
        # Penalty for low mobility (trapped pieces)
        if opportunities['mobility_squares'] <= 2 and piece.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
            opportunities['threat_level'] += 200  # Major problem - increased from 50
        if targets_attacked >= 2:
            opportunities['can_fork'] = True
            opportunities['opportunity_score'] += 40
        
        # Penalty for low mobility (trapped pieces)
        if opportunities['mobility_squares'] <= 2 and piece.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
            opportunities['threat_level'] += 50  # Trapped major piece
        
        # Look for improvement moves (better squares for this piece)
        current_potential = self._calculate_piece_potential(board, square, piece)
        
        for move in board.legal_moves:
            if move.from_square == square and move.to_square not in [m.to_square for m in opportunities['critical_moves']]:
                # Test if this move improves the piece
                board.push(move)
                new_potential = self._calculate_piece_potential(board, move.to_square, piece)
                improvement = new_potential - current_potential
                board.pop()
                
                if improvement > 0.5:  # Significant improvement
                    opportunities['critical_moves'].append(move)
                    opportunities['opportunity_score'] += int(improvement * 10)
        
        return opportunities
    
    def _generate_piece_focused_moves(self, board: chess.Board) -> List[chess.Move]:
        """
        Generate moves by examining pieces and their opportunities first
        Only creates moves for pieces with significant opportunities or threats
        
        Args:
            board: Current position
            
        Returns:
            Prioritized list of moves based on piece analysis
        """
        piece_analyses = []
        piece_map = board.piece_map()
        
        # Analyze each of our pieces for opportunities and threats
        for square, piece in piece_map.items():
            if piece.color == board.turn:
                analysis = self._analyze_piece_opportunities(board, square, piece)
                analysis['square'] = square
                analysis['piece'] = piece
                piece_analyses.append(analysis)
        
        # Sort pieces by urgency and opportunity (threat_level first for urgent pieces)
        piece_analyses.sort(key=lambda x: (x['threat_level'] + x['opportunity_score']), reverse=True)
        
        # Collect moves from most critical pieces first
        prioritized_moves = []
        urgent_moves = []  # Separate urgent moves (pieces under attack)
        
        for analysis in piece_analyses:
            # Prioritize critical moves from this piece
            for move in analysis['critical_moves']:
                if move not in prioritized_moves:
                    if analysis['threat_level'] > 150:  # Very urgent
                        urgent_moves.append(move)
                    else:
                        prioritized_moves.append(move)
            
            # If piece has high threat/opportunity, add some of its other moves too
            if analysis['threat_level'] > 50 or analysis['opportunity_score'] > 30:
                square = analysis['square']
                for move in board.legal_moves:
                    if (move.from_square == square and 
                        move not in prioritized_moves and 
                        move not in urgent_moves):
                        if analysis['threat_level'] > 150:
                            urgent_moves.append(move)
                        else:
                            prioritized_moves.append(move)
                        if len(prioritized_moves) + len(urgent_moves) > 40:
                            break
        
        # Put urgent moves first, then other prioritized moves
        final_moves = urgent_moves + prioritized_moves
        
        # Put urgent moves first, then other prioritized moves
        final_moves = urgent_moves + prioritized_moves
        
        # Add remaining legal moves if we haven't hit them all
        for move in board.legal_moves:
            if move not in final_moves:
                final_moves.append(move)
                if len(final_moves) > 60:  # Hard limit
                    break
        
        return final_moves
    
    def _order_moves_piece_focused(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """
        Enhanced move ordering using piece-focused analysis
        Prioritizes moves based on piece opportunities rather than just move characteristics
        
        Args:
            board: Current position
            moves: List of legal moves
            
        Returns:
            Ordered list of moves (highest priority first)
        """
        if len(moves) <= 2:
            return moves
        
        # Use the piece-focused move generation if we have a fresh position
        if len(moves) == len(list(board.legal_moves)):
            # We have all legal moves, so use piece-focused ordering
            return self._generate_piece_focused_moves(board)
        
        # Otherwise, fall back to analyzing the given moves
        move_scores = []
        
        for move in moves:
            score = 0
            from_square = move.from_square
            to_square = move.to_square
            piece = board.piece_at(from_square)
            target = board.piece_at(to_square)
            
            # Get piece analysis for the moving piece
            piece_analysis = self._analyze_piece_opportunities(board, from_square, piece)
            
            # High priority for critical moves identified in piece analysis
            if move in piece_analysis['critical_moves']:
                score += 1000
            
            # Priority based on piece threat level
            score += piece_analysis['threat_level']
            
            # Priority based on piece opportunity
            score += piece_analysis['opportunity_score']
            
            # Capture scoring
            if target:
                target_potential = len(board.attacks(to_square))  # Quick estimate
                score += target_potential * 10
                
                # Bonus for capturing with threatened pieces
                if piece_analysis['is_under_attack']:
                    score += 200
            
            # Check bonus
            board.push(move)
            if board.is_check():
                score += 100
            board.pop()
            
            move_scores.append((score, move))
        
        # Sort by score (highest first)
        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in move_scores]
        """
        Dynamic potential-based move ordering focused on piece improvement
        
        Args:
            board: Current position
            moves: List of legal moves
            
        Returns:
            Ordered list of moves (highest priority first)
        """
        if len(moves) <= 2:
            return moves
        
        # Get piece priority data once for all pieces
        piece_priorities = self._calculate_piece_priorities(board)
        
        sorted_moves = []
        
        for move in moves:
            from_square = move.from_square
            to_square = move.to_square
            piece = board.piece_at(from_square)
            target_piece = board.piece_at(to_square)

            score = 0
            
            # Get piece data for the moving piece
            piece_data = piece_priorities.get(from_square, {})
            current_potential = piece_data.get('potential', 0)
            
            if target_piece:
                # Capture: Use dynamic potential instead of static values
                # Calculate what the captured piece's potential would be
                board.push(move)  # Temporarily make the move
                try:
                    victim_potential = self._calculate_piece_potential(board, to_square, target_piece)
                except:
                    victim_potential = len(board.attacks(to_square))  # Fallback to mobility
                board.pop()  # Undo the move
                
                # Score based on victim's potential minus our piece's risk
                score = victim_potential * 10 - abs(current_potential)
                
                # Huge bonus for capturing with weak pieces (they need to do something useful)
                if current_potential < 0:
                    score += 500  # Weak piece doing something productive
                
                # Bonus for removing strong enemy pieces
                if victim_potential > 3:
                    score += 200
                    
            else:
                # Quiet move: prioritize improving weak pieces
                if current_potential < 0:
                    # This is a weak piece that needs help - high priority
                    score = 1000 + abs(current_potential) * 100
                    
                elif current_potential < 2.0:
                    # This piece has improvement potential
                    score = 500 + (2.0 - current_potential) * 50
                    
                else:
                    # Already strong piece - lower priority for quiet moves
                    score = current_potential * 10
                
                # Additional bonuses for specific improvements
                # Try to estimate if move improves piece potential
                board.push(move)
                try:
                    new_potential = self._calculate_piece_potential(board, to_square, piece)
                    improvement = new_potential - current_potential
                    score += improvement * 100  # Bonus for improvement
                except:
                    pass  # If calculation fails, use current score
                board.pop()

            sorted_moves.append((score, move))

        # Sort by score (highest first)
        sorted_moves.sort(key=lambda x: x[0], reverse=True)

        return [move for score, move in sorted_moves]
    
    def _evaluate_position(self, board: chess.Board) -> float:
        """
        TAL-BOT evaluation: dynamic piece values + chaos factor
        
        Args:
            board: Position to evaluate
            
        Returns:
            Evaluation score from current player's perspective
        """
        if board.is_checkmate():
            return -900000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Calculate dynamic evaluation for both sides
        white_score = self._evaluate_side_dynamic(board, chess.WHITE)
        black_score = self._evaluate_side_dynamic(board, chess.BLACK)
        
        # Calculate chaos factor for position complexity
        chaos_factor = self._calculate_chaos_factor(board)
        
        # Apply chaos bonus to current player (encourages complex positions)
        if board.turn == chess.WHITE:
            base_score = white_score - black_score
            return base_score + (chaos_factor * 3)  # 3cp per chaos point
        else:
            base_score = black_score - white_score
            return base_score + (chaos_factor * 3)
    
    def _check_pv_following(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Check if we can instantly play a move from stored PV (PV following)
        
        This is crucial for bullet/blitz where TAL-BOT should excel.
        If opponent plays expected moves, we blitz out our response.
        
        Args:
            board: Current position
            
        Returns:
            Instant move if PV following applies, None otherwise
        """
        if not self.last_search_pv or len(self.last_search_pv) < 2:
            return None
        
        # Check if current position matches expected PV position
        # We need to verify the opponent played our predicted move
        
        # For now, simple implementation: if we have stored PV and 
        # it's our turn, try to play the next move in the PV
        if len(self.last_search_pv) >= 1:
            candidate_move = self.last_search_pv[0]
            
            # Verify the move is still legal in current position
            if candidate_move in board.legal_moves:
                # Remove this move from PV and advance
                self.last_search_pv = self.last_search_pv[1:]
                return candidate_move
        
        return None
    
    def _store_pv_board_states(self, board: chess.Board):
        """
        Store board states for PV following verification
        
        Args:
            board: Current position
        """
        # Store current board state and PV for next move
        self.pv_board_states = [board.copy()]
        
        # Simulate PV moves to store expected positions
        temp_board = board.copy()
        for i, move in enumerate(self.principal_variation[:5]):  # Store first 5 moves
            if move in temp_board.legal_moves:
                temp_board.push(move)
                self.pv_board_states.append(temp_board.copy())
            else:
                break
    
    def _negamax(self, board: chess.Board, depth: int, alpha: float, beta: float, 
                        target_time: float, pv_line: List[chess.Move]) -> float:
        """
        TAL-BOT negamax with PV collection for full line display
        
        Args:
            board: Current position
            depth: Remaining depth to search
            alpha: Alpha bound
            beta: Beta bound
            target_time: Target time limit for search
            pv_line: List to collect PV moves
            
        Returns:
            Evaluation score from current player's perspective
        """
        self.nodes_searched += 1
        
        # Check time every 1000 nodes
        if self.nodes_searched % 1000 == 0:
            elapsed = time.time() - self.search_start_time
            if elapsed > target_time:
                return 0  # Return neutral score if time exceeded
        
        # Terminal conditions
        if depth <= 0:
            return self._evaluate_position(board)
        
        if board.is_game_over():
            if board.is_checkmate():
                return -900000 + (self.default_depth - depth)  # Prefer faster mates
            return 0  # Draw
        
        # Move generation and ordering - USE PIECE-FOCUSED APPROACH
        # Instead of generating all moves then ordering, we analyze pieces first
        legal_moves = self._generate_piece_focused_moves(board)
        
        # If we need traditional ordering for some reason, fall back
        if not legal_moves:
            legal_moves = list(board.legal_moves)
            legal_moves = self._order_moves_piece_focused(board, legal_moves)
        
        best_score = -999999
        best_pv = []
        moves_searched = 0
        
        for move in legal_moves:
            board.push(move)
            
            # Recursive search with PV collection
            current_pv = []
            score = -self._negamax(board, depth - 1, -beta, -alpha, target_time, current_pv)
            
            board.pop()
            
            moves_searched += 1
            
            # TAL-BOT conditional pruning with PV tracking
            if score > best_score:
                best_score = score
                best_pv = [move] + current_pv  # Build PV line
            
            if score > alpha:
                alpha = score
            
            # Revolutionary chaos-driven pruning with PV consideration
            if alpha >= beta:
                # Standard alpha-beta cutoff
                material_balance = self._quick_material_balance(board)
                
                break  # Standard beta cutoff
        
        # Copy best PV to output parameter
        pv_line[:] = best_pv
        
        return best_score
    
    
    def _evaluate_side(self, board: chess.Board, color: chess.Color) -> float:
        """
        Dynamic potential-based evaluation for one side
        
        Args:
            board: Current position
            color: Side to evaluate
            
        Returns:
            Total potential score for the side (in pawn units)
        """
        total_potential = 0.0
        
        # Get all pieces at once
        piece_map = board.piece_map()
        
        for square, piece in piece_map.items():
            if piece.color == color:
                # Use cached potential if available, otherwise calculate
                if square in self.piece_potential_cache:
                    potential = self.piece_potential_cache[square]
                else:
                    potential = self._calculate_piece_potential(board, square, piece)
                    self.piece_potential_cache[square] = potential
                
                total_potential += potential
        
        return total_potential
    
    def _evaluate_side_dynamic(self, board: chess.Board, color: chess.Color) -> float:
        """
        Dynamic evaluation using full potential calculation
        (This replaces the old PST-based evaluation)
        
        Args:
            board: Current position
            color: Side to evaluate
            
        Returns:
            Dynamic score for the side
        """
        return self._evaluate_side(board, color)  # Now the same as _evaluate_side
    
    def _calculate_chaos_factor(self, board: chess.Board) -> int:
        """
        Calculate position complexity/chaos factor for TAL-BOT's aggressive style
        
        Args:
            board: Current position
            
        Returns:
            Chaos factor (higher = more complex position)
        """
        chaos = 0
        
        # Count total legal moves (more moves = more complexity)
        legal_moves = list(board.legal_moves)
        chaos += len(legal_moves) // 5  # Scale down move count
        
        # Count pieces under attack
        piece_map = board.piece_map()
        attacked_pieces = 0
        
        for square, piece in piece_map.items():
            if len(board.attackers(not piece.color, square)) > 0:
                attacked_pieces += 1
        
        chaos += attacked_pieces * 2  # Attacked pieces increase chaos
        
        # Check for checks (adds tension)
        if board.is_check():
            chaos += 3
        
        # Count captures available
        captures = 0
        for move in legal_moves:
            if board.piece_at(move.to_square):
                captures += 1
        
        chaos += captures  # Available captures add complexity
        
        return min(chaos, 20)  # Cap chaos factor at reasonable level
    
    def new_game(self):
        """Reset engine state for a new game"""
        self.nodes_searched = 0
    
    def get_engine_info(self) -> dict:
        """Return engine information and statistics"""
        return {
            'name': 'VPR',
            'version': '1.0',
            'author': 'Pat Snyder',
            'description': 'Barebones maximum depth experimental engine',
            'default_depth': self.default_depth,
            'nodes_searched': self.nodes_searched
        }
