#!/usr/bin/env python3
"""
Robust Performance Goals Test with Timeouts

Expected baseline performance (from reference engine):
- Pure minimax: <2 seconds, <4,000,000 positions
- + Alpha Beta: <0.25 seconds, <500,000 positions  
- + Move ordering: <0.025 seconds, <5,000 positions

Critical Issue: Our position count is 20x lower than expected!
This suggests we're missing search branches - potentially a critical bug.
"""

import chess
import time
import signal
import sys

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Search timed out")

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

def minimax(board, depth, maximizing, nodes, start_time, timeout):
    """Traditional minimax with timeout protection"""
    if time.time() - start_time > timeout:
        raise TimeoutError("Search exceeded timeout")
    
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board)
    
    if maximizing:
        max_eval = -9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, False, nodes, start_time, timeout)
            board.pop()
            max_eval = max(max_eval, eval_score)
        return max_eval
    else:
        min_eval = 9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, True, nodes, start_time, timeout)
            board.pop()
            min_eval = min(min_eval, eval_score)
        return min_eval

def minimax_with_move(board, depth, timeout):
    """Minimax that returns best move with timeout protection"""
    nodes = [0]
    best_move = None
    best_score = -9999
    start_time = time.time()
    
    try:
        move_count = 0
        for move in board.legal_moves:
            move_count += 1
            board.push(move)
            score = minimax(board, depth - 1, False, nodes, start_time, timeout)
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move, best_score, nodes[0], False, move_count
    except TimeoutError:
        return best_move, best_score, nodes[0], True, move_count

def alpha_beta_minimax(board, depth, alpha, beta, maximizing, nodes, start_time, timeout):
    """Alpha-beta minimax with timeout protection"""
    if time.time() - start_time > timeout:
        raise TimeoutError("Search exceeded timeout")
        
    nodes[0] += 1
    
    if depth == 0 or board.is_game_over():
        return simple_evaluate(board)
    
    if maximizing:
        max_eval = -9999
        for move in board.legal_moves:
            board.push(move)
            eval_score = alpha_beta_minimax(board, depth - 1, alpha, beta, False, nodes, start_time, timeout)
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
            eval_score = alpha_beta_minimax(board, depth - 1, alpha, beta, True, nodes, start_time, timeout)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def alpha_beta_with_move(board, depth, timeout):
    """Alpha-beta that returns best move with timeout protection"""
    nodes = [0]
    best_move = None
    best_score = -9999
    start_time = time.time()
    
    try:
        move_count = 0
        for move in board.legal_moves:
            move_count += 1
            board.push(move)
            score = alpha_beta_minimax(board, depth - 1, -9999, 9999, False, nodes, start_time, timeout)
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move, best_score, nodes[0], False, move_count
    except TimeoutError:
        return best_move, best_score, nodes[0], True, move_count

def diagnostic_search_analysis(board, depth):
    """Analyze search tree structure to understand position count discrepancy"""
    print("\\n" + "="*60)
    print("DIAGNOSTIC SEARCH ANALYSIS")
    print("="*60)
    
    # Count legal moves at each depth
    def count_positions_per_depth(board, depth, current_depth=0, counts=None):
        if counts is None:
            counts = {}
        
        if current_depth not in counts:
            counts[current_depth] = 0
        counts[current_depth] += 1
        
        if depth > 0 and not board.is_game_over():
            for move in board.legal_moves:
                board.push(move)
                count_positions_per_depth(board, depth - 1, current_depth + 1, counts)
                board.pop()
        
        return counts
    
    print(f"Analyzing position tree for depth {depth}...")
    position_counts = count_positions_per_depth(board, depth)
    
    total_positions = sum(position_counts.values())
    legal_moves = len(list(board.legal_moves))
    
    print(f"\\nPosition count by depth:")
    for d, count in position_counts.items():
        print(f"  Depth {d}: {count:,} positions")
    
    print(f"\\nTotal positions: {total_positions:,}")
    print(f"Root legal moves: {legal_moves}")
    print(f"Expected vs Actual: 4,000,000 vs {total_positions:,}")
    print(f"Discrepancy factor: {4000000 / max(total_positions, 1):.1f}x")
    
    # Calculate theoretical branching
    if len(position_counts) >= 3:
        avg_branching = (position_counts.get(1, 0) / max(position_counts.get(0, 1), 1))
        theoretical_full_tree = legal_moves * (avg_branching ** (depth - 1))
        print(f"\\nAverage branching factor: {avg_branching:.1f}")
        print(f"Theoretical full tree (no pruning): {theoretical_full_tree:,.0f}")

def run_performance_goals_test():
    """Run performance test with timeouts and diagnostics"""
    
    print("=" * 80)
    print("ROBUST PERFORMANCE GOALS BENCHMARK TEST")
    print("=" * 80)
    print("Expected Performance Goals (Depth 4):")
    print("- Pure minimax: <2 seconds, <4,000,000 positions")
    print("- + Alpha Beta: <0.25 seconds, <500,000 positions")
    print("- + Move ordering: <0.025 seconds, <5,000 positions")
    print("\\nTimeout limits: 2x expected time")
    print("=" * 80)
    
    # Test position: Complex middle game position
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board = chess.Board(test_fen)
    depth = 4
    
    print(f"\\nTest Position: Complex Middle Game")
    print(f"FEN: {test_fen}")
    print(f"Search Depth: {depth}")
    print(f"Legal moves at root: {len(list(board.legal_moves))}")
    
    # Run diagnostic analysis first
    diagnostic_search_analysis(board, depth)
    
    print("\\n" + "="*60)
    print("PERFORMANCE TESTING")
    print("="*60)
    
    # Define goals and timeouts
    tests = [
        {
            'name': 'Pure Minimax',
            'function': minimax_with_move,
            'time_goal': 2.0,
            'nodes_goal': 4000000,
            'timeout': 4.0  # 2x expected
        },
        {
            'name': 'Alpha-Beta',
            'function': alpha_beta_with_move,
            'time_goal': 0.25,
            'nodes_goal': 500000,
            'timeout': 0.5  # 2x expected
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\\nTesting {test['name']}...")
        print(f"  Goal: <{test['time_goal']}s, <{test['nodes_goal']:,} nodes")
        print(f"  Timeout: {test['timeout']}s")
        
        start_time = time.time()
        move, score, nodes, timed_out, moves_tried = test['function'](
            board, depth, test['timeout']
        )
        search_time = time.time() - start_time
        
        # Check results
        time_status = "✓ PASS" if search_time < test['time_goal'] else "✗ FAIL"
        nodes_status = "✓ PASS" if nodes < test['nodes_goal'] else "✗ FAIL"
        timeout_status = "✗ TIMEOUT" if timed_out else "✓ COMPLETE"
        
        nps = int(nodes / max(search_time, 0.001))
        
        print(f"  Results:")
        print(f"    Status: {timeout_status}")
        print(f"    Time: {search_time:.3f}s {time_status}")
        print(f"    Nodes: {nodes:,} {nodes_status}")
        print(f"    NPS: {nps:,}")
        print(f"    Best Move: {move}")
        print(f"    Moves Tried: {moves_tried}")
        
        results.append({
            'name': test['name'],
            'time': search_time,
            'nodes': nodes,
            'time_status': time_status,
            'nodes_status': nodes_status,
            'timeout': timed_out,
            'nps': nps
        })
        
        # Critical analysis
        nodes_ratio = nodes / test['nodes_goal']
        if nodes_ratio < 0.1:  # Less than 10% of expected
            print(f"  ⚠️  CRITICAL: Only {nodes_ratio:.1%} of expected positions!")
            print(f"      This suggests a serious search bug.")
    
    # Summary
    print("\\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    print(f"{'Method':<15} {'Time':<10} {'Nodes':<12} {'NPS':<12} {'Status':<15}")
    print("-" * 80)
    
    all_passed = True
    for result in results:
        status_str = f"{result['time_status'][0]}{result['nodes_status'][0]}"
        if result['timeout']:
            status_str += " TIMEOUT"
            all_passed = False
        elif "✗" in result['time_status'] or "✗" in result['nodes_status']:
            all_passed = False
            
        print(f"{result['name']:<15} {result['time']:<10.3f} {result['nodes']:<12,} "
              f"{result['nps']:<12,} {status_str:<15}")
    
    print("\\n" + "="*40)
    if all_passed:
        print("✅ ALL TESTS PASSED - Engine meets performance goals!")
    else:
        print("❌ SOME TESTS FAILED - Performance optimization needed")
        
        # Check for critical position count issues
        for result in results:
            if result['name'] == 'Pure Minimax' and result['nodes'] < 400000:  # <10% expected
                print("\\n🚨 CRITICAL BUG DETECTED:")
                print("   Minimax position count is dramatically low!")
                print("   Expected: ~4,000,000 positions")
                print(f"   Actual: {result['nodes']:,} positions")
                print("   This indicates missing search branches - investigate immediately!")

if __name__ == "__main__":
    run_performance_goals_test()
