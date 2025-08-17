#!/usr/bin/env python3
"""Simple test script for chess_core functionality"""

import chess
import chess_core

def main():
    print("Testing ChessCore functionality...")
    
    # Create core instance
    core = chess_core.ChessCore()
    
    print("\n1. Testing engine move from starting position:")
    move = core.engine_move(depth=3)
    print(f"Engine suggested: {move}")
    
    print("\n2. Testing efficiency on a tactical position:")
    tactical_fen = "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    core.import_fen(tactical_fen)
    print(f"Loaded position: {tactical_fen}")
    
    print("\nRunning quick efficiency test:")
    test_positions = [
        ("Tactical", tactical_fen),
        ("Starting", chess.STARTING_FEN)
    ]
    core.run_efficiency_test(test_positions, depths=[2, 3])
    
    print("\n3. Testing move making:")
    core.new_game()
    print("Starting new game")
    print(core.board)
    
    # Make a few moves
    moves = ["e2e4", "e7e5", "g1f3"]
    for move_str in moves:
        move = chess.Move.from_uci(move_str)
        if core.push_move(move):
            print(f"Played: {move_str}")
        else:
            print(f"Failed to play: {move_str}")
    
    print("\nFinal position:")
    print(core.board)
    
    print("\n4. Testing PGN save:")
    if core.save_game_pgn("test_game.pgn"):
        print("PGN saved successfully")
    else:
        print("PGN save failed")
    
    print("\nChessCore test completed!")

if __name__ == "__main__":
    main()
