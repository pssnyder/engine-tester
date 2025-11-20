#!/usr/bin/env python3
"""
V16.0 Test Suite
Tests for material safety, move filtering, and castling preservation
"""

import sys
sys.path.insert(0, 'src')

import chess
from v7p3r import V7P3REngine

def test_qxh7_prevention():
    """Test that Qxh7 sacrifice is filtered"""
    print("\n" + "="*60)
    print("TEST 1: Qxh7 Sacrifice Prevention")
    print("="*60)
    
    engine = V7P3REngine()
    
    # Position where Qxh7?? hangs queen
    board = chess.Board("r1bqkbnr/pppp1ppp/2n2n2/4p3/1nP5/5N2/PPQ1PPPP/RNB1KB1R w KQkq - 0 1")
    engine.board = board
    
    print("Position: After 3...Nb4")
    print(board)
    print()
    
    # Check Qxh7 material delta
    qxh7 = chess.Move.from_uci('c2h7')
    material_delta = engine._calculate_material_delta(board, qxh7)
    
    print(f"Qxh7 material delta: {material_delta:+d} cp")
    print()
    
    # Get filtered moves
    legal_moves = list(board.legal_moves)
    filtered_moves = engine._filter_and_order_moves(board, legal_moves, 0, None)
    
    qxh7_filtered = qxh7 in filtered_moves
    
    print(f"Total legal moves: {len(legal_moves)}")
    print(f"Filtered moves: {len(filtered_moves)}")
    print(f"Qxh7 in filtered: {qxh7_filtered}")
    print()
    
    if not qxh7_filtered:
        print("[PASS] Qxh7 correctly FILTERED OUT")
    else:
        print("[FAIL] Qxh7 still in move list")
    
    # Get engine's choice
    best_move = engine.get_best_move(time_left=5, increment=0)
    print(f"\nEngine chose: {best_move.uci() if best_move else 'None'}")
    
    if best_move and best_move.uci() != 'c2h7':
        print("[PASS] Did NOT play Qxh7")
    else:
        print("[FAIL] Played Qxh7")
    
    return not qxh7_filtered and (not best_move or best_move.uci() != 'c2h7')


def test_castling_priority():
    """Test that king moves have low priority (preserve castling)"""
    print("\n" + "="*60)
    print("TEST 2: Castling Rights Preservation")
    print("="*60)
    
    engine = V7P3REngine()
    
    # Position where king can move but shouldn't (not castling)
    board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPPKPPP/RNBQ1BNR w kq - 0 1")
    engine.board = board
    
    print("Position: King moved early (Ke2), lost castling")
    print(board)
    print()
    
    # Check move ordering
    legal_moves = list(board.legal_moves)
    ordered_moves = engine._filter_and_order_moves(board, legal_moves, 0, None)
    
    # Find king moves in ordered list
    king_moves = [m for m in ordered_moves if board.piece_at(m.from_square) and 
                  board.piece_at(m.from_square).piece_type == chess.KING]
    
    if king_moves:
        first_king_idx = ordered_moves.index(king_moves[0])
        total_moves = len(ordered_moves)
        
        print(f"First king move position: {first_king_idx + 1}/{total_moves}")
        print(f"Percentage: {(first_king_idx / total_moves) * 100:.1f}%")
        print()
        
        # King moves should be in last 20% of moves (low priority)
        if first_king_idx > total_moves * 0.8:
            print("[PASS] King moves have LOW priority (last 20%)")
            return True
        else:
            print("[FAIL] King moves too high priority")
            return False
    
    return True


def test_castling_high_priority():
    """Test that CASTLING moves have HIGH priority"""
    print("\n" + "="*60)
    print("TEST 3: Castling Move Prioritization")
    print("="*60)
    
    engine = V7P3REngine()
    
    # Position where castling is available
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
    engine.board = board
    
    print("Position: Can castle kingside")
    print(board)
    print()
    
    # Check move ordering
    legal_moves = list(board.legal_moves)
    ordered_moves = engine._filter_and_order_moves(board, legal_moves, 0, None)
    
    # Find castling move
    castling_move = chess.Move.from_uci('e1g1')
    
    if castling_move in ordered_moves:
        castling_idx = ordered_moves.index(castling_move)
        total_moves = len(ordered_moves)
        
        print(f"Castling O-O position: {castling_idx + 1}/{total_moves}")
        print(f"Percentage: {(castling_idx / total_moves) * 100:.1f}%")
        print()
        
        # Castling should be in top 30% (high priority)
        if castling_idx < total_moves * 0.3:
            print("[PASS] Castling has HIGH priority (top 30%)")
            return True
        else:
            print("[FAIL] Castling not prioritized enough")
            return False
    
    print("[INFO] Castling not available in this position")
    return True


def test_winning_capture():
    """Test that winning captures are prioritized"""
    print("\n" + "="*60)
    print("TEST 4: Winning Captures Prioritized")
    print("="*60)
    
    engine = V7P3REngine()
    
    # Position after 1.e4 e5 2.Nf3 Nf6 - Nxe5 wins pawn
    board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
    engine.board = board
    
    print("Position: After 2...Nf6, can play Nxe5 winning pawn")
    print(board)
    print()
    
    nxe5 = chess.Move.from_uci('f3e5')
    if nxe5 not in board.legal_moves:
        print("[ERROR] Test position incorrect - Nxe5 not legal")
        return False
    
    material_delta = engine._calculate_material_delta(board, nxe5)
    
    print(f"Nxe5 material delta: {material_delta:+d} cp")
    
    if material_delta > 50:
        print("[PASS] Winning capture recognized (+100)")
    else:
        print(f"[FAIL] Expected > +50, got {material_delta}")
    
    # Check prioritization
    legal_moves = list(board.legal_moves)
    ordered_moves = engine._filter_and_order_moves(board, legal_moves, 0, None)
    
    print(f"\nTotal moves after filtering: {len(ordered_moves)}/{len(legal_moves)}")
    
    if nxe5 in ordered_moves:
        nxe5_idx = ordered_moves.index(nxe5)
        print(f"Nxe5 position in move list: {nxe5_idx + 1}/{len(ordered_moves)}")
        
        if nxe5_idx < 5:
            print("[PASS] Winning capture in top 5 moves")
            return True
        else:
            print(f"[FAIL] Winning capture at position {nxe5_idx + 1}, expected top 5")
            return False
    else:
        print("[FAIL] Nxe5 not in filtered moves")
        return False


if __name__ == "__main__":
    print("="*60)
    print("V7P3R v16.0 TEST SUITE")
    print("Fresh Start - Material Safety + Positional Play")
    print("="*60)
    
    results = []
    
    try:
        results.append(("Qxh7 Prevention", test_qxh7_prevention()))
        results.append(("Castling Preservation", test_castling_priority()))
        results.append(("Castling Priority", test_castling_high_priority()))
        results.append(("Winning Captures", test_winning_capture()))
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        for test_name, passed in results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} {test_name}")
        
        total = len(results)
        passed = sum(1 for _, p in results if p)
        
        print(f"\nPassed: {passed}/{total}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! V16.0 is ready for tournament testing!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed - needs fixes")
        
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
