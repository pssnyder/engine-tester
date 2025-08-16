#!/usr/bin/env python3
"""
Performance Bottleneck Analysis

The search tree has the correct number of positions (~4M at depth 4),
but our search is too slow (35k NPS instead of expected higher NPS).
Let's identify the bottleneck.
"""

import chess
import time
import cProfile
import io
import pstats

def simple_evaluate_fast(board):
    """Optimized evaluation function"""
    # Quick game over checks
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Fast material count using piece_map()
    piece_values = [0, 100, 320, 330, 500, 900, 0]  # Index by piece type
    
    score = 0
    piece_map = board.piece_map()
    for piece in piece_map.values():
        value = piece_values[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value
        else:
            score -= value
    
    return score if board.turn == chess.WHITE else -score

def simple_evaluate_original(board):
    """Original evaluation for comparison"""
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

def fast_minimax(board, depth, maximizing, nodes, eval_func):
    """Optimized minimax"""
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return eval_func(board)
    
    if maximizing:
        max_eval = -9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = fast_minimax(board, depth - 1, False, nodes, eval_func)
            board.pop()
            max_eval = max(max_eval, eval_score)
        return max_eval
    else:
        min_eval = 9999
        for move in board.legal_moves:
            eval_score = fast_minimax(board, depth - 1, True, nodes, eval_func)
            min_eval = min(min_eval, eval_score)
        return min_eval

def benchmark_evaluation_speed():
    """Test evaluation function speed"""
    print("EVALUATION FUNCTION SPEED TEST")
    print("=" * 50)
    
    # Test position
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = chess.Board(test_fen)
    
    # Test original evaluation
    iterations = 100000
    start_time = time.time()
    for _ in range(iterations):
        score = simple_evaluate_original(board)
    original_time = time.time() - start_time
    
    # Test optimized evaluation
    start_time = time.time()
    for _ in range(iterations):
        score = simple_evaluate_fast(board)
    fast_time = time.time() - start_time
    
    print(f"Original evaluation: {original_time:.3f}s for {iterations:,} calls")
    print(f"Fast evaluation: {fast_time:.3f}s for {iterations:,} calls")
    print(f"Speedup: {original_time/fast_time:.1f}x faster")
    print(f"Original: {iterations/original_time:,.0f} evals/sec")
    print(f"Fast: {iterations/fast_time:,.0f} evals/sec")

def benchmark_search_depth_2():
    """Test search at depth 2 to measure realistic NPS"""
    print("\\nSEARCH SPEED TEST (Depth 2)")
    print("=" * 50)
    
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = chess.Board(test_fen)
    depth = 2
    
    # Test with original evaluation
    nodes = [0]
    start_time = time.time()
    score = fast_minimax(board, depth, True, nodes, simple_evaluate_original)
    original_time = time.time() - start_time
    original_nodes = nodes[0]
    
    # Test with fast evaluation
    nodes = [0]
    start_time = time.time()
    score = fast_minimax(board, depth, True, nodes, simple_evaluate_fast)
    fast_time = time.time() - start_time
    fast_nodes = nodes[0]
    
    print(f"Original eval: {original_time:.3f}s, {original_nodes:,} nodes, {original_nodes/original_time:,.0f} NPS")
    print(f"Fast eval: {fast_time:.3f}s, {fast_nodes:,} nodes, {fast_nodes/fast_time:,.0f} NPS")
    print(f"Speedup: {original_time/fast_time:.1f}x faster")

def profile_minimax():
    """Profile the minimax function to find bottlenecks"""
    print("\\nPROFILING MINIMAX SEARCH")
    print("=" * 50)
    
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = chess.Board(test_fen)
    depth = 3  # Smaller depth for profiling
    
    # Profile the search
    pr = cProfile.Profile()
    nodes = [0]
    
    pr.enable()
    score = fast_minimax(board, depth, True, nodes, simple_evaluate_original)
    pr.disable()
    
    # Get stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    print(f"Depth {depth}: {nodes[0]:,} nodes evaluated")
    print("\\nTop time-consuming functions:")
    print(s.getvalue())

def test_expected_nps():
    """Calculate what NPS we need to meet performance goals"""
    print("\\nEXPECTED NPS ANALYSIS")
    print("=" * 50)
    
    # Performance goals
    goals = [
        ("Minimax", 4000000, 2.0),
        ("Alpha-Beta", 500000, 0.25),
        ("Move Ordering", 5000, 0.025)
    ]
    
    print("Required NPS to meet goals:")
    for name, nodes, time_limit in goals:
        required_nps = nodes / time_limit
        print(f"  {name}: {required_nps:,.0f} NPS")
    
    print(f"\\nOur current NPS: ~35,000")
    print(f"Minimax goal requires: {4000000/2.0:,.0f} NPS (57x faster!)")
    print(f"This suggests we need significant optimization")

if __name__ == "__main__":
    benchmark_evaluation_speed()
    benchmark_search_depth_2()
    test_expected_nps()
    # profile_minimax()  # Uncomment for detailed profiling
