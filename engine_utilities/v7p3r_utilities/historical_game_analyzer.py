#!/usr/bin/env python3
"""
V7P3R Historical Game Analyzer
Analyzes V7P3R's historical games against Stockfish to identify successful positions
and moves for the nudge system. This tool learns from past games to create a database
of favorable positions and preferred moves.

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
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import logging
from datetime import datetime


@dataclass
class PositionAnalysis:
    """Data structure for position analysis results"""
    position_fen: str
    position_hash: str
    v7p3r_move: str
    stockfish_top_moves: List[Tuple[str, float]]  # [(move, eval), ...]
    v7p3r_eval: float
    stockfish_eval: float
    eval_improvement: float
    move_rank_in_stockfish: int  # 1-based rank (1 = best move)
    game_id: str
    move_number: int
    frequency_count: int = 1


@dataclass
class NudgeEntry:
    """Data structure for nudge system entries"""
    position_fen: str
    position_hash: str
    preferred_move: str
    confidence_score: float
    frequency: int
    avg_eval_improvement: float
    stockfish_rank_avg: float
    source_games: List[str]


class V7P3RHistoricalGameAnalyzer:
    """
    Analyzes V7P3R's historical games to extract successful patterns for the nudge system.
    
    Process:
    1. Parse PGN files containing V7P3R games
    2. For each V7P3R move, analyze with Stockfish
    3. Identify moves that are in Stockfish's top 3 and show positive eval improvement
    4. Build database of successful positions and moves
    5. Generate nudge system data for V7P3R v11
    """
    
    def __init__(self, stockfish_path: str, analysis_depth: int = 15):
        self.stockfish_path = stockfish_path
        self.analysis_depth = analysis_depth
        self.position_database: Dict[str, PositionAnalysis] = {}
        self.nudge_entries: Dict[str, NudgeEntry] = {}
        
        # Analysis parameters
        self.min_eval_improvement = 0.1  # Minimum centipawn improvement
        self.max_stockfish_rank = 3      # Must be in top 3 stockfish moves
        self.min_frequency = 2           # Minimum occurrences to include in nudge system
        
        # Setup logging
        self.setup_logging()
        
        # Initialize Stockfish engine
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.init_stockfish()
    
    def setup_logging(self):
        """Setup logging for analysis tracking"""
        log_file = f"v7p3r_historical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_stockfish(self):
        """Initialize Stockfish engine for analysis"""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self.logger.info(f"Stockfish initialized: {self.stockfish_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Stockfish: {e}")
            raise
    
    def create_position_hash(self, board: chess.Board) -> str:
        """Create a unique hash for a chess position"""
        # Use FEN without move counters for position matching
        fen_parts = board.fen().split()
        position_fen = ' '.join(fen_parts[:4])  # Remove halfmove and fullmove counters
        return hashlib.md5(position_fen.encode()).hexdigest()
    
    def analyze_game(self, game: chess.pgn.Game) -> List[PositionAnalysis]:
        """
        Analyze a single game to extract V7P3R's moves and their Stockfish evaluation
        """
        analyses = []
        
        # Check if V7P3R played in this game
        white_player = str(game.headers.get('White', '')).upper()
        black_player = str(game.headers.get('Black', '')).upper()
        
        v7p3r_color = None
        if 'V7P3R' in white_player:
            v7p3r_color = chess.WHITE
        elif 'V7P3R' in black_player:
            v7p3r_color = chess.BLACK
        else:
            return analyses  # V7P3R not in this game
        
        # Create game identifier
        game_id = f"{game.headers.get('Date', 'unknown')}_{game.headers.get('Round', '0')}_{white_player}_vs_{black_player}"
        
        # Analyze the game moves
        board = game.board()
        move_number = 0
        
        for move in game.mainline_moves():
            move_number += 1
            
            # Only analyze V7P3R's moves
            if board.turn == v7p3r_color:
                try:
                    # Get position before move
                    position_before = board.copy()
                    
                    # Analyze position with Stockfish
                    stockfish_analysis = self.analyze_position_with_stockfish(position_before)
                    
                    if stockfish_analysis:
                        # Make V7P3R's move
                        board.push(move)
                        
                        # Get evaluation after move
                        eval_after = self.get_position_evaluation(board)
                        
                        # Calculate eval improvement
                        eval_improvement = eval_after - stockfish_analysis['eval_before']
                        
                        # Find V7P3R's move rank in Stockfish suggestions
                        move_rank = self.find_move_rank(move, stockfish_analysis['top_moves'])
                        
                        # Check if this move meets our criteria
                        if (move_rank <= self.max_stockfish_rank and 
                            eval_improvement >= self.min_eval_improvement):
                            
                            position_hash = self.create_position_hash(position_before)
                            
                            analysis = PositionAnalysis(
                                position_fen=position_before.fen(),
                                position_hash=position_hash,
                                v7p3r_move=str(move),
                                stockfish_top_moves=[(str(m), e) for m, e in stockfish_analysis['top_moves']],
                                v7p3r_eval=stockfish_analysis['eval_before'],
                                stockfish_eval=eval_after,
                                eval_improvement=eval_improvement,
                                move_rank_in_stockfish=move_rank,
                                game_id=game_id,
                                move_number=move_number
                            )
                            
                            analyses.append(analysis)
                            self.logger.info(f"Found good move: {move} in position {position_hash[:8]} (rank {move_rank}, +{eval_improvement:.2f})")
                    
                    else:
                        # Still make the move to continue analysis
                        board.push(move)
                        
                except Exception as e:
                    self.logger.warning(f"Error analyzing move {move} in game {game_id}: {e}")
                    board.push(move)  # Continue despite error
            else:
                board.push(move)
        
        return analyses
    
    def analyze_position_with_stockfish(self, board: chess.Board) -> Optional[Dict]:
        """Analyze position with Stockfish and return top moves with evaluations"""
        if not self.engine:
            return None
            
        try:
            # Get multi-PV analysis for top moves
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(depth=self.analysis_depth),
                multipv=5  # Get top 5 moves
            )
            
            if not info:
                return None
            
            # Extract evaluation and top moves
            top_moves = []
            eval_before = 0
            
            for i, pv_info in enumerate(info):
                if 'pv' in pv_info and len(pv_info['pv']) > 0:
                    move = pv_info['pv'][0]
                    score = pv_info.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
                    
                    if score.is_mate():
                        mate_value = score.white().mate()
                        eval_score = 1000 if mate_value and mate_value > 0 else -1000
                    else:
                        cp_score = score.white().score()
                        eval_score = cp_score / 100.0 if cp_score is not None else 0.0  # Convert centipawns to pawns
                    
                    # Adjust for board perspective
                    if not board.turn:  # Black to move
                        eval_score = -eval_score
                    
                    top_moves.append((move, eval_score))
                    
                    if i == 0:  # Best move evaluation
                        eval_before = eval_score
            
            return {
                'eval_before': eval_before,
                'top_moves': top_moves
            }
            
        except Exception as e:
            self.logger.warning(f"Stockfish analysis failed: {e}")
            return None
    
    def get_position_evaluation(self, board: chess.Board) -> float:
        """Get Stockfish evaluation for a position"""
        if not self.engine:
            return 0.0
            
        try:
            info = self.engine.analyse(board, chess.engine.Limit(depth=self.analysis_depth))
            score = info.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE))
            
            if score.is_mate():
                mate_value = score.white().mate()
                return 1000 if mate_value and mate_value > 0 else -1000
            else:
                cp_score = score.white().score()
                eval_score = cp_score / 100.0 if cp_score is not None else 0.0
                return eval_score if board.turn else -eval_score
                
        except Exception as e:
            self.logger.warning(f"Position evaluation failed: {e}")
            return 0.0
    
    def find_move_rank(self, move: chess.Move, top_moves: List[Tuple[chess.Move, float]]) -> int:
        """Find the rank of a move in Stockfish's top moves (1-based)"""
        for i, (stockfish_move, _) in enumerate(top_moves):
            if move == stockfish_move:
                return i + 1
        return 999  # Move not found in top moves
    
    def process_position_database(self):
        """Process analyzed positions to create nudge entries"""
        position_groups = defaultdict(list)
        
        # Group analyses by position hash
        for analysis in self.position_database.values():
            position_groups[analysis.position_hash].append(analysis)
        
        # Create nudge entries for positions that meet frequency requirements
        for position_hash, analyses in position_groups.items():
            if len(analyses) >= self.min_frequency:
                # Group by move within this position
                move_groups = defaultdict(list)
                for analysis in analyses:
                    move_groups[analysis.v7p3r_move].append(analysis)
                
                # Find the most frequent/successful move for this position
                best_move = None
                best_score = 0
                
                for move, move_analyses in move_groups.items():
                    frequency = len(move_analyses)
                    avg_improvement = sum(a.eval_improvement for a in move_analyses) / frequency
                    avg_rank = sum(a.move_rank_in_stockfish for a in move_analyses) / frequency
                    
                    # Calculate confidence score (higher is better)
                    confidence = (frequency * avg_improvement) / avg_rank
                    
                    if confidence > best_score:
                        best_score = confidence
                        best_move = move
                        best_move_analyses = move_analyses
                
                if best_move:
                    # Create nudge entry
                    source_games = list(set(a.game_id for a in best_move_analyses))
                    
                    nudge_entry = NudgeEntry(
                        position_fen=best_move_analyses[0].position_fen,
                        position_hash=position_hash,
                        preferred_move=best_move,
                        confidence_score=best_score,
                        frequency=len(best_move_analyses),
                        avg_eval_improvement=sum(a.eval_improvement for a in best_move_analyses) / len(best_move_analyses),
                        stockfish_rank_avg=sum(a.move_rank_in_stockfish for a in best_move_analyses) / len(best_move_analyses),
                        source_games=source_games
                    )
                    
                    self.nudge_entries[position_hash] = nudge_entry
                    
                    self.logger.info(f"Created nudge entry: {best_move} for position {position_hash[:8]} "
                                   f"(confidence: {best_score:.2f}, frequency: {len(best_move_analyses)})")
    
    def analyze_pgn_files(self, pgn_directory: str) -> Dict:
        """
        Analyze all PGN files in a directory tree for V7P3R games
        """
        self.logger.info(f"Starting analysis of PGN files in: {pgn_directory}")
        
        total_games = 0
        analyzed_games = 0
        total_analyses = 0
        
        # Walk through directory tree looking for PGN files
        for root, dirs, files in os.walk(pgn_directory):
            for file in files:
                if file.endswith('.pgn'):
                    pgn_path = os.path.join(root, file)
                    self.logger.info(f"Processing: {pgn_path}")
                    
                    try:
                        with open(pgn_path, 'r', encoding='utf-8') as pgn_file:
                            while True:
                                game = chess.pgn.read_game(pgn_file)
                                if game is None:
                                    break
                                
                                total_games += 1
                                
                                # Analyze this game
                                game_analyses = self.analyze_game(game)
                                
                                if game_analyses:
                                    analyzed_games += 1
                                    total_analyses += len(game_analyses)
                                    
                                    # Store analyses
                                    for analysis in game_analyses:
                                        key = f"{analysis.position_hash}_{analysis.v7p3r_move}_{analysis.game_id}"
                                        self.position_database[key] = analysis
                                
                                # Progress logging
                                if total_games % 50 == 0:
                                    self.logger.info(f"Processed {total_games} games, {analyzed_games} with V7P3R, {total_analyses} positions")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {pgn_path}: {e}")
        
        self.logger.info(f"Analysis complete: {total_games} total games, {analyzed_games} V7P3R games, {total_analyses} positions analyzed")
        
        # Process the database to create nudge entries
        self.process_position_database()
        
        return {
            'total_games': total_games,
            'analyzed_games': analyzed_games,
            'total_positions': total_analyses,
            'nudge_entries': len(self.nudge_entries)
        }
    
    def save_results(self, output_directory: str):
        """Save analysis results to files"""
        os.makedirs(output_directory, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save position database
        position_db_file = os.path.join(output_directory, f'v7p3r_position_database_{timestamp}.json')
        with open(position_db_file, 'w') as f:
            position_data = {key: asdict(analysis) for key, analysis in self.position_database.items()}
            json.dump(position_data, f, indent=2)
        
        # Save nudge entries
        nudge_file = os.path.join(output_directory, f'v7p3r_nudge_entries_{timestamp}.json')
        with open(nudge_file, 'w') as f:
            nudge_data = {key: asdict(entry) for key, entry in self.nudge_entries.items()}
            json.dump(nudge_data, f, indent=2)
        
        # Save summary statistics
        summary_file = os.path.join(output_directory, f'v7p3r_analysis_summary_{timestamp}.json')
        with open(summary_file, 'w') as f:
            summary = {
                'analysis_date': datetime.now().isoformat(),
                'total_positions_analyzed': len(self.position_database),
                'nudge_entries_created': len(self.nudge_entries),
                'analysis_parameters': {
                    'min_eval_improvement': self.min_eval_improvement,
                    'max_stockfish_rank': self.max_stockfish_rank,
                    'min_frequency': self.min_frequency,
                    'analysis_depth': self.analysis_depth
                },
                'top_nudge_entries': self.get_top_nudge_entries(10)
            }
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Results saved to {output_directory}")
        self.logger.info(f"Position database: {position_db_file}")
        self.logger.info(f"Nudge entries: {nudge_file}")
        self.logger.info(f"Summary: {summary_file}")
    
    def get_top_nudge_entries(self, count: int) -> List[Dict]:
        """Get top nudge entries by confidence score"""
        sorted_entries = sorted(
            self.nudge_entries.values(),
            key=lambda x: x.confidence_score,
            reverse=True
        )
        
        return [asdict(entry) for entry in sorted_entries[:count]]
    
    def cleanup(self):
        """Cleanup resources"""
        if self.engine:
            self.engine.quit()
            self.logger.info("Stockfish engine closed")


def main():
    """Main function for running the historical game analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='V7P3R Historical Game Analyzer')
    parser.add_argument('--pgn-dir', required=True, help='Directory containing PGN files')
    parser.add_argument('--stockfish-path', required=True, help='Path to Stockfish executable')
    parser.add_argument('--output-dir', default='analysis_output', help='Output directory for results')
    parser.add_argument('--depth', type=int, default=15, help='Stockfish analysis depth')
    parser.add_argument('--min-eval-improvement', type=float, default=0.1, help='Minimum eval improvement')
    parser.add_argument('--max-rank', type=int, default=3, help='Maximum Stockfish rank')
    parser.add_argument('--min-frequency', type=int, default=2, help='Minimum frequency for nudge entries')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = V7P3RHistoricalGameAnalyzer(
        stockfish_path=args.stockfish_path,
        analysis_depth=args.depth
    )
    
    # Set analysis parameters
    analyzer.min_eval_improvement = args.min_eval_improvement
    analyzer.max_stockfish_rank = args.max_rank
    analyzer.min_frequency = args.min_frequency
    
    try:
        # Run analysis
        results = analyzer.analyze_pgn_files(args.pgn_dir)
        
        # Save results
        analyzer.save_results(args.output_dir)
        
        # Print summary
        print("\n" + "="*50)
        print("V7P3R HISTORICAL GAME ANALYSIS COMPLETE")
        print("="*50)
        print(f"Total games processed: {results['total_games']}")
        print(f"V7P3R games analyzed: {results['analyzed_games']}")
        print(f"Positions analyzed: {results['total_positions']}")
        print(f"Nudge entries created: {results['nudge_entries']}")
        print(f"Results saved to: {args.output_dir}")
        
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    main()
