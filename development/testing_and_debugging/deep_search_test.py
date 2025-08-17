#!/usr/bin/env python3
"""
Deep Search Efficiency Test - Depth 5

Focus on one position at depth 5 to see efficiency at deeper levels.
"""

import chess
import time

# Copy the same functions from core_search_test.py
def simple_evaluate(board):
    """Simple material evaluation"""
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    piece_values = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
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

def simple_minimax(board, depth, nodes, max_nodes=1000000):
    nodes[0] += 1
    if nodes[0] > max_nodes:
        return 0, []  # Early exit to prevent excessive computation
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board), []
    
    best_score = -9999
    best_line = []
    
    for move in board.legal_moves:
        board.push(move)
        score, line = simple_minimax(board, depth - 1, nodes, max_nodes)
        score = -score
        board.pop()
        
        if nodes[0] > max_nodes:
            break
        
        if score > best_score:
            best_score = score
            best_line = [move] + line
    
    return best_score, best_line

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
            break
    
    return best_score, best_line

def mvv_lva_sort(board, moves):
    """Sort moves by Most Valuable Victim - Least Valuable Attacker"""
    piece_values = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 10000
    }
    
    def move_score(move):
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += piece_values[victim.piece_type] * 100 - piece_values[attacker.piece_type]
        
        if move.promotion:
            score += piece_values.get(move.promotion, 0) * 100
        
        board.push(move)
        if board.is_check():
            score += 50
        board.pop()
        
        return score
    
    return sorted(moves, key=move_score, reverse=True)

def ordered_alpha_beta(board, depth, alpha, beta, nodes):
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board), []
    
    best_score = -9999
    best_line = []
    
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
            break
    
    return best_score, best_line

def test_depth_5():
    """Test at depth 5 to see deeper search efficiency"""
    
    print("=" * 70)
    print("DEEP SEARCH EFFICIENCY TEST - DEPTH 5")
    print("=" * 70)
    
    # Use a tactical position that should show good move ordering benefits
    fen = "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    board = chess.Board(fen)
    depth = 5
    
    print(f"Position: Scholar's Mate Setup (Tactical)")
    print(f"Depth: {depth}")
    print()
    print(f"{'Method':<25} {'Nodes':<12} {'Time':<8} {'NPS':<12} {'Score':<8}")
    print("-" * 72)
    
    # Test Simple Minimax (with node limit to avoid waiting too long)
    print("Testing Simple Minimax (limited to 1M nodes)...")
    nodes = [0]
    start_time = time.time()
    score, pv = simple_minimax(board, depth, nodes, max_nodes=1000000)
    search_time = time.time() - start_time
    nps = int(nodes[0] / max(search_time, 0.001))
    limited = " (limited)" if nodes[0] >= 1000000 else ""
    print(f"{'Simple Minimax':<25} {nodes[0]:<12,}{limited} {search_time:<8.3f} {nps:<12,} {score:<8}")
    simple_nodes = nodes[0]
    
    # Test Alpha-Beta
    nodes = [0]
    start_time = time.time()
    score, pv = alpha_beta_minimax(board, depth, -9999, 9999, nodes)
    search_time = time.time() - start_time
    nps = int(nodes[0] / max(search_time, 0.001))
    print(f"{'Alpha-Beta':<25} {nodes[0]:<12,} {search_time:<8.3f} {nps:<12,} {score:<8}")
    ab_nodes = nodes[0]
    
    # Test Alpha-Beta + Move Ordering
    nodes = [0]
    start_time = time.time()
    score, pv = ordered_alpha_beta(board, depth, -9999, 9999, nodes)
    search_time = time.time() - start_time
    nps = int(nodes[0] / max(search_time, 0.001))
    print(f"{'AB + Move Ordering':<25} {nodes[0]:<12,} {search_time:<8.3f} {nps:<12,} {score:<8}")
    ordered_nodes = nodes[0]
    
    print()
    print("Efficiency Analysis:")
    
    # Calculate reductions (use minimum for simple if it was limited)
    if simple_nodes >= 1000000:
        print(f"  Simple Minimax: ≥{simple_nodes:,} nodes (search limited)")
        ab_min_reduction = (simple_nodes - ab_nodes) / simple_nodes * 100
        print(f"  Alpha-Beta: ≥{ab_min_reduction:.1f}% node reduction (minimum)")
        
        ordered_min_reduction = (simple_nodes - ordered_nodes) / simple_nodes * 100  
        print(f"  Full Optimization: ≥{ordered_min_reduction:.1f}% node reduction (minimum)")
    else:
        ab_reduction = (simple_nodes - ab_nodes) / simple_nodes * 100
        ordered_reduction = (simple_nodes - ordered_nodes) / simple_nodes * 100
        print(f"  Alpha-Beta vs Simple: {ab_reduction:+.1f}% node reduction")
        print(f"  Full vs Simple: {ordered_reduction:+.1f}% node reduction")
    
    ordering_benefit = (ab_nodes - ordered_nodes) / ab_nodes * 100 if ab_nodes > 0 else 0
    print(f"  Move Ordering additional: {ordering_benefit:+.1f}% node reduction")
    
    print(f"\\n  Node count ratios:")
    print(f"    Alpha-Beta efficiency: {ab_nodes / simple_nodes:.4f}x nodes vs simple")
    print(f"    Full optimization efficiency: {ordered_nodes / simple_nodes:.4f}x nodes vs simple")
    print(f"    Move ordering efficiency: {ordered_nodes / ab_nodes:.4f}x nodes vs alpha-beta")

if __name__ == "__main__":
    test_depth_5()
