#!/usr/bin/env python3
"""
Random Opponent Chess Engine
A minimal UCI-compatible chess engine that plays random legal moves.
"""

import sys
import chess
import random

class UCIRandomEngine:
    def __init__(self):
        self.board = chess.Board()
        
    def get_random_move(self):
        """Get a random legal move for the side to move"""
        moves = list(self.board.legal_moves)
        return random.choice(moves) if moves else None
        
    def run(self):
        """Main UCI loop"""
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                    
                if line == "uci":
                    print("id name Random Opponent")
                    print("id author OpponentEngine")
                    print("uciok")
                    
                elif line == "isready":
                    print("readyok")
                    
                elif line == "ucinewgame":
                    self.board = chess.Board()
                    
                elif line.startswith("position"):
                    parts = line.split()
                    if parts[1] == "startpos":
                        self.board = chess.Board()
                        moves_idx = 3 if len(parts) > 3 and parts[2] == "moves" else None
                    else:  # position fen ...
                        fen_parts = []
                        i = 2
                        while i < len(parts) and parts[i] != "moves":
                            fen_parts.append(parts[i])
                            i += 1
                        self.board = chess.Board(" ".join(fen_parts))
                        moves_idx = i + 1 if i < len(parts) - 1 and parts[i] == "moves" else None
                    
                    if moves_idx:
                        for move in parts[moves_idx:]:
                            self.board.push(chess.Move.from_uci(move))
                            
                elif line.startswith("go"):
                    move = self.get_random_move()
                    print(f"bestmove {move.uci() if move else '0000'}")
                    
                elif line == "quit":
                    break
                    
            except EOFError:
                break
            except Exception as e:
                print(f"info string Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    engine = UCIRandomEngine()
    engine.run()
