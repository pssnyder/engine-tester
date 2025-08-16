#!/usr/bin/env python3
"""
Quick Performance Comparison Test

Test just depth 3 across all configurations to quickly see the efficiency gains.
"""

import chess
import time
import chess_ai

def quick_performance_test():
    """Run a quick test at depth 3 to see efficiency differences"""
    
    print("=" * 70)
    print("QUICK PERFORMANCE COMPARISON TEST (Depth 3)")
    print("=" * 70)
    
    # Test positions
    positions = [
        ("Starting Position", chess.STARTING_FEN),
        ("Tactical Puzzle", "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
        ("Complex Middle Game", "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w Q - 0 7")
    ]
    
    configs = [
        ("Base Search", "base"),
        ("Alpha-Beta", "alphabeta"), 
        ("AB + Move Ordering", "full")
    ]
    
    depth = 3
    results = []
    
    for pos_name, fen in positions:
        print(f"\\n--- {pos_name} ---")
        print(f"{'Config':<20} {'Nodes':<10} {'Time':<8} {'NPS':<10} {'Move':<8} {'Score':<8}")
        print("-" * 70)
        
        position_results = []
        
        for config_name, config_type in configs:
            board = chess.Board(fen)
            
            # Capture metrics
            final_nodes = 0
            final_score = 0
            
            def capture_info(**info):
                nonlocal final_nodes, final_score
                final_nodes = info.get('nodes', 0)
                final_score = info.get('score', 0)
            
            # Time the search
            start_time = time.time()
            best_move = chess_ai.search(
                board=board,
                depth=depth,
                info_callback=capture_info,
                config=config_type
            )
            search_time = time.time() - start_time
            
            nps = int(final_nodes / max(search_time, 0.001))
            
            print(f"{config_name:<20} {final_nodes:<10,} {search_time:<8.3f} {nps:<10,} {best_move:<8} {final_score:+8}")
            
            position_results.append({
                'config': config_name,
                'nodes': final_nodes,
                'time': search_time,
                'nps': nps
            })
        
        results.append((pos_name, position_results))
        
        # Calculate efficiency gains for this position
        base_nodes = position_results[0]['nodes']
        ab_nodes = position_results[1]['nodes']
        full_nodes = position_results[2]['nodes']
        
        if base_nodes > 0:
            ab_reduction = (base_nodes - ab_nodes) / base_nodes * 100
            full_reduction = (base_nodes - full_nodes) / base_nodes * 100
            ordering_improvement = (ab_nodes - full_nodes) / ab_nodes * 100 if ab_nodes > 0 else 0
            
            print(f"\\n  Efficiency gains:")
            print(f"    Alpha-Beta vs Base: {ab_reduction:+.1f}% node reduction")
            print(f"    Full vs Base: {full_reduction:+.1f}% node reduction")
            print(f"    Move Ordering additional: {ordering_improvement:+.1f}% node reduction")
    
    print("\\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Calculate overall averages
    total_base_nodes = 0
    total_ab_nodes = 0
    total_full_nodes = 0
    position_count = 0
    
    for pos_name, pos_results in results:
        if len(pos_results) >= 3:
            total_base_nodes += pos_results[0]['nodes']
            total_ab_nodes += pos_results[1]['nodes']
            total_full_nodes += pos_results[2]['nodes']
            position_count += 1
    
    if position_count > 0:
        avg_base = total_base_nodes / position_count
        avg_ab = total_ab_nodes / position_count
        avg_full = total_full_nodes / position_count
        
        overall_ab_gain = (avg_base - avg_ab) / avg_base * 100
        overall_full_gain = (avg_base - avg_full) / avg_base * 100
        
        print(f"\\nOverall Average Results (Depth {depth}):")
        print(f"  Base Search: {avg_base:,.0f} nodes")
        print(f"  Alpha-Beta:  {avg_ab:,.0f} nodes ({overall_ab_gain:+.1f}% improvement)")
        print(f"  Full Optimizations: {avg_full:,.0f} nodes ({overall_full_gain:+.1f}% improvement)")

if __name__ == "__main__":
    quick_performance_test()
