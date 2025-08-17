#!/usr/bin/env python3
"""
Core Search Efficiency Test

Test the main search without quiescence to isolate alpha-beta and move ordering gains.
"""

import chess
import time

# Simple evaluation for testing (no quiescence)
def simple_evaluate(board):
    """Simple material evaluation"""
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0
    }
    
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    
    return score if board.turn == chess.WHITE else -score

# Simple minimax (no alpha-beta)
def simple_minimax(board, depth, nodes):
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board), []
    
    best_score = -9999
    best_line = []
    
    for move in board.legal_moves:
        board.push(move)
        score, line = simple_minimax(board, depth - 1, nodes)
        score = -score
        board.pop()
        
        if score > best_score:
            best_score = score
            best_line = [move] + line
    
    return best_score, best_line

# Alpha-beta minimax
def alpha_beta_minimax(board, depth, alpha, beta, nodes):
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board), []
    
    best_score = -9999
    best_line = []
    
    for move in board.legal_moves:
        board.push(move)
        score, line = alpha_beta_minimax(board, depth - 1, -beta, -alpha, nodes)
        score = -score
        board.pop()
        
        if score > best_score:
            best_score = score
            best_line = [move] + line
        
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Alpha-beta cutoff
    
    return best_score, best_line

# MVV-LVA move ordering
def mvv_lva_sort(board, moves):
    """Sort moves by Most Valuable Victim - Least Valuable Attacker"""
    piece_values = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 10000
    }
    
    def move_score(move):
        score = 0
        
        # Captures: MVV-LVA
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += piece_values[victim.piece_type] * 100 - piece_values[attacker.piece_type]
        
        # Promotions
        if move.promotion:
            score += piece_values.get(move.promotion, 0) * 100
        
        # Checks
        board.push(move)
        if board.is_check():
            score += 50
        board.pop()
        
        return score
    
    return sorted(moves, key=move_score, reverse=True)

# Alpha-beta with move ordering
def ordered_alpha_beta(board, depth, alpha, beta, nodes):
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board), []
    
    best_score = -9999
    best_line = []
    
    # Sort moves by likely importance
    moves = list(board.legal_moves)
    moves = mvv_lva_sort(board, moves)
    
    for move in moves:
        board.push(move)
        score, line = ordered_alpha_beta(board, depth - 1, -beta, -alpha, nodes)
        score = -score
        board.pop()
        
        if score > best_score:
            best_score = score
            best_line = [move] + line
        
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Alpha-beta cutoff
    
    return best_score, best_line

def test_search_efficiency():
    """Test efficiency of different search methods"""
    
    print("=" * 70)
    print("CORE SEARCH EFFICIENCY TEST")
    print("=" * 70)
    
    positions = [
        ("Starting Position", chess.STARTING_FEN),
        ("Open Middle Game", "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
        ("Tactical Position", "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    ]
    
    depth = 4
    
    for pos_name, fen in positions:
        print(f"\\n--- {pos_name} (Depth {depth}) ---")
        print(f"{'Method':<25} {'Nodes':<10} {'Time':<8} {'NPS':<12} {'Score':<8}")
        print("-" * 70)
        
        board = chess.Board(fen)
        results = []
        
        # Test 1: Simple Minimax
        nodes = [0]
        start_time = time.time()
        score, pv = simple_minimax(board, depth, nodes)
        search_time = time.time() - start_time
        nps = int(nodes[0] / max(search_time, 0.001))
        print(f"{'Simple Minimax':<25} {nodes[0]:<10,} {search_time:<8.3f} {nps:<12,} {score:<8}")
        results.append(('Simple', nodes[0], search_time))
        
        # Test 2: Alpha-Beta
        nodes = [0]
        start_time = time.time()
        score, pv = alpha_beta_minimax(board, depth, -9999, 9999, nodes)
        search_time = time.time() - start_time
        nps = int(nodes[0] / max(search_time, 0.001))
        print(f"{'Alpha-Beta':<25} {nodes[0]:<10,} {search_time:<8.3f} {nps:<12,} {score:<8}")
        results.append(('Alpha-Beta', nodes[0], search_time))
        
        # Test 3: Alpha-Beta + Move Ordering
        nodes = [0]
        start_time = time.time()
        score, pv = ordered_alpha_beta(board, depth, -9999, 9999, nodes)
        search_time = time.time() - start_time
        nps = int(nodes[0] / max(search_time, 0.001))
        print(f"{'AB + Move Ordering':<25} {nodes[0]:<10,} {search_time:<8.3f} {nps:<12,} {score:<8}")
        results.append(('Ordered', nodes[0], search_time))
        
        # Calculate efficiency gains
        simple_nodes = results[0][1]
        ab_nodes = results[1][1]
        ordered_nodes = results[2][1]
        
        ab_reduction = (simple_nodes - ab_nodes) / simple_nodes * 100
        ordered_reduction = (simple_nodes - ordered_nodes) / simple_nodes * 100
        ordering_additional = (ab_nodes - ordered_nodes) / ab_nodes * 100 if ab_nodes > 0 else 0
        
        print(f"\\n  Efficiency gains:")
        print(f"    Alpha-Beta vs Simple: {ab_reduction:+.1f}% node reduction")
        print(f"    Ordered vs Simple: {ordered_reduction:+.1f}% node reduction")
        print(f"    Move Ordering additional: {ordering_additional:+.1f}% node reduction")

if __name__ == "__main__":
    test_search_efficiency()
