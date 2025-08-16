#!/usr/bin/env python3
"""
Performance Goals Benchmark Test

Target Performance Goals (Depth 4):
- Pure minimax: <2 seconds, <4,000,000 positions
- + Alpha Beta: <0.25 seconds, <500,000 positions  
- + Move ordering: <0.025 seconds, <5,000 pos    # Test position: Complex middle game position (better benchmark)
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = chess.Board(test_fen)
    depth = 4
    
    print(f"\nTest Position: Complex Middle Game")
    print(f"FEN: {test_fen}")
    print(f"Search Depth: {depth} (2 moves per side)")
    print()
"""

import chess
import time

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

def minimax(board, depth, maximizing, nodes):
    """Traditional minimax (not negamax)"""
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board)
    
    if maximizing:
        max_eval = -9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, False, nodes)
            board.pop()
            max_eval = max(max_eval, eval_score)
        return max_eval
    else:
        min_eval = 9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, True, nodes)
            board.pop()
            min_eval = min(min_eval, eval_score)
        return min_eval

def minimax_with_move(board, depth):
    """Minimax that returns best move and statistics"""
    nodes = [0]
    best_move = None
    best_score = -9999
    
    for move in board.legal_moves:
        board.push(move)
        score = minimax(board, depth - 1, False, nodes)
        board.pop()
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, best_score, nodes[0]

def negamax(board, depth, nodes):
    """Negamax version for comparison"""
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board)
    
    max_score = -9999
    for move in board.legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1, nodes)
        board.pop()
        max_score = max(max_score, score)
    
    return max_score

def negamax_with_move(board, depth):
    """Negamax that returns best move and statistics"""
    nodes = [0]
    best_move = None
    best_score = -9999
    
    for move in board.legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1, nodes)
        board.pop()
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, best_score, nodes[0]

def alpha_beta_minimax(board, depth, alpha, beta, maximizing, nodes):
    """Alpha-beta minimax"""
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board)
    
    if maximizing:
        max_eval = -9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = alpha_beta_minimax(board, depth - 1, alpha, beta, False, nodes)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = alpha_beta_minimax(board, depth - 1, alpha, beta, True, nodes)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def alpha_beta_with_move(board, depth):
    """Alpha-beta that returns best move and statistics"""
    nodes = [0]
    best_move = None
    best_score = -9999
    
    for move in board.legal_moves:
        board.push(move)
        score = alpha_beta_minimax(board, depth - 1, -9999, 9999, False, nodes)
        board.pop()
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, best_score, nodes[0]

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

def ordered_alpha_beta_minimax(board, depth, alpha, beta, maximizing, nodes):
    """Alpha-beta with move ordering"""
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board)
    
    moves = list(board.legal_moves)
    moves = mvv_lva_sort(board, moves)
    
    if maximizing:
        max_eval = -9999
        for move in moves:
            board.push(move)
            eval_score = ordered_alpha_beta_minimax(board, depth - 1, alpha, beta, False, nodes)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 9999
        for move in moves:
            board.push(move)
            eval_score = ordered_alpha_beta_minimax(board, depth - 1, alpha, beta, True, nodes)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def ordered_alpha_beta_with_move(board, depth):
    """Ordered alpha-beta that returns best move and statistics"""
    nodes = [0]
    best_move = None
    best_score = -9999
    
    moves = list(board.legal_moves)
    moves = mvv_lva_sort(board, moves)
    
    for move in moves:
        board.push(move)
        score = ordered_alpha_beta_minimax(board, depth - 1, -9999, 9999, False, nodes)
        board.pop()
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, best_score, nodes[0]

def benchmark_performance_goals():
    """Test against specific performance goals"""
    
    print("=" * 80)
    print("PERFORMANCE GOALS BENCHMARK TEST")
    print("=" * 80)
    print("Target Performance Goals (Depth 4):")
    print("- Pure minimax: <2 seconds, <4,000,000 positions")
    print("- + Alpha Beta: <0.25 seconds, <500,000 positions")  
    print("- + Move ordering: <0.025 seconds, <5,000 positions")
    print("=" * 80)
    
    # Test position: Complex middle game position (better benchmark)
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = chess.Board(test_fen)
    depth = 4
    
    print(f"\\nTest Position: Complex Middle Game")
    print(f"FEN: {test_fen}")
    print(f"Search Depth: {depth} (2 moves per side)")
    print()
    
    # Goals for comparison
    goals = {
        'minimax': {'time': 2.0, 'nodes': 4000000},
        'alphabeta': {'time': 0.25, 'nodes': 500000},
        'ordered': {'time': 0.025, 'nodes': 5000}
    }
    
    results = []
    
    # Test 1: Pure Minimax
    print("Testing Pure Minimax...")
    start_time = time.time()
    move, score, nodes = minimax_with_move(board, depth)
    search_time = time.time() - start_time
    
    time_goal = goals['minimax']['time']
    nodes_goal = goals['minimax']['nodes']
    time_status = "✓ PASS" if search_time < time_goal else "✗ FAIL"
    nodes_status = "✓ PASS" if nodes < nodes_goal else "✗ FAIL"
    
    print(f"  Time: {search_time:.3f}s (goal: <{time_goal}s) {time_status}")
    print(f"  Nodes: {nodes:,} (goal: <{nodes_goal:,}) {nodes_status}")
    print(f"  NPS: {int(nodes/max(search_time, 0.001)):,}")
    print(f"  Best Move: {move}")
    print()
    results.append(('Minimax', search_time, nodes, time_status, nodes_status))
    
    # Test 2: Alpha-Beta
    print("Testing Alpha-Beta...")
    start_time = time.time()
    move, score, nodes = alpha_beta_with_move(board, depth)
    search_time = time.time() - start_time
    
    time_goal = goals['alphabeta']['time']
    nodes_goal = goals['alphabeta']['nodes']
    time_status = "✓ PASS" if search_time < time_goal else "✗ FAIL"
    nodes_status = "✓ PASS" if nodes < nodes_goal else "✗ FAIL"
    
    print(f"  Time: {search_time:.3f}s (goal: <{time_goal}s) {time_status}")
    print(f"  Nodes: {nodes:,} (goal: <{nodes_goal:,}) {nodes_status}")
    print(f"  NPS: {int(nodes/max(search_time, 0.001)):,}")
    print(f"  Best Move: {move}")
    print()
    results.append(('Alpha-Beta', search_time, nodes, time_status, nodes_status))
    
    # Test 3: Alpha-Beta + Move Ordering
    print("Testing Alpha-Beta + Move Ordering...")
    start_time = time.time()
    move, score, nodes = ordered_alpha_beta_with_move(board, depth)
    search_time = time.time() - start_time
    
    time_goal = goals['ordered']['time']
    nodes_goal = goals['ordered']['nodes']
    time_status = "✓ PASS" if search_time < time_goal else "✗ FAIL"
    nodes_status = "✓ PASS" if nodes < nodes_goal else "✗ FAIL"
    
    print(f"  Time: {search_time:.3f}s (goal: <{time_goal}s) {time_status}")
    print(f"  Nodes: {nodes:,} (goal: <{nodes_goal:,}) {nodes_status}")
    print(f"  NPS: {int(nodes/max(search_time, 0.001)):,}")
    print(f"  Best Move: {move}")
    print()
    results.append(('Ordered AB', search_time, nodes, time_status, nodes_status))
    
    # Summary
    print("=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    print(f"{'Method':<15} {'Time':<10} {'Nodes':<12} {'Time Goal':<10} {'Nodes Goal':<12}")
    print("-" * 80)
    
    for method, time_val, nodes_val, time_stat, nodes_stat in results:
        print(f"{method:<15} {time_val:<10.3f} {nodes_val:<12,} {time_stat:<10} {nodes_stat:<12}")
    
    # Check if we need to test Negamax
    minimax_time = results[0][1]
    minimax_nodes = results[0][2]
    
    if minimax_time >= 2.0 or minimax_nodes >= 4000000:
        print("\\n" + "="*50)
        print("MINIMAX UNDERPERFORMING - TESTING NEGAMAX")
        print("="*50)
        
        print("Testing Negamax for comparison...")
        start_time = time.time()
        move, score, nodes = negamax_with_move(board, depth)
        search_time = time.time() - start_time
        
        print(f"\\nNegamax Results:")
        print(f"  Time: {search_time:.3f}s")
        print(f"  Nodes: {nodes:,}")
        print(f"  NPS: {int(nodes/max(search_time, 0.001)):,}")
        print(f"  Best Move: {move}")
        
        time_improvement = ((minimax_time - search_time) / minimax_time * 100)
        nodes_improvement = ((minimax_nodes - nodes) / minimax_nodes * 100)
        
        print(f"\\nNegamax vs Minimax:")
        print(f"  Time improvement: {time_improvement:+.1f}%")
        print(f"  Nodes improvement: {nodes_improvement:+.1f}%")
        
        if search_time < 2.0 and nodes < 4000000:
            print("\\n✓ Negamax meets performance goals - recommend switching from minimax")
        else:
            print("\\n✗ Negamax still doesn't meet goals - may need further optimization")

if __name__ == "__main__":
    benchmark_performance_goals()
