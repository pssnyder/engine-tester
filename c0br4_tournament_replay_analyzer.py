#!/usr/bin/env python3
"""
C0BR4 Tournament Replay Analyzer v2.7
=====================================
Comprehensive position-by-position tournament replay system to isolate illegal move scenarios.
This tool recreates exact tournament conditions to catch C0BR4's illegal move generation.

Key Features:
- Loads tournament PGN files and extracts every position
- Replays each position individually with C0BR4 
- Tests each UCI command that Arena issued during the game
- Compares C0BR4's moves against known good engines (python-chess)
- Detects illegal moves, validation failures, and communication issues
- Creates detailed reports for debugging and fixing move generation

Usage:
    python c0br4_tournament_replay_analyzer.py --pgn tournament.pgn --engine engines/C0BR4/C0BR4_v2.6_FIXED.exe
"""

import argparse
import json
import chess
import chess.pgn
import chess.engine
import subprocess
import sys
import time
import io
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

class TournamentReplayAnalyzer:
    def __init__(self, engine_path: str, time_limit: float = 10.0):
        """
        Initialize the tournament replay analyzer.
        
        Args:
            engine_path: Path to C0BR4 engine executable
            time_limit: Time limit per move in seconds
        """
        self.engine_path = Path(engine_path)
        self.time_limit = time_limit
        self.results = {
            'metadata': {
                'engine_path': str(engine_path),
                'time_limit': time_limit,
                'analysis_start': datetime.now().isoformat(),
            },
            'games': [],
            'illegal_moves': [],
            'validation_failures': [],
            'communication_errors': [],
            'summary': {}
        }
        
    def load_tournament_pgn(self, pgn_path: str) -> List[chess.pgn.Game]:
        """Load all games from a tournament PGN file."""
        games = []
        try:
            with open(pgn_path, 'r') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    games.append(game)
            print(f"✅ Loaded {len(games)} games from {pgn_path}")
            return games
        except Exception as e:
            print(f"❌ Error loading PGN: {e}")
            return []
    
    def extract_positions_from_game(self, game: chess.pgn.Game) -> List[Dict[str, Any]]:
        """
        Extract all positions and moves from a game for replay testing.
        
        Returns list of position dictionaries with FEN, expected move, move number, etc.
        """
        positions = []
        board = game.board()
        move_number = 1
        
        # Add starting position
        positions.append({
            'fen': board.fen(),
            'move_number': move_number,
            'half_move': 'white' if board.turn else 'black',
            'expected_move': None,
            'game_result': game.headers.get('Result', '*'),
            'termination': game.headers.get('Termination', 'Unknown'),
            'white_player': game.headers.get('White', 'Unknown'),
            'black_player': game.headers.get('Black', 'Unknown'),
        })
        
        # Extract each position and the move played
        for node in game.mainline():
            move = node.move
            expected_uci = move.uci()
            
            # Store position before the move
            position_data = {
                'fen': board.fen(),
                'move_number': move_number + (0 if board.turn else 0.5),
                'half_move': 'white' if board.turn else 'black',
                'expected_move': expected_uci,
                'game_result': game.headers.get('Result', '*'),
                'termination': game.headers.get('Termination', 'Unknown'),
                'white_player': game.headers.get('White', 'Unknown'),
                'black_player': game.headers.get('Black', 'Unknown'),
                'legal_moves': [m.uci() for m in board.legal_moves],  # All legal moves in position
            }
            
            # Check if this was the player we're testing (C0BR4)
            player_name = game.headers.get('White', '') if board.turn else game.headers.get('Black', '')
            if 'C0BR4' in player_name or 'COBRA' in player_name:
                position_data['c0br4_to_move'] = True
            else:
                position_data['c0br4_to_move'] = False
                
            positions.append(position_data)
            
            # Apply the move to board
            board.push(move)
            if board.turn:  # After black's move, increment move number
                move_number += 1
                
        return positions
    
    def test_engine_on_position(self, fen: str, expected_move: Optional[str] = None) -> Dict[str, Any]:
        """
        Test C0BR4 on a specific position and return detailed results.
        
        Args:
            fen: FEN string of the position
            expected_move: The move that was actually played in the tournament
            
        Returns:
            Dictionary with engine response, legality check, timing, etc.
        """
        result = {
            'fen': fen,
            'expected_move': expected_move,
            'engine_move': None,
            'move_time': None,
            'is_legal': False,
            'is_expected': False,
            'legal_moves': [],
            'communication_error': None,
            'engine_output': [],
            'validation_with_python_chess': None
        }
        
        try:
            # Validate position with python-chess first
            board = chess.Board(fen)
            result['legal_moves'] = [move.uci() for move in board.legal_moves]
            result['validation_with_python_chess'] = 'valid'
            
            # Start engine process
            process = subprocess.Popen(
                [str(self.engine_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            if not process.stdin or not process.stdout:
                result['communication_error'] = 'Failed to establish engine communication'
                return result
            
            # Send UCI commands
            commands = [
                "uci\n",
                "isready\n",
                f"position fen {fen}\n",
                f"go movetime {int(self.time_limit * 1000)}\n"
            ]
            
            start_time = time.time()
            engine_output = []
            
            for cmd in commands:
                process.stdin.write(cmd)
                process.stdin.flush()
                engine_output.append(f">>> {cmd.strip()}")
                
                # Read response for each command
                if cmd.startswith("go"):
                    # For 'go' command, wait for bestmove
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        line = line.strip()
                        engine_output.append(f"<<< {line}")
                        
                        if line.startswith("bestmove"):
                            # Extract the move
                            parts = line.split()
                            if len(parts) >= 2:
                                move = parts[1]
                                if move != "resign" and move != "(none)":
                                    result['engine_move'] = move
                            break
                else:
                    # For other commands, read until ready or uciok
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        line = line.strip()
                        engine_output.append(f"<<< {line}")
                        
                        if line == "readyok" or line == "uciok":
                            break
            
            end_time = time.time()
            result['move_time'] = end_time - start_time
            result['engine_output'] = engine_output
            
            # Close engine
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.terminate()
            process.wait(timeout=2)
            
            # Validate the engine's move
            if result['engine_move']:
                # Check if legal using python-chess
                try:
                    move = chess.Move.from_uci(result['engine_move'])
                    result['is_legal'] = move in board.legal_moves
                except:
                    result['is_legal'] = False
                    
                # Check if matches expected
                if expected_move:
                    result['is_expected'] = (result['engine_move'] == expected_move)
            
        except ValueError:
            result['validation_with_python_chess'] = 'invalid_fen'
        except Exception as e:
            result['communication_error'] = str(e)
            
        return result
    
    def analyze_tournament_game(self, game: chess.pgn.Game, game_index: int) -> Dict[str, Any]:
        """
        Analyze a complete tournament game position by position.
        
        Args:
            game: The chess game to analyze
            game_index: Index of this game in the tournament
            
        Returns:
            Dictionary with complete game analysis results
        """
        print(f"\n{'='*80}")
        print(f"ANALYZING GAME {game_index + 1}")
        print(f"{'='*80}")
        print(f"White: {game.headers.get('White', 'Unknown')}")
        print(f"Black: {game.headers.get('Black', 'Unknown')}")
        print(f"Result: {game.headers.get('Result', '*')}")
        print(f"Termination: {game.headers.get('Termination', 'Unknown')}")
        
        # Extract all positions from the game
        positions = self.extract_positions_from_game(game)
        print(f"Extracted {len(positions)} positions for analysis")
        
        game_results = {
            'game_index': game_index,
            'headers': dict(game.headers),
            'total_positions': len(positions),
            'c0br4_positions': 0,
            'illegal_moves_found': 0,
            'communication_errors': 0,
            'position_results': []
        }
        
        # Test each position where C0BR4 was to move
        for pos_idx, position in enumerate(positions):
            if position.get('c0br4_to_move', False) and position.get('expected_move'):
                game_results['c0br4_positions'] += 1
                
                print(f"  Testing position {pos_idx + 1}/{len(positions)}: {position['fen'][:50]}...")
                print(f"    Expected move: {position['expected_move']}")
                
                # Test engine on this position
                test_result = self.test_engine_on_position(
                    position['fen'], 
                    position['expected_move']
                )
                
                # Add position context
                test_result['position_index'] = pos_idx
                test_result['move_number'] = position['move_number']
                test_result['half_move'] = position['half_move']
                
                # Report results
                if test_result['engine_move']:
                    legality = "✅ Legal" if test_result['is_legal'] else "🚨 ILLEGAL"
                    match = "✅ Match" if test_result['is_expected'] else "❌ Different"
                    print(f"    Engine move: {test_result['engine_move']} ({legality}, {match})")
                    
                    if not test_result['is_legal']:
                        game_results['illegal_moves_found'] += 1
                        self.results['illegal_moves'].append({
                            'game_index': game_index,
                            'position_index': pos_idx,
                            'fen': position['fen'],
                            'illegal_move': test_result['engine_move'],
                            'expected_move': position['expected_move'],
                            'legal_moves': test_result['legal_moves']
                        })
                        print(f"    🚨 ILLEGAL MOVE DETECTED: {test_result['engine_move']}")
                        print(f"    Legal moves were: {', '.join(test_result['legal_moves'][:10])}...")
                else:
                    print(f"    ❌ No move returned by engine")
                    
                if test_result['communication_error']:
                    game_results['communication_errors'] += 1
                    self.results['communication_errors'].append({
                        'game_index': game_index,
                        'position_index': pos_idx,
                        'error': test_result['communication_error']
                    })
                    
                game_results['position_results'].append(test_result)
                
                # Small delay between positions
                time.sleep(0.1)
        
        print(f"  Game analysis complete:")
        print(f"    C0BR4 positions tested: {game_results['c0br4_positions']}")
        print(f"    Illegal moves found: {game_results['illegal_moves_found']}")
        print(f"    Communication errors: {game_results['communication_errors']}")
        
        return game_results
    
    def run_tournament_analysis(self, pgn_path: str, max_games: Optional[int] = None) -> None:
        """
        Run complete tournament analysis on all games in PGN file.
        
        Args:
            pgn_path: Path to tournament PGN file
            max_games: Maximum number of games to analyze (None for all)
        """
        print(f"🚀 Starting C0BR4 Tournament Replay Analysis v2.7")
        print(f"Engine: {self.engine_path}")
        print(f"Time limit: {self.time_limit}s per position")
        print(f"Tournament PGN: {pgn_path}")
        
        # Load tournament games
        games = self.load_tournament_pgn(pgn_path)
        if not games:
            print("❌ No games found in PGN file")
            return
            
        if max_games:
            games = games[:max_games]
            print(f"🔄 Limiting analysis to first {max_games} games")
        
        # Analyze each game
        for game_index, game in enumerate(games):
            try:
                game_result = self.analyze_tournament_game(game, game_index)
                self.results['games'].append(game_result)
            except Exception as e:
                print(f"❌ Error analyzing game {game_index + 1}: {e}")
                continue
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
    def generate_summary(self) -> None:
        """Generate summary statistics for the tournament analysis."""
        total_games = len(self.results['games'])
        total_positions = sum(game['c0br4_positions'] for game in self.results['games'])
        total_illegal = len(self.results['illegal_moves'])
        total_comm_errors = len(self.results['communication_errors'])
        
        self.results['summary'] = {
            'total_games_analyzed': total_games,
            'total_c0br4_positions_tested': total_positions,
            'total_illegal_moves_found': total_illegal,
            'total_communication_errors': total_comm_errors,
            'illegal_move_rate': (total_illegal / total_positions * 100) if total_positions > 0 else 0,
            'games_with_illegal_moves': len([g for g in self.results['games'] if g['illegal_moves_found'] > 0]),
            'analysis_completed': datetime.now().isoformat()
        }
        
        print(f"\n{'='*80}")
        print("TOURNAMENT REPLAY ANALYSIS SUMMARY")
        print(f"{'='*80}")
        print(f"Games analyzed: {total_games}")
        print(f"C0BR4 positions tested: {total_positions}")
        print(f"Illegal moves found: {total_illegal}")
        print(f"Communication errors: {total_comm_errors}")
        print(f"Illegal move rate: {self.results['summary']['illegal_move_rate']:.2f}%")
        print(f"Games with illegal moves: {self.results['summary']['games_with_illegal_moves']}")
        
        if self.results['illegal_moves']:
            print(f"\n🚨 ILLEGAL MOVES DETECTED:")
            for i, illegal in enumerate(self.results['illegal_moves'][:5]):  # Show first 5
                print(f"  {i+1}. Game {illegal['game_index']+1}, Position {illegal['position_index']+1}")
                print(f"     FEN: {illegal['fen'][:60]}...")
                print(f"     Illegal Move: {illegal['illegal_move']} (Expected: {illegal['expected_move']})")
            if len(self.results['illegal_moves']) > 5:
                print(f"     ... and {len(self.results['illegal_moves']) - 5} more")
    
    def save_results(self) -> None:
        """Save analysis results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"c0br4_tournament_replay_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description="C0BR4 Tournament Replay Analyzer v2.7 - Systematic position testing"
    )
    parser.add_argument(
        "--pgn", 
        required=True, 
        help="Path to tournament PGN file"
    )
    parser.add_argument(
        "--engine", 
        default="engines/C0BR4/C0BR4_v2.6_FIXED.exe",
        help="Path to C0BR4 engine executable"
    )
    parser.add_argument(
        "--time-limit", 
        type=float, 
        default=5.0,
        help="Time limit per position in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--max-games", 
        type=int,
        help="Maximum number of games to analyze (default: all)"
    )
    
    args = parser.parse_args()
    
    # Verify engine exists
    engine_path = Path(args.engine)
    if not engine_path.exists():
        print(f"❌ Engine not found: {engine_path}")
        sys.exit(1)
    
    # Verify PGN exists
    pgn_path = Path(args.pgn)
    if not pgn_path.exists():
        print(f"❌ PGN file not found: {pgn_path}")
        sys.exit(1)
    
    # Run analysis
    analyzer = TournamentReplayAnalyzer(args.engine, args.time_limit)
    analyzer.run_tournament_analysis(str(pgn_path), args.max_games)

if __name__ == "__main__":
    main()
