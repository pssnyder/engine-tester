#!/usr/bin/env python3
"""
C0BR4 Illegal Move Quick Tester v2.7
====================================
Quick and focused tester that extracts the exact positions where C0BR4 made illegal moves
in the tournament and tests those specific scenarios.

This focuses on the positions immediately before the illegal move was made.
"""

import chess
import chess.pgn
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

def extract_illegal_move_positions(pgn_path: str) -> List[Dict]:
    """Extract positions where illegal moves occurred from tournament PGN."""
    illegal_positions = []
    
    try:
        with open(pgn_path, 'r') as pgn_file:
            game_index = 0
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                
                # Check if this game had a rules infraction
                termination = game.headers.get('Termination', '')
                if 'rules infraction' in termination.lower():
                    # Extract the illegal move position
                    board = game.board()
                    move_number = 1
                    
                    # Look for C0BR4 in white or black
                    white_player = game.headers.get('White', '')
                    black_player = game.headers.get('Black', '')
                    c0br4_is_white = 'C0BR4' in white_player
                    c0br4_is_black = 'C0BR4' in black_player
                    
                    if c0br4_is_white or c0br4_is_black:
                        # Go through moves until we find the illegal one (or get close)
                        moves = list(game.mainline())
                        
                        for move_idx, node in enumerate(moves):
                            move = node.move
                            player_to_move = white_player if board.turn else black_player
                            
                            # If this is C0BR4's turn, record the position
                            if ('C0BR4' in player_to_move):
                                position_data = {
                                    'game_index': game_index,
                                    'move_number': move_number + (0 if board.turn else 0.5),
                                    'fen': board.fen(),
                                    'player': player_to_move,
                                    'actual_move': move.uci(),
                                    'termination': termination,
                                    'white_player': white_player,
                                    'black_player': black_player,
                                    'result': game.headers.get('Result', '*'),
                                    'move_index': move_idx,
                                    'legal_moves': [m.uci() for m in board.legal_moves]
                                }
                                
                                # Check if this move is actually legal
                                try:
                                    if move in board.legal_moves:
                                        position_data['move_was_legal'] = True
                                    else:
                                        position_data['move_was_legal'] = False
                                        position_data['illegal_move_detected'] = True
                                        print(f"🚨 Found illegal move in PGN: {move.uci()} in position {board.fen()}")
                                except:
                                    position_data['move_was_legal'] = False
                                    position_data['parse_error'] = True
                                
                                illegal_positions.append(position_data)
                            
                            # Apply the move and continue
                            board.push(move)
                            if board.turn:  # After black's move
                                move_number += 1
                
                game_index += 1
                if game_index >= 10:  # Limit to first 10 games for quick testing
                    break
                    
    except Exception as e:
        print(f"❌ Error reading PGN: {e}")
    
    return illegal_positions

def test_engine_on_position(engine_path: str, fen: str, time_limit: float = 3.0) -> Dict:
    """Test C0BR4 on a specific position quickly."""
    result = {
        'fen': fen,
        'engine_move': None,
        'is_legal': False,
        'communication_error': None,
        'move_time': None
    }
    
    try:
        # Validate position first
        board = chess.Board(fen)
        legal_moves = [move.uci() for move in board.legal_moves]
        
        # Start engine
        start_time = time.time()
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if not process.stdin or not process.stdout:
            result['communication_error'] = 'Failed to start engine'
            return result
        
        # Send UCI commands
        process.stdin.write("uci\n")
        process.stdin.flush()
        
        # Wait for uciok
        while True:
            line = process.stdout.readline()
            if not line or "uciok" in line:
                break
        
        process.stdin.write("isready\n")
        process.stdin.flush()
        
        # Wait for readyok
        while True:
            line = process.stdout.readline()
            if not line or "readyok" in line:
                break
        
        # Set position and get move
        process.stdin.write(f"position fen {fen}\n")
        process.stdin.flush()
        
        process.stdin.write(f"go movetime {int(time_limit * 1000)}\n")
        process.stdin.flush()
        
        # Wait for bestmove
        while True:
            line = process.stdout.readline()
            if not line:
                break
            line = line.strip()
            
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    move = parts[1]
                    if move not in ["resign", "(none)", "null"]:
                        result['engine_move'] = move
                break
        
        end_time = time.time()
        result['move_time'] = end_time - start_time
        
        # Check if move is legal
        if result['engine_move']:
            try:
                move_obj = chess.Move.from_uci(result['engine_move'])
                result['is_legal'] = move_obj in board.legal_moves
            except:
                result['is_legal'] = False
        
        # Clean up
        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()
        process.wait(timeout=1)
        
    except Exception as e:
        result['communication_error'] = str(e)
    
    return result

def main():
    if len(sys.argv) < 3:
        print("Usage: python quick_illegal_move_tester.py <pgn_file> <engine_path>")
        sys.exit(1)
    
    pgn_path = sys.argv[1]
    engine_path = sys.argv[2]
    
    if not Path(pgn_path).exists():
        print(f"❌ PGN file not found: {pgn_path}")
        sys.exit(1)
    
    if not Path(engine_path).exists():
        print(f"❌ Engine not found: {engine_path}")
        sys.exit(1)
    
    print(f"🚀 C0BR4 Illegal Move Quick Tester v2.7")
    print(f"PGN: {pgn_path}")
    print(f"Engine: {engine_path}")
    print()
    
    # Extract positions where illegal moves occurred
    print("📖 Extracting illegal move positions from tournament...")
    illegal_positions = extract_illegal_move_positions(pgn_path)
    
    if not illegal_positions:
        print("✅ No illegal move positions found (or no C0BR4 games)")
        return
    
    print(f"Found {len(illegal_positions)} C0BR4 positions to test")
    print()
    
    # Test each position
    illegal_moves_reproduced = 0
    total_illegal_found = 0
    
    for i, pos_data in enumerate(illegal_positions):
        print(f"🔍 Testing position {i+1}/{len(illegal_positions)}")
        print(f"   Game {pos_data['game_index']+1}, Move {pos_data['move_number']}")
        print(f"   Player: {pos_data['player']}")
        print(f"   Original move: {pos_data['actual_move']}")
        print(f"   FEN: {pos_data['fen'][:60]}...")
        
        # Test with our engine
        result = test_engine_on_position(engine_path, pos_data['fen'])
        
        if result['communication_error']:
            print(f"   ❌ Communication error: {result['communication_error']}")
            continue
        
        if not result['engine_move']:
            print(f"   ❌ No move returned")
            continue
        
        # Report results
        if result['is_legal']:
            print(f"   ✅ Engine move: {result['engine_move']} (Legal)")
        else:
            print(f"   🚨 Engine move: {result['engine_move']} (ILLEGAL)")
            total_illegal_found += 1
            
            # Check if it reproduced the same illegal move
            if result['engine_move'] == pos_data['actual_move']:
                print(f"   🎯 REPRODUCED EXACT ILLEGAL MOVE!")
                illegal_moves_reproduced += 1
        
        # Check original move legality
        if pos_data.get('move_was_legal') == False:
            print(f"   📋 Original move {pos_data['actual_move']} was indeed illegal in PGN")
        
        print(f"   ⏱️  Time: {result['move_time']:.2f}s")
        print()
        
        time.sleep(0.5)  # Brief pause between tests
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"C0BR4 positions tested: {len(illegal_positions)}")
    print(f"Illegal moves found by engine: {total_illegal_found}")
    print(f"Exact tournament illegal moves reproduced: {illegal_moves_reproduced}")
    print(f"Illegal move reproduction rate: {illegal_moves_reproduced/len(illegal_positions)*100:.1f}%")
    
    if total_illegal_found > 0:
        print(f"\n🚨 C0BR4 v2.6 still generates illegal moves!")
        print(f"   This confirms the move generation bug is still present.")
        print(f"   We need to fix the move generation logic in C0BR4 source code.")
    else:
        print(f"\n✅ No illegal moves detected in isolated testing.")
        print(f"   The issue may be related to game state or communication timing.")

if __name__ == "__main__":
    main()
