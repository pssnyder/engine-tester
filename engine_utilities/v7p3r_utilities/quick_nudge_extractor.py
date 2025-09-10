#!/usr/bin/env python3
"""
V7P3R Quick Nudge Extractor
Fast, simple tool to extract nudge positions from V7P3R games for the v11 nudge system.
Only does what's needed: finds V7P3R positions, quick Stockfish evaluation, builds nudge database.

Author: Pat Snyder
Created: September 7, 2025
"""

import chess
import chess.pgn
import chess.engine
import json
import os
import time
import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict
import logging
from datetime import datetime


@dataclass
class NudgePosition:
    """Simple nudge position data"""
    fen: str
    move: str
    eval_score: float
    frequency: int
    games: List[str]


class QuickNudgeExtractor:
    """
    Fast extractor for V7P3R nudge positions.
    
    Process:
    1. Scan PGN files for V7P3R games
    2. Extract V7P3R positions and moves
    3. Quick Stockfish evaluation (depth 10, fast)
    4. Build frequency database
    5. Output nudge-ready JSON
    
    Takes minutes, not hours.
    """
    
    def __init__(self, stockfish_path: str):
        self.stockfish_path = stockfish_path
        self.positions = defaultdict(lambda: defaultdict(list))  # fen -> move -> [evals]
        self.processed_games = set()
        self.load_processed_games()
        
        # Quick analysis settings
        self.analysis_depth = 10  # Fast but adequate
        self.min_eval_threshold = 0.0  # Include all moves initially
        self.max_eval_time = 1.0  # 1 second max per position
        
        print(f"🚀 Quick Nudge Extractor initialized")
        print(f"   Stockfish: {stockfish_path}")
        print(f"   Analysis depth: {self.analysis_depth}")
        print(f"   Max time per position: {self.max_eval_time}s")
    
    def load_processed_games(self):
        """Load list of already processed games to skip duplicates"""
        cache_file = "processed_games_cache.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.processed_games = set(json.load(f))
                print(f"📁 Loaded {len(self.processed_games)} previously processed games")
            except:
                self.processed_games = set()
    
    def save_processed_games(self):
        """Save processed games cache"""
        with open("processed_games_cache.json", 'w') as f:
            json.dump(list(self.processed_games), f)
    
    def create_position_key(self, board: chess.Board) -> str:
        """Create position key (simplified FEN without move counters)"""
        fen_parts = board.fen().split()
        return ' '.join(fen_parts[:4])  # Position only, no counters
    
    def quick_evaluate(self, board: chess.Board, engine) -> Optional[float]:
        """Quick Stockfish evaluation - fast and simple"""
        try:
            info = engine.analyse(
                board, 
                chess.engine.Limit(depth=self.analysis_depth, time=self.max_eval_time)
            )
            
            score = info.get('score')
            if score:
                if score.is_mate():
                    mate_value = score.white().mate()
                    return 1000 if mate_value and mate_value > 0 else -1000
                else:
                    cp_score = score.white().score()
                    if cp_score is not None:
                        eval_score = cp_score / 100.0
                        return eval_score if board.turn else -eval_score
            
            return 0.0
            
        except Exception as e:
            print(f"⚠️  Quick eval failed: {e}")
            return None
    
    def extract_from_game(self, game: chess.pgn.Game, engine) -> int:
        """Extract positions from a single V7P3R game"""
        # Check if V7P3R played
        white = str(game.headers.get('White', '')).upper()
        black = str(game.headers.get('Black', '')).upper()
        
        v7p3r_color = None
        if 'V7P3R' in white:
            v7p3r_color = chess.WHITE
        elif 'V7P3R' in black:
            v7p3r_color = chess.BLACK
        else:
            return 0  # V7P3R not playing
        
        game_id = f"{game.headers.get('Date', '')}-{white}-vs-{black}"
        
        # Skip if already processed
        if game_id in self.processed_games:
            return 0
        
        extracted = 0
        board = game.board()
        
        for move in game.mainline_moves():
            # Only analyze V7P3R's moves
            if board.turn == v7p3r_color:
                position_key = self.create_position_key(board)
                
                # Quick evaluation
                eval_score = self.quick_evaluate(board, engine)
                
                if eval_score is not None and eval_score >= self.min_eval_threshold:
                    self.positions[position_key][str(move)].append({
                        'eval': eval_score,
                        'game': game_id
                    })
                    extracted += 1
            
            board.push(move)
        
        self.processed_games.add(game_id)
        return extracted
    
    def scan_pgn_files(self, pgn_directory: str) -> Dict:
        """Scan PGN files and extract V7P3R positions"""
        print(f"📂 Scanning PGN files in: {pgn_directory}")
        
        total_games = 0
        v7p3r_games = 0
        total_positions = 0
        
        # Initialize Stockfish
        try:
            engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            print("✅ Stockfish connected")
        except Exception as e:
            print(f"❌ Failed to start Stockfish: {e}")
            return {}
        
        try:
            # Walk through PGN files
            for root, dirs, files in os.walk(pgn_directory):
                for file in files:
                    if file.endswith('.pgn'):
                        pgn_path = os.path.join(root, file)
                        print(f"🔍 Processing: {os.path.basename(pgn_path)}")
                        
                        try:
                            with open(pgn_path, 'r', encoding='utf-8') as pgn_file:
                                while True:
                                    game = chess.pgn.read_game(pgn_file)
                                    if game is None:
                                        break
                                    
                                    total_games += 1
                                    positions_extracted = self.extract_from_game(game, engine)
                                    
                                    if positions_extracted > 0:
                                        v7p3r_games += 1
                                        total_positions += positions_extracted
                                    
                                    # Progress update
                                    if total_games % 10 == 0:
                                        print(f"   📊 {total_games} games, {v7p3r_games} V7P3R, {total_positions} positions", end='\r')
                        
                        except Exception as e:
                            print(f"⚠️  Error reading {pgn_path}: {e}")
        
        finally:
            engine.quit()
            print(f"\n✅ Stockfish disconnected")
        
        # Save processed games cache
        self.save_processed_games()
        
        return {
            'total_games': total_games,
            'v7p3r_games': v7p3r_games,
            'total_positions': total_positions,
            'unique_positions': len(self.positions)
        }
    
    def build_nudge_database(self, min_frequency: int = 2, top_n_per_position: int = 3) -> Dict:
        """Build final nudge database from extracted positions"""
        print(f"🏗️  Building nudge database...")
        print(f"   Min frequency: {min_frequency}")
        print(f"   Top moves per position: {top_n_per_position}")
        
        nudge_db = {}
        
        for position_fen, moves_data in self.positions.items():
            # Process each move for this position
            move_scores = {}
            
            for move, evaluations in moves_data.items():
                if len(evaluations) >= min_frequency:
                    avg_eval = sum(e['eval'] for e in evaluations) / len(evaluations)
                    games = [e['game'] for e in evaluations]
                    
                    move_scores[move] = {
                        'avg_eval': avg_eval,
                        'frequency': len(evaluations),
                        'games': games,
                        'score': avg_eval * len(evaluations)  # Combined score
                    }
            
            # Keep top N moves for this position
            if move_scores:
                top_moves = sorted(
                    move_scores.items(), 
                    key=lambda x: x[1]['score'], 
                    reverse=True
                )[:top_n_per_position]
                
                position_hash = hashlib.md5(position_fen.encode()).hexdigest()[:12]
                
                nudge_db[position_hash] = {
                    'fen': position_fen,
                    'moves': {
                        move: {
                            'eval': data['avg_eval'],
                            'frequency': data['frequency'],
                            'games': data['games'][:5]  # Keep sample games
                        }
                        for move, data in top_moves
                    }
                }
        
        print(f"✅ Built nudge database with {len(nudge_db)} positions")
        return nudge_db
    
    def save_nudge_database(self, nudge_db: Dict, output_file: str):
        """Save nudge database to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(nudge_db, f, indent=2)
        
        print(f"💾 Nudge database saved: {output_file}")
        
        # Print summary
        total_moves = sum(len(pos['moves']) for pos in nudge_db.values())
        print(f"📊 Summary:")
        print(f"   Positions: {len(nudge_db)}")
        print(f"   Total moves: {total_moves}")
        print(f"   Avg moves per position: {total_moves/len(nudge_db):.1f}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick V7P3R Nudge Extractor')
    parser.add_argument('--pgn-dir', required=True, help='Directory with PGN files')
    parser.add_argument('--stockfish', required=True, help='Stockfish executable path')
    parser.add_argument('--output', default='v7p3r_nudge_database.json', help='Output file')
    parser.add_argument('--min-frequency', type=int, default=2, help='Min frequency for moves')
    parser.add_argument('--top-moves', type=int, default=3, help='Top moves per position')
    
    args = parser.parse_args()
    
    print("🚀 V7P3R Quick Nudge Extractor")
    print("="*40)
    
    start_time = time.time()
    
    # Create extractor
    extractor = QuickNudgeExtractor(args.stockfish)
    
    # Extract positions
    results = extractor.scan_pgn_files(args.pgn_dir)
    
    if results['total_positions'] > 0:
        # Build nudge database
        nudge_db = extractor.build_nudge_database(
            min_frequency=args.min_frequency,
            top_n_per_position=args.top_moves
        )
        
        # Save results
        extractor.save_nudge_database(nudge_db, args.output)
        
        elapsed = time.time() - start_time
        print(f"\n🎉 Complete in {elapsed:.1f} seconds!")
        print(f"📁 Nudge database: {args.output}")
        
    else:
        print("❌ No V7P3R positions found")


if __name__ == "__main__":
    main()
